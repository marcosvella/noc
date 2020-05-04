# ----------------------------------------------------------------------
# BaseAPITest
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import functools
import types

# Third-party modules
import tornado.gen
import tornado.ioloop
import tornado.testing
import tornado.httpserver
import tornado.web
import pytest
import ujson

# NOC modules
from noc.core.http.client import fetch


class APIHandler(object):
    io_loop = None

    def __init__(self, handlers):
        if not getattr(APIHandler, "io_loop"):
            APIHandler.io_loop = tornado.ioloop.IOLoop()
            APIHandler.io_loop.make_current()
        sock, port = tornado.testing.bind_unused_port()
        app = tornado.web.Application(handlers)
        self.server = tornado.httpserver.HTTPServer(app)
        self.server.add_socket(sock)
        self.base_url = "http://127.0.0.1:%d" % port
        self.server.start()

    @tornado.gen.coroutine
    def fetch(self, url, method="GET", headers=None, body=None):
        url = "%s%s" % (self.base_url, url)
        code, headers, body = yield fetch(url=url, method=method, headers=headers, body=body)
        return code, headers, body


def gen_test(f):
    def wrap(f):
        @functools.wraps(f)
        def pre_coroutine(self, *args, **kwargs):
            result = f(self, *args, **kwargs)
            if isinstance(result, types.GeneratorType):
                self._test_generator = result
            else:
                self._test_generator = None
            return result

        coro = tornado.gen.coroutine(pre_coroutine)

        @functools.wraps(coro)
        def post_coroutine(self, *args, **kwargs):
            try:
                return self.io_loop.run_sync(
                    functools.partial(coro, self, *args, **kwargs), timeout=15
                )
            except tornado.gen.TimeoutError as e:
                self._test_generator.throw(e)
                raise

        return post_coroutine

    return wrap(f)


class BaseAPITest(object):
    name = None
    _api = {}

    @pytest.fixture(autouse=True)
    def init_api(self):
        if self.name not in self._api:
            self._api[self.name] = APIHandler(self.get_handlers())
            self.api = self._api[self.name]
        self.api = self._api[self.name]
        self.io_loop = self.api.io_loop

    @tornado.gen.coroutine
    def fetch(self, url, method="GET", headers=None, body=None, user="superuser"):
        headers = headers or {}
        headers["Remote-User"] = user
        code, headers, body = yield self.api.fetch(url, method=method, headers=headers, body=body)
        if "Content-Type" in headers and headers["Content-Type"].startswith("text/json"):
            body = ujson.loads(body)
        return code, headers, body

    def get_handlers(self):
        raise NotImplementedError()


class WebAPITest(BaseAPITest):
    name = "web"

    def get_handlers(self):
        from noc.services.web.service import WebService

        ws = WebService()
        ws.setup_test_logging()
        ws.on_activate()
        return ws.get_handlers()
