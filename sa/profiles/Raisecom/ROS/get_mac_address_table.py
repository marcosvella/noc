# ---------------------------------------------------------------------
# Raisecom.ROS.get_mac_address_table
# ---------------------------------------------------------------------
# Copyright (C) 2007-2017 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.sa.profiles.Generic.get_mac_address_table import Script as BaseScript
from noc.sa.interfaces.igetmacaddresstable import IGetMACAddressTable


class Script(BaseScript):
    name = "Raisecom.ROS.get_mac_address_table"
    interface = IGetMACAddressTable

    rx_line = re.compile(
        r"^(?P<mac>[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})\s+"
        r"(?P<interface>(?:P|PC|port|gigaethernet1/1/)?\d+)\s+"
        r"(?P<vlan_id>\d+)\s*(?P<type>Hit|Static|dynamic)",
        re.MULTILINE | re.IGNORECASE,
    )

    def execute_cli(self,  interface=None, vlan=None, mac=None):
        if not self.is_iscom2624g:
            v = self.cli("show mac-address-table l2-address")
        else:
            v = self.cli("show mac-address all")
        r = []
        for match in self.rx_line.finditer(v):
            r += [
                {
                    "vlan_id": match.group("vlan_id"),
                    "mac": match.group("mac"),
                    "interfaces": [match.group("interface")],
                    "type": {"hit": "D", "dynamic": "D", "static": "S"}[
                        match.group("type").lower()
                    ],
                }
            ]
        return r
