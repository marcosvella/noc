# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# CustomerPortal client
# ---------------------------------------------------------------------
# Copyright (C) 2007-2015 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import logging
# Third-party modules
import requests
import ujson
# Python modules
import os
import ConfigParser
from noc.core.version import version

logger = logging.getLogger(__name__)


class CPClient(object):
    CONFIG = "etc/support.conf"
    CP_URL = "https://cp.nocproject.org"
    PRODUCT = "NOC"

    Error = Exception

    ACCOUNT_SERVICE = "/api/v1.0/AccountService/"
    SYSTEM_SERVICE = "/api/v1.0/SystemService/"
    UPGRADE_SERVICE = "/api/v1.0/UpgradeService/"
    CRASHINFO_SERVICE = "/api/v1.0/CrashinfoService/"
    PASTE_SERVICE = "/api/v1.0/PasteService/"

    def __init__(self):
        self.cp_url = self.CP_URL
        self.account_uuid = None
        self.account_name = None
        self.account_password = None
        self.system_uuid = None
        self.system_name = None
        self.system_type = None
        self.load_config()
        self.t_id = 0

    def load_config(self):
        if os.path.exists(self.CONFIG):
            logger.debug("Loading config %s", self.CONFIG)
            config = ConfigParser.RawConfigParser()
            config.read(self.CONFIG)
            # Read account settings
            if config.has_section("account"):
                if config.has_option("account", "cp_url"):
                    self.cp_url = config.get("account", "cp_url")
                else:
                    self.cp_url = self.CP_URL
                if config.has_option("account", "uuid"):
                    self.account_uuid = config.get("account", "uuid")
                if config.has_option("account", "name"):
                    self.account_name = config.get("account", "name")
                if config.has_option("account", "password"):
                    self.account_password = config.get("account", "password")
            # Read system settings
            if config.has_section("system"):
                if config.has_option("system", "uuid"):
                    self.system_uuid = config.get("system", "uuid")
                if config.has_option("system", "name"):
                    self.system_name = config.get("system", "name")
                if config.has_option("system", "type"):
                    self.system_type = config.get("system", "type")
        else:
            logger.debug("Unregistered installation")
            self.cp_url = self.CP_URL

    def has_account(self):
        return self.account_name is not None

    def has_system(self):
        return self.has_account() and self.system_name is not None

    def write_config(self):
        cfg = [
            "#",
            "# Autogenerated file",
            "# Received through system registration",
            "# Support > Account",
            "# Do not change manually",
            "#"
        ]
        if self.cp_url or self.account_uuid:
            cfg += ["[account]"]
            if self.cp_url and self.cp_url != self.CP_URL:
                cfg += ["cp_url = %s" % self.cp_url]
            if self.account_uuid:
                cfg += [
                    "uuid = %s" % self.account_uuid,
                    "name = %s" % self.account_name,
                    "password = %s" % self.account_password
                ]
        if self.system_uuid:
            cfg += [
                "[system]",
                "uuid = %s" % self.system_uuid,
                "name = %s" % self.system_name,
                "type = %s" % self.system_type
            ]
        cfg += [""]
        logger.info("Saving %s", self.CONFIG)
        with open(self.CONFIG, "w") as f:
            f.write("\n".join(cfg))

    def call(self, service, method, *args):
        """
        JSON-RPC client
        """
        self.t_id += 1
        r = {
            "id": self.t_id,
            "method": method,
            "params": args
        }
        auth = None
        if self.account_name and self.account_password:
            auth = (self.account_name, self.account_password)
        r = ujson.dumps(r)
        logger.debug("JSON-RPC REQUEST: %s", r)
        try:
            req = requests.post(
                self.cp_url + service,
                data=r,
                auth=auth,
                verify=True
            )
        except Exception, why:
            logger.error("JSON-RPC Error: %s", why)
            raise self.Error(str(why))
        try:
            response = req.json()
            logger.debug("JSON-RPC RESPONSE: %s", response)
        except ValueError, why:
            logger.error("Invalid JSON-RPC response: %s", why)
            raise self.Error("Invalid response")
        if response.get("error"):
            logger.error("JSON-RPC error: %s", response["error"])
            raise self.Error(response["error"])
        return response.get("result")

    def create_account(self, name, email, password,
                       country=None, org=None, industries=None,
                       language=None):
        if self.has_account():
            raise self.Error("Account is already exists")
        info = {}
        if country:
            info["country"] = country
        if org:
            info["org"] = org.strip()
        if industries:
            if isinstance(industries, basestring):
                industries = [x.strip() for x in industries.split(",")
                              if x.strip()]
            info["industries"] = industries
        if language:
            info["language"] = language
        self.account_uuid = self.call(
            self.ACCOUNT_SERVICE, "create",
            name, email, password, info)["uuid"]
        self.account_name = name
        self.account_password = password
        self.write_config()

    def update_account(self, name, email,
                       country=None, org=None, industries=None,
                       language=None):
        if not self.has_account():
            raise self.Error("Account is not registred")
        info = {}
        if country:
            info["country"] = country
        if org:
            info["org"] = org.strip()
        if industries:
            if isinstance(industries, basestring):
                industries = [x.strip() for x in industries.split(",")
                              if x.strip()]
            info["industries"] = industries
        if language:
            info["language"] = language
        self.call(self.ACCOUNT_SERVICE, "update", name, email, info)
        if name != self.account_name:
            self.account_name = name
            self.write_config()

    def account_info(self):
        if not self.has_account():
            raise self.Error("Account is not registered")
        return self.call(self.ACCOUNT_SERVICE, "info")

    def attach_account(self, name, password):
        if self.has_account():
            raise self.Error("Account is already registred")
        logger.info("Attaching account %s", name)
        self.account_name = name
        self.account_password = password
        try:
            self.account_uuid = self.account_info()["uuid"]
        except CPClient.Error as e:
            logging.error("Error attaching account: %s", e)
            raise self.Error(e)
        self.write_config()
        logger.info("Account %s has been attached", name)

    def change_password(self, new_password):
        if not self.has_account():
            raise self.Error("Account is not registred")
        logger.info("Changing password for %s", self.account_name)
        self.call(self.ACCOUNT_SERVICE, "change_password", new_password)
        self.account_password = new_password
        self.write_config()

    def create_system(self, name, type, description=None):
        if not self.has_account():
            raise self.Error("Account is not registred")
        logger.info("Creating system %s for %s", name, self.account_name)
        info = {}
        if description:
            info["description"] = description
        self.system_uuid = self.call(self.SYSTEM_SERVICE,
                                     "create", self.PRODUCT,
                                     name, type, info)["uuid"]
        self.system_name = name
        self.system_type = type
        self.write_config()

    def update_system(self, name, type, description=None, is_active=True):
        if not self.has_account():
            raise self.Error("Account is not registred")
        if not self.has_system():
            raise self.Error("System is not registred")
        logger.info("Changing system %s for %s", name, self.account_name)
        info = {}
        if description:
            info["description"] = description
        self.call(self.SYSTEM_SERVICE,
                  "update", self.system_uuid,
                  name, is_active, type, info)

    def system_info(self):
        if not self.has_system():
            raise self.Error("System is not registered")
        return self.call(self.SYSTEM_SERVICE, "info", self.system_uuid)

    def upgrade(self, status, log=""):
        if not self.has_system():
            raise self.Error("System is not registred")
        return self.call(self.UPGRADE_SERVICE, "upgrade",
                         self.system_uuid,
                         version.os_brand, version.os_version,
                         version.branch, version.changeset,
                         version.package_versions, [], status, log)

    def report_crashinfo(self, crashinfo):
        if not self.has_system():
            raise self.Error("System is not registred")
        return self.call(
            self.CRASHINFO_SERVICE, "report",
            self.system_uuid, crashinfo)

    def create_paste(self, subject=None, data=None, syntax=None, ttl=None, public=False):
        if not self.has_system():
            raise self.Error("System is not registred")
        return self.call(self.PASTE_SERVICE, "create",
                         subject, data, syntax, ttl, public)
