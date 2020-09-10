# ---------------------------------------------------------------------
# Vendor: Eltex
# OS:     WOPLR
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.profile.base import BaseProfile


class Profile(BaseProfile):
    name = "Eltex.WOPLR"
    pattern_prompt = r"^(?P<hostname>\S+)\s*#|~ #"
    command_exit = "exit"
    pattern_syntax_error = r"Invalid command\."

    rx_physical = re.compile(r"^(wlan|eth|br|tun|gre)\d+$")

    @classmethod
    def get_interface_type(cls, name):
        match = cls.rx_physical.match(name)
        if match and match.group(1) in {"eth", "wlan"}:
            return "physical"
        elif match and match.group(1) in {"br", "tun", "gre"}:
            return "SVI"
        return "other"
