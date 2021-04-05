# ----------------------------------------------------------------------
# CALCIFY Biosegmentation policy
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Any, Dict, List

# NOC modules
from noc.inv.models.link import Link
from noc.inv.models.interface import Interface
from noc.core.text import alnum_key
from .base import BaseBioSegPolicy


class CalcifyBioSegPolicy(BaseBioSegPolicy):
    """
    Calcify Biosegmentation policy.
    """

    name = "calcify"
    PERSISTENT_POLICY = {
        "merge": "keep",
        "keep": "keep",
        "eat": "keep",
        "feed": "keep",
        "calcify": "calcify",
    }
    FLOATING_POLICY = {
        "merge": "keep",
        "keep": "keep",
        "eat": "keep",
        "feed": "feed",
        "calcify": "calcify",
    }

    def trial(self) -> str:
        self.logger.info("Applying %s policy", self.name)
        if not self.calcified_profile:
            self.logger.info("Cannot calcify without calcified profile")
            raise ValueError("Cannot calcify without calcified profile")
        if not self.calcified_profile.is_persistent:
            self.logger.info("Calcified profile must be persistent")
            raise ValueError("Calcified profile must be persistent")
        self.logger.info("Calcified with profile '%s'" % self.calcified_profile)
        # Change segment profile to calcified one
        self.attacker.segment.profile = self.calcified_profile
        # Change segment name when necessary
        if self.attacker.segment.profile.calcified_name_template:
            name = self.attacker.segment.profile.calcified_name_template.render_body(
                **self.get_template_context()
            )
            # @todo Duplicate segment name - trial merge ?
            self.logger.info("Changed name to '%s'", name)
            self.attacker.segment.name = name
        # Attach to target as child
        self.attacker.segment.parent = self.target.segment
        self.attacker.segment.save()
        # Schedule uplink rebuilding
        self.refresh_topology(self.attacker.segment)
        return "calcify"

    def get_template_context(self) -> Dict[str, Any]:
        local_interfaces: List[Interface] = []
        remote_interfaces: List[Interface] = []
        for link in Link.objects.filter(linked_segments=self.attacker.segment.id):
            for iface in link.interfaces:
                if iface.managed_object.segment.id == self.attacker.segment.id:
                    local_interfaces += [iface]
                else:
                    remote_interfaces += [iface]
        return {
            "interfaces": list(sorted(local_interfaces, key=lambda x: alnum_key(x.name))),
            "parent_interfaces": list(sorted(remote_interfaces, key=lambda x: alnum_key(x.name))),
            "attacker": self.attacker.segment,
            "target": self.target.segment,
        }
