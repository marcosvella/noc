# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Firmware
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import os
import threading
import operator
import uuid

# Third-party modules
import six
from mongoengine.document import Document
from mongoengine.fields import StringField, LongField, UUIDField
from mongoengine.errors import NotUniqueError
import cachetools

# NOC modules
from .vendor import Vendor
from noc.sa.models.profile import Profile
from noc.core.mongo.fields import PlainReferenceField
from noc.core.bi.decorator import bi_sync
from noc.core.prettyjson import to_json
from noc.core.model.decorator import on_delete_check

id_lock = threading.Lock()


@bi_sync
@on_delete_check(
    check=[
        ("sa.ManagedObject", "version"),
        ("sa.ManagedObject", "next_version"),
        ("sa.ManagedObjectSelector", "filter_version"),
        ("inv.FirmwarePolicy", "firmware"),
    ]
)
@six.python_2_unicode_compatible
class Firmware(Document):
    meta = {
        "collection": "noc.firmwares",
        "strict": False,
        "auto_create_index": False,
        "json_collection": "inv.firmwares",
        "json_depends_on": ["sa.profile"],
        "json_unique_fields": ["profile", "vendor", "version"],
        "indexes": [{"fields": ["profile", "vendor", "version"], "unique": True}],
    }
    # Global ID
    uuid = UUIDField(binary=True)
    #
    profile = PlainReferenceField(Profile)
    vendor = PlainReferenceField(Vendor)
    version = StringField()
    description = StringField()
    download_url = StringField()
    # Full name, combined from profile and version
    full_name = StringField()
    # Object id in BI
    bi_id = LongField(unique=True)

    _id_cache = cachetools.TTLCache(1000, ttl=60)
    _bi_id_cache = cachetools.TTLCache(1000, ttl=60)
    _ensure_cache = cachetools.TTLCache(1000, ttl=60)

    def __str__(self):
        return self.full_name if self.full_name else self.version

    def clean(self):
        self.full_name = "%s %s" % (self.profile.name, self.version)
        super(Firmware, self).clean()

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_id_cache"), lock=lambda _: id_lock)
    def get_by_id(cls, id):
        return Firmware.objects.filter(id=id).first()

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_bi_id_cache"), lock=lambda _: id_lock)
    def get_by_bi_id(cls, id):
        return Firmware.objects.filter(bi_id=id).first()

    def to_json(self):
        return to_json(
            {
                "$collection": self._meta["json_collection"],
                "profile__name": self.profile.name,
                "vendor__code": self.vendor.code[0],
                "version": self.version,
                "uuid": self.uuid,
            },
            order=["profile__name", "vendor__code", "version", "uuid"],
        )

    def get_json_path(self):
        return os.path.join(
            self.vendor.code[0], self.profile.name, "%s.json" % self.version.replace(os.sep, "_")
        )

    @classmethod
    @cachetools.cachedmethod(
        operator.attrgetter("_ensure_cache"),
        key=lambda p, v, vv: "%s-%s-%s" % (p.id, v.id, vv),
        lock=lambda _: id_lock,
    )
    def ensure_firmware(cls, profile, vendor, version):
        """
        Get or create firmware by profile, vendor and version
        :param profile:
        :param vendor:
        :param version:
        :return:
        """
        while True:
            firmware = Firmware.objects.filter(
                profile=profile.id, vendor=vendor.id, version=version
            ).first()
            if firmware:
                return firmware
            try:
                firmware = Firmware(
                    profile=profile, vendor=vendor, version=version, uuid=uuid.uuid4()
                )
                firmware.save()
                return firmware
            except NotUniqueError:
                pass  # Already created by concurrent process, reread
