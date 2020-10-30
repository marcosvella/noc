# ----------------------------------------------------------------------
# Link loader
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from .base import BaseLoader
from ..models.link import Link
from noc.inv.models.extnrilink import ExtNRILink


class LinkLoader(BaseLoader):
    """
    Managed Object loader
    """

    name = "link"
    model = ExtNRILink
    data_model = Link
    fields = ["id", "source", "src_mo", "src_interface", "dst_mo", "dst_interface"]

    mapped_fields = {"src_mo": "managedobject", "dst_mo": "managedobject"}

    discard_deferred = True

    def change_object(self, object_id, v):
        v["link"] = None
        v["error"] = None
        v["warn"] = None
        return super().change_object(object_id, v)
