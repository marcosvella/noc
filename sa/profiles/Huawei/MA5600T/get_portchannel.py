# ---------------------------------------------------------------------
# Huawei.MA5600T.get_portchannel
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetportchannel import IGetPortchannel


class Script(BaseScript):
    name = "Huawei.MA5600T.get_portchannel"
    interface = IGetPortchannel

    rx_id = re.compile(r"^\s+(?P<id>\d+)\s+\d+", re.MULTILINE)
    rx_iface = re.compile(r"^\s+(?:Master|Sub) Port: (?P<port>\S+)", re.MULTILINE)

    def execute_cli(self, **kwargs):
        r = []
        try:
            # On version V800R013 command return otput after empty result
            s = self.cli(
                "display lacp link-aggregation summary", allow_empty_response=True
            )
        except self.CLISyntaxError:
            return []
        for match in self.rx_id.finditer(s):
            lid = match.group("id")
            c = self.cli("display lacp link-aggregation verbose %s" % lid)
            iface = {"interface": lid, "type": "L", "members": []}
            for match1 in self.rx_iface.finditer(c):
                iface["members"] += [match1.group("port")]
            r += [iface]
        return r
