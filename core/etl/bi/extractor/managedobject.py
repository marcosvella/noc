# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Managed Object Extractor
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from __future__ import absolute_import
import datetime
from collections import defaultdict

# Third-party modules
from pymongo import ReadPreference
from mongoengine.queryset.visitor import Q
import six

# NOC modules
from .base import BaseExtractor
from noc.core.text import ch_escape
from noc.core.etl.bi.stream import Stream
from noc.core.clickhouse.connect import connection
from noc.sa.models.managedobject import ManagedObject, ManagedObjectAttribute
from noc.sa.models.objectcapabilities import ObjectCapabilities
from noc.sa.models.servicesummary import ServiceSummary
from noc.bi.models.managedobjects import ManagedObject as ManagedObjectBI
from noc.inv.models.interface import Interface
from noc.inv.models.link import Link
from noc.inv.models.capability import Capability
from noc.inv.models.discoveryid import DiscoveryID
from noc.fm.models.uptime import Uptime
from noc.fm.models.reboot import Reboot
from noc.fm.models.outage import Outage


class ManagedObjectsExtractor(BaseExtractor):
    name = "managedobjects"
    is_snapshot = True

    # Caps to field mapping
    CAPS_MAP = {
        "Network | STP": "has_stp",
        "Network | CDP": "has_cdp",
        "Network | LLDP": "has_lldp",
        "SNMP": "has_snmp",
        "SNMP | v1": "has_snmp_v1",
        "SNMP | v2c": "has_snmp_v2c",
    }

    # Link discovery method to field mapping
    LD_MAP = {
        "bfd": "bfd_links",
        "cdp": "cdp_links",
        "fdp": "fdp_links",
        "huawei_ndp": "huawei_ndp_links",
        "lacp": "lacp_links",
        "lldp": "lldp_links",
        "mac": "mac_links",
        "nri": "nri_links",
        "oam": "oam_links",
        "rep": "rep_links",
        "stp": "stp_links",
        "udld": "udld_links",
        "xmac": "xmac_links",
    }

    def __init__(self, prefix, start, stop):
        super(ManagedObjectsExtractor, self).__init__(prefix, start, stop)
        self.mo_stream = Stream(ManagedObjectBI, prefix)

    def extract(self, *args, **options):
        nr = 0
        ts = datetime.datetime.now()
        # External data
        stats_start = self.start - datetime.timedelta(days=1)  # configuration ?
        x_data = [
            self.get_interfaces(),
            self.get_links(),
            self.get_caps(),
            self.get_n_subs_n_serv(),
            self.get_reboots(stats_start, self.stop),
            self.get_availability(stats_start, self.stop),
            self.get_object_metrics(stats_start, self.stop),
        ]
        sn = self.get_mo_sn()
        # Extract managed objects
        for mo in ManagedObject.objects.all().iterator():
            did = DiscoveryID.objects.filter(object=mo).first()
            uptime = Uptime.objects.filter(object=mo.id, stop=None).first()
            serials = sn.get(mo.id, [])
            inventory = mo.get_inventory()
            if inventory:
                serials += inventory[0].get_object_serials(chassis_only=False)
            location = ""
            if mo.container:
                location = mo.container.get_address_text()
            r = {
                "ts": ts,
                "managed_object": mo,
                "profile": mo.profile,
                "administrative_domain": mo.administrative_domain,
                "segment": mo.segment,
                "container": mo.container,
                "level": mo.object_profile.level,
                "x": mo.x,
                "y": mo.y,
                "pool": mo.pool,
                "object_profile": mo.object_profile,
                "vendor": mo.vendor,
                "platform": mo.platform,
                "hw_version": mo.get_attr("HW version", default=None),
                "version": mo.version,
                "bootprom_version": mo.get_attr("Boot PROM", default=None),
                "name": ch_escape(mo.name),
                "hostname": ch_escape(did.hostname or "") if did else "",
                "ip": mo.address,
                "is_managed": mo.is_managed,
                "location": ch_escape(location) if location else "",
                "uptime": uptime.last_value if uptime else 0.0,
                "availability": 100.0,
                "tags": [str(t) for t in mo.tags if "{" not in t] if mo.tags else [],  # { - bug
                "serials": list(set(serials))
                # subscribers
                # services
            }
            # Apply external data
            for data in x_data:
                d = data.get(mo.id)
                if d:
                    r.update(d)
            # Submit
            self.mo_stream.push(**r)
            nr += 1
        self.mo_stream.finish()
        return nr

    def get_links(self):
        """
        Build discovery method summary
        :return:
        """

        def link_data(mo):
            links_left = t[mo]
            ld = {
                "n_neighbors": len(neighbors[mo]) - 1,
                "n_links": links_left,
            }
            for lm, field in six.iteritems(self.LD_MAP):
                n = r.get((mo, lm), 0)
                ld[field] = n
                links_left -= n
            ld["other_links"] = links_left
            return ld

        t = defaultdict(int)  # object -> count
        r = defaultdict(int)  # object_id, method -> count
        neighbors = defaultdict(set)  # object_id -> {objects}
        for d in Link._get_collection().find(
            {}, {"_id": 0, "discovery_method": 1, "linked_objects": 1}
        ):
            method = d.get("discovery_method")
            linked = d.get("linked_objects", [])
            for o in linked:
                r[o, method] += 1
                t[o] += 1
                neighbors[o].update(linked)
        return {o: link_data(o) for o in t}

    def get_interfaces(self):
        """
        Build interface counts
        :return:
        """
        r = Interface._get_collection().aggregate(
            [
                {"$match": {"type": "physical"}},
                {"$group": {"_id": "$managed_object", "total": {"$sum": 1}}},
            ]
        )
        return dict((d["_id"], {"n_interfaces": d["total"]}) for d in r)

    def get_caps(self):
        # name -> id map
        caps = dict(
            (self.CAPS_MAP[d["name"]], d["_id"])
            for d in Capability._get_collection().find(
                {"name": {"$in": list(self.CAPS_MAP)}}, {"_id": 1, "name": 1}
            )
        )
        # object -> caps
        add_expr = dict((c, {"$in": [caps[c], "$caps.capability"]}) for c in caps)
        project_expr = dict((c, 1) for c in caps)
        project_expr["_id"] = 1
        return dict(
            (d["_id"], dict((x, d[x]) for x in d if x != "_id"))
            for d in ObjectCapabilities._get_collection().aggregate(
                [{"$addFields": add_expr}, {"$project": project_expr}]
            )
        )

    @staticmethod
    def get_mo_sn():
        """
        Extract serial number from attributes
        :return:
        """
        r = {
            mo_id: [serial]
            for mo_id, serial in ManagedObjectAttribute.objects.filter(
                key="Serial Number"
            ).values_list("managed_object", "value")
        }
        return r

    @staticmethod
    def get_reboots(start_date=None, stop_date=None):
        match = {"ts": {"$gte": start_date, "$lte": stop_date}}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$object", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        data = (
            Reboot._get_collection()
            .with_options()
            .read_preference(ReadPreference.SECONDARY_PREFERRED)
            .aggregate(pipeline)
        )
        # data = data["result"]
        return {rb["_id"]: {"n_reboots": rb["count"]} for rb in data}

    @staticmethod
    def get_availability(start_date, stop_date, skip_zero_avail=False):
        # now = datetime.datetime.now()
        b = start_date
        d = stop_date
        outages = defaultdict(list)
        td = (d - b).total_seconds()
        # q = Q(start__gte=b) | Q(stop__gte=b) | Q(stop__exists=False)
        q = (Q(start__gte=b) | Q(stop__gte=b) | Q(stop__exists=False)) & Q(start__lt=d)
        for o in Outage.objects.filter(q):
            start = max(o.start, b)
            stop = o.stop if (o.stop and o.stop < d) else d
            if (stop - start).total_seconds() == td and skip_zero_avail:
                continue
            outages[o.object] += [(stop - start).total_seconds()]
        # Normalize to percents
        return {
            o: {
                "availability": (td - sum(outages[o])) * 100.0 / td,
                "total_unavailability": int(sum(outages[o])),
                "n_outages": len(outages[o]),
            }
            for o in outages
        }

    @staticmethod
    def get_n_subs_n_serv():
        r = defaultdict(dict)
        service_pipeline = [
            {"$unwind": "$service"},
            {"$group": {"_id": "$managed_object", "service_sum": {"$sum": "$service.summary"}}},
        ]
        for doc in ServiceSummary._get_collection().aggregate(service_pipeline):
            r[doc["_id"]]["n_services"] = doc["service_sum"]
        subscriber_pipeline = [
            {"$unwind": "$subscriber"},
            {
                "$group": {
                    "_id": "$managed_object",
                    "subscriber_sum": {"$sum": "$subscriber.summary"},
                }
            },
        ]
        for doc in ServiceSummary._get_collection().aggregate(subscriber_pipeline):
            r[doc["_id"]]["n_subscribers"] = doc["subscriber_sum"]
        return r

    @staticmethod
    def get_object_metrics(start, stop):
        """

        :param start:
        :type stop: datetime.datetime
        :param stop:
        :type stop: datetime.datetime
        :return:
        """
        r = {}
        bi_map = {
            str(bi_id): mo_id for mo_id, bi_id in ManagedObject.objects.values_list("id", "bi_id")
        }
        ch = connection()
        for row in ch.execute(
            "SELECT managed_object, sum(stp_topology_changes_delta) "
            "FROM routing WHERE ts > '%s' and ts < '%s' GROUP BY managed_object"
            % (
                start.replace(microsecond=0).isoformat(sep=" "),
                stop.replace(microsecond=0).isoformat(sep=" "),
            )
        ):  # delta
            r[bi_map[row[0]]] = {"n_stp_topo_changes": row[1]}
        del bi_map
        return r
