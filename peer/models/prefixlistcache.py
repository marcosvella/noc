# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Peer module models
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
import six
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import (
    StringField,
    IntField,
    ListField,
    EmbeddedDocumentField,
    DateTimeField,
)

# NOC modules
from noc.core.mongo.fields import ForeignKeyField
from .peeringpoint import PeeringPoint


@six.python_2_unicode_compatible
class PrefixListCachePrefix(EmbeddedDocument):
    meta = {"strict": False, "auto_create_index": False}

    prefix = StringField(required=True)
    min = IntField(required=True)
    max = IntField(required=True)

    def __str__(self):
        return self.prefix


@six.python_2_unicode_compatible
class PrefixListCache(Document):
    """
    Prepared prefix-list cache. Can hold IPv4/IPv6 prefixes at same time.
    Prefixes are stored sorted
    """

    meta = {"collection": "noc.prefix_list_cache", "strict": False, "auto_create_index": False}

    peering_point = ForeignKeyField(PeeringPoint)
    name = StringField()
    prefixes = ListField(EmbeddedDocumentField(PrefixListCachePrefix))
    changed = DateTimeField()
    pushed = DateTimeField()

    def __str__(self):
        return " %s/%s" % (self.peering_point.hostname, self.name)

    def cmp_prefixes(self, prefixes):
        """
        Compare cached prefixes with a list of (prefix, min, max)
        """
        return [(c.prefix, c.min, c.max) for c in self.prefixes] == prefixes
