# ----------------------------------------------------------------------
# Glyph Collection
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import os
from threading import Lock
import operator
from typing import Union

# Third-party modules
from mongoengine.document import Document
from mongoengine.fields import StringField, UUIDField, IntField
import cachetools
import bson

# NOC modules
from noc.core.prettyjson import to_json
from noc.core.text import quote_safe_path
from noc.core.mongo.fields import PlainReferenceField
from .font import Font

id_lock = Lock()


class Glyph(Document):
    meta = {
        "collection": "glyphs",
        "strict": False,
        "auto_create_index": False,
        "json_collection": "main.glyphs",
    }
    name = StringField(unique=True)
    uuid = UUIDField(unique=True, binary=True)
    font = PlainReferenceField(Font)
    code = IntField()

    _id_cache = cachetools.TTLCache(maxsize=100, ttl=60)

    def __str__(self):
        return self.name

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_id_cache"), lock=lambda _: id_lock)
    def get_by_id(cls, id: Union[str, bson.ObjectId]) -> "Glyph":
        return Glyph.objects.filter(id=id).first()

    @property
    def json_data(self):
        return {
            "name": self.name,
            "$collection": self._meta["json_collection"],
            "uuid": str(self.uuid),
            "font__name": self.font.name,
            "code": self.code,
        }

    def to_json(self):
        return to_json(self.json_data, order=["name", "$collection", "uuid", "font__name", "code"])

    def get_json_path(self):
        p = [quote_safe_path(n.strip()) for n in self.name.split("|")]
        return os.path.join(*p) + ".json"
