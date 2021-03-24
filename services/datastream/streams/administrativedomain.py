# ----------------------------------------------------------------------
# administrativedomain datastream
# ----------------------------------------------------------------------
# Copyright (C) 2007-2018 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from noc.core.datastream.base import DataStream
from noc.sa.models.administrativedomain import AdministrativeDomain
from noc.core.comp import smart_text


def qs(s):
    if not s:
        return ""
    return smart_text(s)


class AdmDomainDataStream(DataStream):
    name = "administrativedomain"
    clean_id = DataStream.clean_id_int

    @classmethod
    def get_object(cls, id):
        ad = AdministrativeDomain.objects.filter(id=id)[:1]
        if not ad:
            raise KeyError()
        ad = ad[0]
        r = {"id": str(ad.id), "name": qs(ad.name)}
        if ad.parent:
            r["parent"] = str(ad.parent.id)
        if ad.labels:
            r["labels"] = [qs(t) for t in ad.labels]
            # Alias for compat
            r["tags"] = [qs(t) for t in ad.labels]
        cls._apply_remote_system(ad, r)
        return r

    @staticmethod
    def _apply_remote_system(mo, r):
        if mo.remote_system:
            r["remote_system"] = {"id": str(mo.remote_system.id), "name": qs(mo.remote_system.name)}
            r["remote_id"] = mo.remote_id
