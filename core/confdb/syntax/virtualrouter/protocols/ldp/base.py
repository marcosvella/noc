# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# ConfDB virtual-router <name> protocols ldp syntax
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from ....defs import DEF
from ....patterns import UNIT_NAME

LDP_SYNTAX = DEF(
    "ldp",
    [
        DEF(
            "interface",
            [DEF(UNIT_NAME, name="interface", required=True, multi=True, gen="make_ldp_interface")],
        )
    ],
)
