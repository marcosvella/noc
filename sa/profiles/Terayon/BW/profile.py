# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Vendor: Terayon
# OS:     BW
# ---------------------------------------------------------------------
# Copyright (C) 2007-2018 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.profile.base import BaseProfile


class Profile(BaseProfile):
    name = "Terayon.BW"
    pattern_unprivileged_prompt = r"^(.*\x00)?(?P<hostname>.+?)>"
    pattern_prompt = r"Terayon CMTS#(\x1b\[K)?"
    pattern_syntax_error = r"% invalid input"
    command_super = "enable"
    command_submit = "\r"
    command_disable_pager = "terminal length 0"
    pattern_more = [(r"--More--", " ")]
    rogue_chars = [re.compile(b"\x1b\[19D\r\x00Terayon CMTS#"), b"\r"]

    def setup_session(self, script):
        script.cli("\r")
