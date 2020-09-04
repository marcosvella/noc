# ---------------------------------------------------------------------
# ZTE.ZXA10.get_interfaces
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetinterfaces import IGetInterfaces

# NOC modules
import re


class Script(BaseScript):
    name = "ZTE.ZXA10.get_interfaces"
    interface = IGetInterfaces
    TIMEOUT = 240

    type = {
        "GUSQ": "gei_",
        "HUVQ": "gei_",
        "GTGHK": "gpon-olt_",
        "GTGOG": "gpon-onu_",
        "VDWVD": "vdsl_",
        "SCXN": "gei_",
        "SCTM": "gei_",
        "SCXM": "gei_",
        "SCXL": "gei_",
        "SMXA": "gei_",
        "PRWGS": "",
    }
    rx_iface = re.compile(
        r"^(?P<ifname>\S+) is (?P<admin_status>activate|deactivate|down|administratively down|up),\s*"
        r"line protocol is (?P<oper_status>down|up).+\n"
        r"^\s+Description is (?P<descr>.+)\n",
        re.MULTILINE,
    )
    rx_vlan = re.compile(
        r"^(?P<mode>access=0|trunk\>0|hybrid\>=0|accessUn)\s+(?P<pvid>\d+).+\n"
        r"^UntaggedVlan:\s*\n"
        r"(^(?P<untagged>\d+)\s*\n)?"
        r"^TaggedVlan:\s*\n"
        r"(^(?P<tagged>[\d,]+)\s*\n)?",
        re.MULTILINE,
    )
    rx_pvc = re.compile(
        r"^\s+Pvc (?P<pvc_no>\d+):\s*\n"
        r"^\s+Admin Status\s+:\s*(?P<admin_status>enable|disable)\s*\n"
        r"^\s+VPI/VCI\s+:\s*(?P<vpi>\d+)/(?P<vci>\d+)\s*\n",
        re.MULTILINE,
    )
    rx_ip = re.compile(
        r"^(?P<ifname>\S+)\s+AdminStatus is (?P<admin_status>up),\s+"
        r"PhyStatus is (?:up),\s+line protocol is (?P<oper_status>up)\s*\n"
        r"^\s+Internet address is (?P<ip>\S+)\s*\n"
        r"^\s+Broadcast address is .+\n"
        r"^\s+IP MTU is (?P<mtu>\d+) bytes\s*\n",
        re.MULTILINE,
    )
    rx_mac = re.compile(
        r"^\s+Description is (?P<descr>.+)\n^\s+MAC address is (?P<mac>\S+)\s*\n", re.MULTILINE
    )

    def execute_cli(self):
        interfaces = []
        ports = self.profile.fill_ports(self)
        # Get portchannels
        portchannel_members = {}
        for pc in self.scripts.get_portchannel():
            i = self.profile.convert_interface_name(pc["interface"])
            t = pc["type"] == "L"
            for m in pc["members"]:
                portchannel_members[m] = (i, t)
            interfaces += [
                {
                    "name": pc["interface"],
                    "type": "aggregated",
                    "admin_status": True,
                    "oper_status": True,
                    "subinterfaces": [
                        {
                            "name": pc["interface"],
                            "admin_status": True,
                            "oper_status": True,
                            "enabled_afi": ["BRIDGE"],
                        }
                    ],
                }
            ]
        for p in ports:
            if int(p["port"]) < 1 or p["realtype"] == "":
                continue
            prefix = self.type[p["realtype"]]
            if prefix == "gpon-onu_":
                continue
            for i in range(int(p["port"])):
                ifname = "%s%s/%s/%s" % (prefix, p["shelf"], p["slot"], str(i + 1))
                try:
                    v = self.cli("show interface %s" % ifname)
                except self.CLISyntaxError:
                    # In some card we has both gei_ and xgei_ interfaces
                    if prefix == "gei_":
                        ifname = "xgei_%s/%s/%s" % (p["shelf"], p["slot"], str(i + 1))
                        v = self.cli("show interface %s" % ifname)
                match = self.rx_iface.search(v)
                admin_status = bool(match.group("admin_status") == "up")
                oper_status = bool(match.group("oper_status") == "up")
                descr = match.group("descr").strip()
                iface = {
                    "name": ifname,
                    "type": "physical",
                    "admin_status": admin_status,
                    "oper_status": oper_status,
                    "subinterfaces": [],
                }
                if descr not in ["none", "none."]:
                    iface["description"] = descr
                if prefix in ["gei_", "gpon-olt_"]:
                    v = self.cli("show vlan port %s" % ifname)
                    match = self.rx_vlan.search(v)
                    sub = {
                        "name": ifname,
                        "admin_status": admin_status,
                        "oper_status": oper_status,
                        "enabled_afi": ["BRIDGE"],
                    }
                    if match.group("untagged"):
                        sub["untagged_vlan"] = match.group("untagged")
                    if match.group("tagged"):
                        sub["tagged_vlans"] = self.expand_rangelist(match.group("tagged"))
                    iface["subinterfaces"] += [sub]
                    if ifname in portchannel_members:
                        ai, is_lacp = portchannel_members[ifname]
                        iface["aggregated_interface"] = ai
                        iface["enabled_protocols"] = ["LACP"]
                if prefix == "vdsl_":
                    for match in self.rx_pvc.finditer(v):
                        sub = {
                            "name": "%s.%s" % (ifname, match.group("pvc_no")),
                            "admin_status": match.group("admin_status") == "enable",
                            # "oper_status": oper_status  # need more examples
                            "enabled_afi": ["BRIDGE", "ATM"],
                            "vpi": match.group("vpi"),
                            "vci": match.group("vci"),
                        }
                        iface["subinterfaces"] += [sub]
                interfaces += [iface]

        v = self.cli("show ip interface")
        for match in self.rx_ip.finditer(v):
            ifname = match.group("ifname")
            admin_status = bool(match.group("admin_status") == "up")
            oper_status = bool(match.group("oper_status") == "up")
            iface = {
                "name": ifname,
                "admin_status": admin_status,
                "oper_status": oper_status,
                "subinterfaces": [
                    {
                        "name": ifname,
                        "admin_status": admin_status,
                        "oper_status": oper_status,
                        "enabled_afi": ["IPv4"],
                        "ip_addreses": [match.group("ip")],
                        "mtu": match.group("mtu"),
                    }
                ],
            }
            c = self.cli("show interface %s" % ifname)
            match1 = self.rx_mac.search(c)
            iface["mac"] = match1.group("mac")
            iface["subinterfaces"][0]["mac"] = match1.group("mac")
            if ifname.startswith("vlan"):
                iface["type"] = "SVI"
                iface["subinterfaces"][0]["vlan_ids"] = [ifname[4:]]
            else:
                raise self.NotSupportedError()
            interfaces += [iface]

        return [{"interfaces": interfaces}]
