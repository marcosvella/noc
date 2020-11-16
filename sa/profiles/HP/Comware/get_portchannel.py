# ---------------------------------------------------------------------
# HP.Comware.get_portchannel
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.sa.profiles.Generic.get_portchannel import Script as BaseScript
from noc.sa.interfaces.igetportchannel import IGetPortchannel


class Script(BaseScript):
    name = "HP.Comware.get_portchannel"
    interface = IGetPortchannel

    rx_po_members = re.compile(
        r"^(?P<interface>\S+):\s*\n^Aggregation Interface: (?P<agg_interface>\S+)", re.MULTILINE
    )

    def execute(self):
        try:
            v = self.cli("display link-aggregation member-port")
        except self.CLISyntaxError:
            try:
                v = self.cli("display link-aggregation verbose")
            except self.CLISyntaxError:
                v = ""
        r = []
        for match in self.rx_po_members.finditer(v):
            found = False
            for i in r:
                if i["interface"] == match.group("agg_interface"):
                    i["members"] += [match.group("interface")]
                    found = True
                    break
            if not found:
                r += [
                    {
                        "interface": match.group("agg_interface"),
                        "type": "L",
                        "members": [match.group("interface")],
                    }
                ]
        return r
