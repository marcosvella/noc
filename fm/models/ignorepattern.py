# ---------------------------------------------------------------------
# IgnorePattern model
# Propagated to collectors
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
from mongoengine.document import Document
from mongoengine.fields import StringField, BooleanField


class IgnorePattern(Document):
    meta = {"collection": "noc.fm.ignorepatterns", "strict": False, "auto_create_index": False}

    source = StringField(unique=True)
    pattern = StringField(unique=True)
    is_active = BooleanField()
    description = StringField(required=False)

    def __str__(self):
        return "%s: %s" % (self.source, self.pattern)
