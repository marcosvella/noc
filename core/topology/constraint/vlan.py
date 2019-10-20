# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# VLANConstraint
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from __future__ import absolute_import
import operator

# Third-party modules
from typing import Dict, Set
import cachetools

# NOC modules
from noc.inv.models.link import Link
from noc.inv.models.subinterface import SubInterface
from .base import BaseConstraint


class VLANConstraint(BaseConstraint):
    """
    Follow only links with specific VLANs
    """

    def __init__(self, vlan=1, allow_tagged=True, allow_untagged=True):
        # type: (int, bool, bool) -> None
        super(VLANConstraint, self).__init__()
        self.vlan = vlan
        self.allow_tagged = allow_tagged
        self.allow_untagged = allow_untagged
        self._is_valid_link_cache = {}  # type: Dict[Link, bool]

    @cachetools.cachedmethod(operator.attrgetter("_is_valid_link_cache"))
    def is_valid_link(self, link):
        # type: (Link) -> bool
        bridged_mo = set()  # type: Set[int]
        tagged_mo = set()  # type: Set[int]
        untagged_mo = set()  # type: Set[int]
        for doc in SubInterface._get_collection().find(
            {"interface": {"$in": link.interface_ids}},
            {
                "_id": 0,
                "managed_object": 1,
                "enabled_afi": 1,
                "untagged_vlan": 1,
                "tagged_vlans": 1,
            },
        ):
            if "BRIDGE" in doc["enabled_afi"]:
                bridged_mo.add(doc["managed_object"])
            if doc.get("untagged_vlan") == self.vlan:
                untagged_mo.add(doc["managed_object"])
            if self.vlan in doc.get("tagged_vlans", []):
                tagged_mo.add(doc["managed_object"])
        return len(bridged_mo) > 1 and (
            (self.allow_tagged and len(tagged_mo) > 1)
            or (self.allow_untagged and len(untagged_mo) > 1)
        )
