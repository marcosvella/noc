# ----------------------------------------------------------------------
# Container datasource
# ----------------------------------------------------------------------
# Copyright (C) 2007-2017 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from pymongo import ReadPreference

# NOC modules
from .base import BaseDataSource
from noc.inv.models.object import Object
from noc.core.bi.decorator import bi_hash


class CHContainerDataSource(BaseDataSource):
    name = "ch_container"

    def extract(self):
        o = Object._get_collection().with_options(
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        for obj in o.find(
            {},
            {"_id": 1, "bi_id": 1, "name": 1, "container": 1, "data.address.text": 1},
            no_cursor_timeout=True,
        ):
            address = [
                a for a in obj["data"] if a and a["interface"] == "address" and a["attr"] == "text"
            ]
            yield (
                obj["bi_id"],
                obj["_id"],
                obj.get("name", ""),
                bi_hash(obj["container"]) if obj.get("container") else "",
                address[0] if address else "",
            )
