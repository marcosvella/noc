# ----------------------------------------------------------------------
# ifdesc check
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List, Tuple, Dict

# NOC modules
from noc.services.discovery.jobs.base import TopologyDiscoveryCheck
from noc.inv.models.interface import Interface
from noc.inv.models.ifdescpatterns import IfDescPatterns
from noc.main.models.handler import Handler
from noc.sa.models.managedobject import ManagedObject


class IfDescCheck(TopologyDiscoveryCheck):
    """
    IfDesc Topology discovery
    """

    name = "ifdesc"
    OBJ_REF_NAMES = {"name", "address", "hostname"}
    IFACE_REF_NAMES = {"interface", "ifindex"}
    MAX_MO_CANDIDATES = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.if_cache: Dict[int, Dict[str, Interface]] = {}

    def handler(self):
        candidates: List[Tuple[Interface, Interface]] = []
        ifaces = self.get_object_interfaces(self.object)
        for iface in ifaces.values():
            ri = self.resolve_remote_interface(iface)
            if ri:
                self.logger.info(
                    "Candidate link: %s:%s -- %s:%s",
                    iface.managed_object.name,
                    iface.name,
                    ri.managed_object.name,
                    ri.name,
                )
                candidates += [(iface, ri)]
        # Check other side
        if self.object.object_profile.ifdesc_symmetric:
            confirmed: List[Tuple[Interface, Interface]] = []
            for li, ri in candidates:
                riri = self.resolve_remote_interface(ri)
                if not riri:
                    self.logger.info(
                        "Failed symmetric check: %s:%s -- %s:%s, not found, ignoring",
                        li.managed_object.name,
                        li.name,
                        ri.managed_object.name,
                        ri.name,
                    )
                    continue
                if riri.managed_object.id != self.object.id:
                    self.logger.info(
                        "Failed symmetric check: %s:%s -- %s:%s, leading to other object %s, ignoring",
                        li.managed_object.name,
                        li.name,
                        ri.managed_object.name,
                        ri.name,
                        riri.managed_object.name,
                    )
                    continue
                if riri.name != li.name:
                    self.logger.info(
                        "Failed symmetric check: %s:%s -- %s:%s, leading to other interface %s, ignoring",
                        li.managed_object.name,
                        li.name,
                        ri.managed_object.name,
                        ri.name,
                        riri.name,
                    )
                    continue
                confirmed += [(li, ri)]
            candidates = confirmed
        # Link remaining
        for li, ri in candidates:
            self.confirm_link(li.managed_object, li.name, ri.managed_object, ri.name)

    def resolve_remote_interface(self, iface: Interface) -> Optional[Interface]:
        direction = "local" if iface.managed_object.id == self.object.id else "remote"
        if not iface.description or not iface.description.strip():
            self.logger.info("%s interface %s has no description. Ignoring", direction, iface.name)
            return None
        if not iface.type == "physical":
            self.logger.info(
                "%s interface %s has invalid type %s. Ignoring", direction, iface.name, iface.type
            )
            return None
        # Try Interface Profile Handler
        if_prof = iface.get_profile()
        if if_prof.ifdesc_handler:
            ri = self.resolve_via_handler(if_prof.ifdesc_handler, iface)
            if ri:
                return ri
        # Try Interface Profile Patterns
        if if_prof.ifdesc_patterns:
            ri = self.resolve_via_patterns(if_prof.ifdesc_patterns, iface)
            if ri:
                return ri
        # Try Object Profile Handler
        if self.object.object_profile.ifdesc_handler:
            ri = self.resolve_via_handler(self.object.object_profile.ifdesc_handler, iface)
            if ri:
                return ri
        # Try Object Profile Patterns
        if self.object.object_profile.ifdesc_patterns:
            ri = self.resolve_via_patterns(self.object.object_profile.ifdesc_patterns, iface)
            if ri:
                return ri
        # Not found
        return None

    def resolve_via_handler(self, hi: Handler, iface: Interface) -> Optional[Interface]:
        """
        Try to resolve remote interface via handler
        :param hi:
        :param iface:
        :return:
        """
        handler = hi.get_handler()
        return handler(self.object, iface)

    def resolve_via_patterns(
        self, patterns: IfDescPatterns, iface: Interface
    ) -> Optional[Interface]:
        self.logger.debug("[%s] Checking patterns %s", iface.name, patterns.name)
        for matches in patterns.iter_match(iface.description):
            self.logger.debug("Matches %s", matches)
            obj_ref = {n: matches[n] for n in matches if n in self.OBJ_REF_NAMES}
            if not obj_ref:
                self.logger.debug(
                    "No object reference extracted. At least one of the %s must be present",
                    ", ".join(self.OBJ_REF_NAMES),
                )
                continue
            ro = self.resolve_object_via_patterns(iface.managed_object, **obj_ref)
            if not ro:
                self.logger.debug("Object cannot be resolved. Skipping")
                continue
            iface_ref = {n: matches[n] for n in matches if n in self.IFACE_REF_NAMES}
            if not obj_ref:
                self.logger.debug(
                    "No interface reference extracted. At least one of the %s must be present",
                    ", ".join(self.IFACE_REF_NAMES),
                )
                continue
            ri = self.resolve_interface_via_patterns(ro, **iface_ref)
            if not ri:
                self.logger.debug("Interface cannot be resolved. Skipping")
            return ri
        return None

    def resolve_object_via_patterns(
        self,
        mo: ManagedObject,
        name: Optional[str] = None,
        address: Optional[str] = None,
        hostname: Optional[str] = None,
    ) -> Optional[ManagedObject]:
        def get_nearest_object(objects: List[ManagedObject]) -> Optional[ManagedObject]:
            # Prefer same pool
            left = [x for x in objects if x.pool.id == mo.pool.id]
            if len(left) == 1:
                return left[0]
            # Prefer same segment
            left = [x for x in objects if x.segment.id == mo.segment.id]
            if len(left) == 1:
                return left[0]
            return None

        if name:
            # Full name match
            mo = ManagedObject.objects.filter(name=name).first()
            if mo:
                return mo
            # Partial name match
            if "#" not in name:
                mos = ManagedObject.objects.filter(name__startswith=name + "#")[
                    : self.MAX_MO_CANDIDATES
                ]
                mo = get_nearest_object(mos)
                if mo:
                    return mo
        if address:
            # Address match
            mos = ManagedObject.objects.filter(address=address)[: self.MAX_MO_CANDIDATES]
            mo = get_nearest_object(mos)
            if mo:
                return mo
        if hostname:
            mo = self.get_neighbor_by_hostname(hostname)
            if mo:
                return mo
        return None

    def resolve_interface_via_patterns(
        self, mo: ManagedObject, interface: Optional[str] = None, ifindex: Optional[str] = None
    ) -> Optional[Interface]:
        ifaces = self.get_object_interfaces(mo)
        if not ifaces:
            return None
        if interface:
            interface = self.get_remote_interface(mo, interface)
            if interface:
                iface = ifaces.get(interface)
                if iface:
                    return iface
        if ifindex:
            ifi = int(ifindex)
            matched = [x for x in ifaces.values() if x.ifindex == ifi]
            if len(matched) == 1:
                return matched[0]
        return None

    def get_object_interfaces(self, mo: ManagedObject) -> Dict[str, Interface]:
        ifaces = self.if_cache.get(mo.id)
        if ifaces is not None:
            return ifaces
        ifaces = {
            x.name: x for x in Interface.objects.filter(managed_object=mo.id, type="physical")
        }
        self.if_cache[mo.id] = ifaces
        return ifaces
