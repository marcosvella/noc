# ---------------------------------------------------------------------
# Qtech.QSW8200.get_lldp_neighbors
# ---------------------------------------------------------------------
# Copyright (C) 2007-2021 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.sa.profiles.Generic.get_lldp_neighbors import Script as BaseScript
from noc.sa.interfaces.igetlldpneighbors import IGetLLDPNeighbors
from noc.core.lldp import (
    LLDP_PORT_SUBTYPE_ALIAS,
    LLDP_PORT_SUBTYPE_COMPONENT,
    LLDP_PORT_SUBTYPE_LOCAL,
    LLDP_PORT_SUBTYPE_MAC,
    LLDP_PORT_SUBTYPE_NAME,
    LLDP_CHASSIS_SUBTYPE_MAC,
    LLDP_CHASSIS_SUBTYPE_NETWORK_ADDRESS,
)


class Script(BaseScript):
    name = "Qtech.QSW8200.get_lldp_neighbors"
    interface = IGetLLDPNeighbors

    rx_int = re.compile(
        r"^(?P<interface>\S+) has\s+1 remotes:\s*\n"
        r"^Remote 1\s*\n"
        r"^-+\s*\n"
        r"^ChassisIdSubtype:\s+(?P<chassis_subtype>\S+)\s*\n"
        r"^ChassisId:\s+(?P<chassis_id>\S+)\s*\n"
        r"^PortIdSubtype:\s+(?P<port_subtype>\S+)\s*\n"
        r"^PortId:\s+(?P<port_id>\S+)\s*\n"
        r"^PortDesc:(?P<port_descr>.*?)\n"
        r"^SysName:(?P<system_name>.*?)\n"
        r"^SysDesc:(?P<system_descr>.*?)\n"
        r"^SysCapSupported:.*?\n"
        r"^SysCapEnabled:(?P<caps>.*?)\n",
        re.MULTILINE | re.DOTALL,
    )
    CHASSIS_TYPE = {
        "macAddress": LLDP_CHASSIS_SUBTYPE_MAC,
        "networkAddress": LLDP_CHASSIS_SUBTYPE_NETWORK_ADDRESS,
    }
    PORT_TYPE = {
        "interfaceAlias": LLDP_PORT_SUBTYPE_ALIAS,
        "portComponent": LLDP_PORT_SUBTYPE_COMPONENT,
        "macAddress": LLDP_PORT_SUBTYPE_MAC,
        "nterfaceName": LLDP_PORT_SUBTYPE_NAME,
        "local": LLDP_PORT_SUBTYPE_LOCAL,
        "ifName": LLDP_PORT_SUBTYPE_NAME,
    }

    def execute_cli(self, **kwargs):
        result = []
        c = self.cli("show lldp remote detail")
        for match in self.rx_int.finditer(c):
            r = {
                "local_interface": match.group("interface"),
                "neighbors": [
                    {
                        "remote_chassis_id_subtype": self.CHASSIS_TYPE[
                            match.group("chassis_subtype")
                        ],
                        "remote_chassis_id": match.group("chassis_id"),
                        "remote_port_subtype": self.PORT_TYPE[match.group("port_subtype")],
                        "remote_port": match.group("port_id"),
                    }
                ],
            }
            system_name = match.group("system_name").strip()
            if system_name and system_name != "N/A":
                r["neighbors"][0]["remote_system_name"] = system_name
            system_descr = match.group("system_descr").strip()
            if system_descr and system_descr != "N/A":
                r["neighbors"][0]["remote_system_description"] = re.sub(
                    r"\n\s{10,}", "", system_descr
                )
            port_descr = match.group("port_descr").strip()
            if port_descr and port_descr != "N/A":
                r["neighbors"][0]["remote_port_description"] = re.sub(r"\n\s{10,}", "", port_descr)
            cap = 0
            caps = match.group("caps").strip()
            if caps and caps != "N/A":
                # Need more examples
                pass
            # Dummy stub
            r["neighbors"][0]["remote_capabilities"] = cap
            result += [r]
        return result
