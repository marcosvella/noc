# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Cisco.SMB.get_arp
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetarp import IGetARP
from noc.core.text import parse_table


class Script(BaseScript):
    name = "Cisco.SMB.get_arp"
    interface = IGetARP
    rx_line_l2 = re.compile(
        r"^vlan\s(?P<vlanid>\d+)\s+(?P<ip>\S+)\s+(?P<mac>\S+)\s+(?P<status>\S+)\s*$"
    )
    rx_line_l3 = re.compile(
        r"^(vlan\s(?P<vlanid>\d+)\s+)?(?P<interface>\S+)\s+"
        r"(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+"
        r"(?P<mac>\S+)\s+(?P<status>\S+)\s*$"
    )

    def execute_cli(self, vrf=None):
        if vrf:
            # only one vrf supported
            raise self.NotSupportedError()
        s = self.cli("show arp")
        reply = []
        for l in s.split("\n"):
            l3_mode = False
            match = self.rx_line_l2.match(l.strip())
            if not match:
                match = self.rx_line_l3.match(l.strip())
                if match:
                    l3_mode = True
                else:
                    continue
            mac = match.group("mac")
            ip = match.group("ip")
            if l3_mode:
                interface = match.group("interface")
            if mac.lower() == "incomplete":
                reply.append({"ip": ip, "mac": None, "interface": None})
            elif l3_mode:
                reply.append({"ip": ip, "mac": mac, "interface": interface})
            else:
                reply.append({"ip": ip, "mac": mac})
        # refine interfaces by mac table
        s = self.cli("show mac address-table")
        for row in parse_table(s):
            mac = row[1]
            port = row[2].strip()
            if port == "0":  # self
                continue
            interface = self.profile.convert_interface_name(port)
            for l in reply:
                ind = reply.index(l)
                if not reply[ind].get("interface"):
                    reply[ind]["interface"] = interface

        return reply
