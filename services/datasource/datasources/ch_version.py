# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# CHVersion datasource
# ----------------------------------------------------------------------
# Copyright (C) 2007-2017 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from pymongo import ReadPreference

# NOC modules
from .base import BaseDataSource
from noc.inv.models.firmware import Firmware


class CHVersionDataSource(BaseDataSource):
    name = "ch_version"

    def extract(self):
        for a in (
            Firmware.objects.filter()
            .read_preference(ReadPreference.SECONDARY_PREFERRED)
            .all()
            .order_by("id")
        ):
            yield (a.bi_id, a.id, a.version, a.profile.name, a.vendor.name)
