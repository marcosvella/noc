# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Fix outages
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
# NOC modules
from noc.fm.models.outage import Outage


def fix():
    """
    Remove broken outages (stop < start).
    Problem has been related to out-of-order NSQ messages
    and has been fixed 08-NOV-2016
    """
    print("Fixing broken outages")
    r = Outage._get_collection().aggregate(
        [
            {"$project": {"_id": 1, "duration": {"$subtract": ["$stop", "$start"]}}},
            {"$match": {"duration": {"$lte": 0}}},
            {"$project": {"_id": 1}},
        ]
    )
    ids = [d["_id"] for d in r]
    if ids:
        Outage._get_collection().remove({"_id": {"$in": ids}})
    print(" ... Done (%d records fixed)" % len(ids))
