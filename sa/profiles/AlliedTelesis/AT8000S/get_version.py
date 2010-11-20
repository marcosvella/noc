# -*- coding: utf-8 -*-
##----------------------------------------------------------------------
## AlliedTelesis.AT8000S.get_version
##----------------------------------------------------------------------
## Copyright (C) 2007-2010 The NOC Project
## coded by azhur
## See LICENSE for details
##----------------------------------------------------------------------
"""
"""
import noc.sa.script
from noc.sa.interfaces import IGetVersion
import re

rx_ver=re.compile(r"^\s*(?:\w*\s+){1,2}\s*(?P<version>v?[\d.]+)\s",re.MULTILINE|re.DOTALL)

class Script(noc.sa.script.Script):
    name="AlliedTelesis.AT8000S.get_version"
    cache=True
    implements=[IGetVersion]
    def execute(self):
        if self.snmp and self.access_profile.snmp_ro:
            try:
                ver=self.snmp.get("1.3.6.1.4.1.89.2.4.0")
                return {
                    "vendor"    : "Allied Telesis",
                    "platform"  : "AT8000S",
                    "version"   : ver,
                }
            except self.snmp.TimeOutError:
                pass
        v=self.cli("show version")
        match=rx_ver.search(v)
        return {
            "vendor"    : "Allied Telesis",
            "platform"  : "AT8000S",
            "version"   : match.group("version"),
        }
