# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Covered Objects
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
import six
from mongoengine.document import Document
from mongoengine.fields import IntField

# NOC modules
from .coverage import Coverage
from noc.inv.models.object import Object
from noc.core.mongo.fields import PlainReferenceField


@six.python_2_unicode_compatible
class CoveredObject(Document):
    meta = {
        "collection": "noc.coveredobjects",
        "strict": False,
        "auto_create_index": False,
        "indexes": ["coverage", "object"],
    }
    coverage = PlainReferenceField(Coverage)
    # Coverage preference.
    # The more is the better
    # Zero means coverage is explicitly disabled for ordering
    preference = IntField(default=100)

    object = PlainReferenceField(Object)

    def __str__(self):
        return "%s %s" % (self.coverage.name, self.object.name or self.object.id)
