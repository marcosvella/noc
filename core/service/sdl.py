# ----------------------------------------------------------------------
# SDL Request handler
# ----------------------------------------------------------------------
# Copyright (C) 2007-2017 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import tornado.web
import orjson


class SDLRequestHandler(tornado.web.RequestHandler):
    def initialize(self, sdl):
        self.sdl = sdl

    def get(self):
        self.set_header("Content-Type", "text/javascript")
        self.write("var SDL = %s;" % orjson.dumps(self.sdl))
