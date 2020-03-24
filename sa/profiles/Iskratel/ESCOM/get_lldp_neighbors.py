# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Iskratel.ESCOM.get_lldp_neighbors
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetlldpneighbors import IGetLLDPNeighbors
from noc.core.validators import is_ipv4, is_ipv6, is_mac
from noc.core.text import parse_table


class Script(BaseScript):
    name = "Iskratel.ESCOM.get_lldp_neighbors"
    interface = IGetLLDPNeighbors

    rx_port = re.compile(
        r"^Device ID: (?P<device_id>\S+)\s*\n"
        r"^Port ID: (?P<port_id>\S+)\s*\n"
        r"^Capabilities: (?P<capabilities>.+)\s*\n"
        r"^System Name:(?P<system_name>.*)\n"
        r"^System description:(?P<system_description>.*)\n"
        r"^Port description:(?P<port_description>.*)\n",
        re.MULTILINE,
    )
    rx_port2 = re.compile(
        r"chassis id: (?P<device_id>\S+)\n+"
        r"^port id: (?P<port_id>\S+)\n+"
        r"^port description: (?P<port_description>.+)\n+"
        r"^system name: (?P<system_name>\S+|)\n+"
        r"^system description: (?P<system_description>\S+|)\n+"
        r"^.+\n+^system capabilities: (?P<capabilities>.+)",
        re.MULTILINE,
    )
    rx_search = re.compile(
        r"^(?:(?P<chassis_id>\S+)|)\s+(?P<iface>\S+)\s+\d+\s+(?P<port_id>\S+)\s+(?:(?P<caps>\S+)|)?",
        re.MULTILINE,
    )

    def execute(self):
        r = []
        data = []
        try:
            v = self.cli("show lldp neighbors")
        except self.CLISyntaxError:
            raise self.NotSupportedError()
        t = parse_table(v, allow_wrap=True)
        if not t:
            for line in v.splitlines():
                if not self.rx_search.search(line):
                    continue
                data.append(
                    list([c[1], c[0], c[2], "", c[3]] for c in self.rx_search.findall(line))[0]
                )
            t = data
        for i in t:
            chassis_id = i[1]
            if is_ipv4(chassis_id) or is_ipv6(chassis_id):
                chassis_id_subtype = 5
            elif is_mac(chassis_id):
                chassis_id_subtype = 4
            else:
                chassis_id_subtype = 7
            port_id = i[2]
            if is_ipv4(port_id) or is_ipv6(port_id):
                port_id_subtype = 4
            elif is_mac(port_id):
                port_id_subtype = 3
            else:
                port_id_subtype = 7
            caps = 0
            for c in i[4].split(","):
                c = c.strip()
                if c:
                    caps |= {"O": 1, "r": 2, "B": 4, "W": 8, "R": 16, "T": 32, "C": 64, "S": 128}[c]
            """
            if "O" in i[4]:
                caps += 1
            elif "r" in i[4]:
                caps += 2
            elif "B" in i[4]:
                caps += 4
            elif "W" in i[4]:
                caps += 8
            elif "R" in i[4]:
                caps += 16
            elif "T" in i[4]:
                caps += 32
            elif "D" in i[4]:
                caps += 64
            elif "H" in i[4]:
                caps += 128
            """
            neighbor = {
                "remote_chassis_id": chassis_id,
                "remote_chassis_id_subtype": chassis_id_subtype,
                "remote_port": port_id,
                "remote_port_subtype": port_id_subtype,
                "remote_capabilities": caps,
            }
            if i[3]:
                neighbor["remote_system_name"] = i[3]
            if self.is_escom_l:
                try:
                    v = self.cli("show lldp neighbors interface %s" % i[0])
                    match = self.rx_port2.search(v)
                except self.CLISyntaxError:
                    pass
            else:
                try:
                    v = self.cli("show lldp neighbors %s" % i[0])
                    match = self.rx_port.search(v)
                except self.CLISyntaxError:
                    pass
            if match:
                if not neighbor["remote_chassis_id"] and match.group("device_id"):
                    neighbor["remote_chassis_id"] = match.group("device_id")
                neighbor["remote_system_description"] = match.group("system_description").strip()
                neighbor["remote_port_description"] = match.group("port_description").strip()
            r += [{"local_interface": i[0], "neighbors": [neighbor]}]
        return r
