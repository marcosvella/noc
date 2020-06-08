#!./bin/python
# ---------------------------------------------------------------------
# Login service
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import operator

# Third-party modules
import cachetools

# NOC modules
from noc.core.service.ui import UIService
from noc.services.login.auth import AuthRequestHandler
from noc.services.login.logout import LogoutRequestHandler
from noc.services.login.logged import IsLoggedRequestHandler
from noc.services.login.api.login import LoginAPI
from noc.services.login.backends.base import BaseAuthBackend
from noc.aaa.models.user import User
from noc.aaa.models.apikey import APIKey
from noc.core.perf import metrics
from noc.config import config
from noc.core.comp import smart_text


class LoginService(UIService):
    name = "login"
    process_name = "noc-%(name).10s-%(instance).2s"
    api = [LoginAPI]
    use_mongo = True
    use_translation = True
    if config.features.traefik:
        traefik_backend = "login"
        traefik_frontend_rule = "PathPrefix:/api/login,/api/auth/auth"

    _apikey_cache = cachetools.TTLCache(100, ttl=3)

    def get_handlers(self):
        return super().get_handlers() + [
            ("^/api/auth/auth/$", AuthRequestHandler, {"service": self}),
            ("^/api/login/logout/$", LogoutRequestHandler),
            ("^/api/login/is_logged/$", IsLoggedRequestHandler),
        ]

    # Fields excluded from logging
    HIDDEN_FIELDS = ["password", "new_password", "old_password", "retype_password"]

    def iter_methods(self):
        for m in config.login.methods.split(","):
            yield m.strip()

    def authenticate(self, handler, credentials):
        """
        Authenticate user. Returns True when user is authenticated
        """
        c = credentials.copy()
        for f in self.HIDDEN_FIELDS:
            if f in c:
                c[f] = "***"
        le = "No active auth methods"
        for method in self.iter_methods():
            bc = BaseAuthBackend.get_backend(method)
            if not bc:
                self.logger.error("Cannot initialize backend '%s'", method)
                continue
            backend = bc(self)
            self.logger.info("Authenticating credentials %s using method %s", c, method)
            try:
                user = backend.authenticate(**credentials)
                metrics["auth_try", ("method", method)] += 1
            except backend.LoginError as e:
                self.logger.info("[%s] Login Error: %s", method, smart_text(e))
                metrics["auth_fail", ("method", method)] += 1
                le = smart_text(e)
                continue
            self.logger.info("Authorized credentials %s as user %s", c, user)
            metrics["auth_success", ("method", method)] += 1
            # Set cookie
            handler.set_secure_cookie(
                "noc_user", user, expires_days=config.login.session_ttl, httponly=True,
            )
            # Register last login
            if config.login.register_last_login:
                u = User.get_by_username(user)
                if u:
                    u.register_login()
            return True
        self.logger.error("Login failed for %s: %s", c, le)
        return False

    def change_credentials(self, handler, credentials):
        """
        Change credentials. Return true when credentials changed
        """
        c = credentials.copy()
        for f in self.HIDDEN_FIELDS:
            if f in c:
                c[f] = "***"
        r = False
        for method in self.iter_methods():
            bc = BaseAuthBackend.get_backend(method)
            if not bc:
                self.logger.error("Cannot initialize backend '%s'", method)
                continue
            backend = bc(self)
            self.logger.info("Changing credentials %s using method %s", c, method)
            try:
                backend.change_credentials(**credentials)
                r = True
            except NotImplementedError:
                continue
            except backend.LoginError as e:
                self.logger.error("Failed to change credentials for %s: %s", c, e)
            self.logger.info("Changed user credentials: %s", c)
        return r

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_apikey_cache"))
    def get_api_access(cls, key, ip):
        return APIKey.get_name_and_access_str(key, ip)


if __name__ == "__main__":
    LoginService().start()
