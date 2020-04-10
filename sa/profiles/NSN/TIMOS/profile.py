# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Vendor: NSN
# OS:     TIMOS
# ----------------------------------------------------------------------
# Copyright (C) 2007-2018 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

import re
from noc.core.profile.base import BaseProfile


class Profile(BaseProfile):
    name = "NSN.TIMOS"
    pattern_prompt = r"^\S+?#"
    pattern_more = r"^Press any key to continue.*$"
    pattern_syntax_error = r"Error: Bad command\.|Error: Invalid parameter\."
    command_disable_pager = "environment no more"
    command_exit = "logout"
    config_volatile = [r"^# Finished.*$", r"^# Generated.*$"]
    command_more = " "
    rogue_chars = [re.compile(b"\r\s+\r"), b"\r"]

    def convert_interface_name(self, s):
        if "," in s:
            s = s.split(",", 1)[0].strip()
        return s
