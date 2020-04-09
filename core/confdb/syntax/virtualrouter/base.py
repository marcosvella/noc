# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# ConfDB virtual-router syntax
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from ..defs import DEF
from ..patterns import ANY, CHOICES, INTEGER, VR_NAME, FI_NAME
from .interfaces.base import VR_INTERFACES_SYNTAX
from .protocols.base import VR_PROTOCOLS_SYNTAX
from .route.base import VR_ROUTE_SYNTAX

VIRTUAL_ROUTER_SYNTAX = DEF(
    "virtual-router",
    [
        DEF(
            VR_NAME,
            [
                DEF(
                    "forwarding-instance",
                    [
                        DEF(
                            FI_NAME,
                            [
                                DEF(
                                    "type",
                                    [
                                        DEF(
                                            CHOICES(
                                                "table",
                                                "bridge",
                                                "vrf",
                                                "vll",
                                                "vpls",
                                                "evpn",
                                                "vxlan",
                                            ),
                                            required=True,
                                            name="type",
                                            gen="make_forwarding_instance_type",
                                        )
                                    ],
                                ),
                                DEF(
                                    "description",
                                    [
                                        DEF(
                                            ANY,
                                            required=False,
                                            name="description",
                                            gen="make_forwarding_instance_description",
                                        )
                                    ],
                                ),
                                DEF(
                                    "route-distinguisher",
                                    [
                                        DEF(
                                            ANY,
                                            required=True,
                                            name="rd",
                                            gen="make_forwarding_instance_rd",
                                        )
                                    ],
                                ),
                                DEF(
                                    "vrf-target",
                                    [
                                        DEF(
                                            "import",
                                            [
                                                DEF(
                                                    ANY,
                                                    multi=True,
                                                    name="target",
                                                    gen="make_forwarding_instance_import_target",
                                                )
                                            ],
                                        ),
                                        DEF(
                                            "export",
                                            [
                                                DEF(
                                                    ANY,
                                                    multi=True,
                                                    name="target",
                                                    gen="make_forwarding_instance_export_target",
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                                DEF(
                                    "vpn-id",
                                    [
                                        DEF(
                                            ANY,
                                            required=True,
                                            name="vpn_id",
                                            gen="make_forwarding_instance_vpn_id",
                                        )
                                    ],
                                ),
                                DEF(
                                    "vlans",
                                    [
                                        DEF(
                                            INTEGER,
                                            [
                                                DEF(
                                                    "name",
                                                    [
                                                        DEF(
                                                            ANY,
                                                            required=True,
                                                            name="name",
                                                            gen="make_vlan_name",
                                                        )
                                                    ],
                                                ),
                                                DEF(
                                                    "description",
                                                    [
                                                        DEF(
                                                            ANY,
                                                            required=True,
                                                            name="description",
                                                            gen="make_vlan_description",
                                                        )
                                                    ],
                                                ),
                                            ],
                                            multi=True,
                                            name="vlan_id",
                                            gen="make_vlan_id",
                                        )
                                    ],
                                ),
                                VR_INTERFACES_SYNTAX,
                                VR_ROUTE_SYNTAX,
                                VR_PROTOCOLS_SYNTAX,
                            ],
                            required=True,
                            multi=True,
                            name="instance",
                            default="default",
                        )
                    ],
                    required=True,
                )
            ],
            required=True,
            multi=True,
            name="vr",
            default="default",
        )
    ],
)
