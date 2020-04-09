# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# ConfDB hints protocols cdp syntax
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from ...defs import DEF
from ...patterns import BOOL, IF_NAME

HINTS_PROTOCOLS_CDP = DEF(
    "cdp",
    [
        DEF("status", [DEF(BOOL, name="status", required=True, gen="make_global_cdp_status")]),
        DEF(
            "interface",
            [
                DEF(
                    IF_NAME,
                    [DEF("off", gen="make_cdp_interface_disable")],
                    multi=True,
                    name="interface",
                )
            ],
        ),
    ],
)
