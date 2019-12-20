# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# MikroTik.SwOS profile
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re
import ujson

# NOC modules
from noc.core.profile.base import BaseProfile


class Profile(BaseProfile):
    name = "MikroTik.SwOS"
    http_request_middleware = ["digestauth"]

    rx_pass1 = re.compile(r"([{,])([a-zA-Z][a-zA-Z0-9]+)")
    rx_pass2 = re.compile(r"'")
    rx_pass3 = re.compile(r"(0x[0-9a-zA-Z]+)")

    def fixBrokenJson(self, brokenJson):
        pass1 = self.rx_pass1.sub(r'\1"\2"', brokenJson)  # {abc: 123} -> {"abc": 123}
        pass2 = self.rx_pass2.sub(r'"', pass1)  # ' -> "
        pass3 = self.rx_pass3.sub(r'"\1"', pass2)  # 0x1234 -> "0x1234"
        return pass3

    def parseBrokenJson(self, brokenJson):
        return ujson.loads(self.fixBrokenJson(brokenJson))

    def parseHexInt16(hex):
        result = int(hex, 16)
        if (result & 0x8000) != 0:
            result -= 0x10000
        return result

    def parseHexInt32(hex):
        result = int(hex, 16)
        if (result & 0x80000000) != 0:
            result -= 0x100000000
        return result
