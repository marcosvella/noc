# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# ConfDB virtual-router <name> protocols vrrp syntax
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from __future__ import absolute_import

# NOC modules
from ....defs import DEF
from ....patterns import ANY, INTEGER, IP_ADDRESS, UNIT_NAME, CHOICES

VRRP_SYNTAX = DEF(
    "vrrp",
    [
        DEF(
            "group",
            [
                DEF(
                    ANY,
                    [
                        DEF("description", [DEF(ANY, name="description", gen="make_vrrp_group")]),
                        DEF(
                            "virtual-address",
                            [
                                DEF(
                                    "inet",
                                    [DEF(IP_ADDRESS, name="address", gen="make_vrrp_address")],
                                ),
                                DEF(
                                    "inet6",
                                    [DEF(IP_ADDRESS, name="address", gen="make_vrrp_address6")],
                                ),
                            ],
                        ),
                        DEF(
                            "interface",
                            [DEF(UNIT_NAME, name="interface", gen="make_vrrp_interface")],
                        ),
                        DEF("priority", [DEF(INTEGER, name="priority", gen="make_vrrp_priority")]),
                        DEF(
                            "authentication",
                            [
                                DEF(
                                    "plain-text",
                                    [
                                        DEF(
                                            "key",
                                            [DEF(ANY, name="key", gen="make_vrrp_plain_key")],
                                        )
                                    ],
                                ),
                                DEF(
                                    "md5",
                                    [DEF("key", [DEF(ANY, name="key", gen="make_vrrp_md5_key")])],
                                ),
                            ],
                        ),
                        DEF(
                            "timers",
                            [
                                DEF(
                                    "advertise-interval",
                                    [DEF(INTEGER, name="interval", gen="make_vrrp_adv_interval")],
                                )
                            ],
                        ),
                        DEF("preempt", [DEF(CHOICES("yes", "no"), name="preempt")]),
                    ],
                    name="group",
                    multi=True,
                    required=True,
                )
            ],
            required=True,
        )
    ],
)
