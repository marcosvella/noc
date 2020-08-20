# ----------------------------------------------------------------------
# BaseBioSegPolicy class
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import logging
from typing import Optional, List, Dict
from django.db import connection

# NOC modules
from noc.inv.models.networksegment import NetworkSegment
from noc.inv.models.link import Link
from noc.sa.models.managedobject import ManagedObject
from noc.core.topology.segment import update_uplinks


class BaseBioSegPolicy(object):
    name = None

    # Persistent target. Effective attacker's policy map
    PERSISTENT_POLICY = {}
    # Floating target. Effective attacker's policy map
    FLOATING_POLICY = {}

    def __init__(
        self,
        attacker: NetworkSegment,
        target: NetworkSegment,
        logger: Optional[logging.Logger] = None,
    ):
        self.attacker = attacker
        self.target = target
        self.logger = logger or logging.getLogger(__name__)
        self._powers: Dict[NetworkSegment, int] = {}

    def trial(self) -> str:
        """
        Perform trial between attacker and target
        :return: Outcome
        """
        raise NotImplementedError

    def get_power(self, seg: NetworkSegment) -> int:
        """
        Calculate network segment's power
        :param seg:
        :return:
        """
        pwr = self._powers.get(seg)
        if pwr is not None:
            return pwr
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT SUM(p.level)
                FROM sa_managedobject mo JOIN sa_managedobjectprofile p ON mo.object_profile_id = p.id
                WHERE segment = %s
            """,
                [str(seg.id)],
            )
            pwr = cursor.fetchall()[0][0] or 0
        self.set_power(seg, pwr)
        return pwr

    def set_power(self, seg: NetworkSegment, power: int) -> None:
        self._powers[seg] = power

    def get_objects(self, seg: NetworkSegment) -> List[ManagedObject]:
        return list(ManagedObject.objects.filter(segment=seg.id))

    def consume_objects(self, src: NetworkSegment, dst: NetworkSegment) -> None:
        """
        Move all objects from src to dst
        :param src:
        :param dst:
        :return:
        """
        self.logger.info("%s consumes objects from %s", dst.name, src.name)
        objects: List[ManagedObject] = self.get_objects(src)
        if not objects:
            self.logger.info("Nothing to consume. Giving up.")
            return
        self.logger.info("Moving %d objects from %s to %s", len(objects), src.name, dst.name)
        dp = 0
        dst_pwr = self.get_power(dst)
        for mo in objects:
            self.logger.info("Moving %s from %s to %s", mo.name, src.name, dst.name)
            mo.segment = dst
            mo.save()
            mo._reset_caches()
            dp += mo.object_profile.level
        self.logger.info(
            "%s power is increased from %d to %d (+%d)", dst.name, dst_pwr, dst_pwr + dp, dp
        )
        # Adjust power caches
        self.set_power(src, 0)
        self.set_power(dst, dst_pwr + dp)
        # Update link segment information
        Link._get_collection().update_many(
            {"linked_segments": src.id}, {"$pull": {"linked_segments": src.id}}
        )
        # Eliminate source segment when possible
        self.destroy_segment(src)
        # Force topology rebuild if moved to persistent segment
        if dst.profile.is_persistent:
            self.refresh_topology(dst)

    @classmethod
    def get_effective_policy_name(cls, target: NetworkSegment, attacker_policy_name: str) -> str:
        if target.profile.is_persistent:
            return cls.PERSISTENT_POLICY[attacker_policy_name]
        return cls.FLOATING_POLICY[attacker_policy_name]

    def refresh_topology(self, seg: NetworkSegment):
        """
        Rebuild topology and recalculate uplinks
        :return:
        """
        update_uplinks(seg.id)

    def destroy_segment(self, seg: NetworkSegment):
        """
        Try to destroy empty network segment

        :param seg:
        :return:
        """
        self.logger.info("Try to destroy segment %s" % seg.name)
        if seg.profile.is_persistent:
            self.logger.info("Cannot destroy persistent segment. Giving up.")
            return
        n_objects = ManagedObject.objects.filter(segment=seg).count()
        if n_objects:
            self.logger.info("Cannot destroy non-empty segment. Giving up.")
            return
        # Link all children segments to parent
        for c_seg in NetworkSegment.objects.filter(parent=seg.id):
            c_seg.parent = seg.parent
            c_seg.save()
        # Finally destroy segment
        self.logger.info("Deleting segment %s" % seg.name)
        seg.delete()
