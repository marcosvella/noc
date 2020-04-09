# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# FailedEvent model
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import datetime
import time

# Third-party modules
import six
from mongoengine.document import Document
from mongoengine.fields import DateTimeField, StringField, EmbeddedDocumentField, ListField

# NOC modules
from noc.sa.models.managedobject import ManagedObject
from noc.core.mongo.fields import ForeignKeyField, RawDictField
from .eventlog import EventLog


@six.python_2_unicode_compatible
class FailedEvent(Document):
    """
    Events that caused noc-classifier traceback
    """

    meta = {"collection": "noc.events.failed", "strict": False, "auto_create_index": False}
    status = "F"
    # Fields
    timestamp = DateTimeField(required=True)
    managed_object = ForeignKeyField(ManagedObject, required=True)
    source = StringField()
    raw_vars = RawDictField(required=True)
    # NOC version caused traceback
    version = StringField(required=True)
    traceback = StringField()
    log = ListField(EmbeddedDocumentField(EventLog))

    def __str__(self):
        return "%s" % self.id

    def mark_as_new(self, message=None):
        """
        Move to unclassified queue
        """
        from noc.core.nsq.pub import nsq_pub

        data = {"source": self.source}
        data.update(self.raw_vars)
        msg = {
            "id": str(self.id),
            "ts": time.mktime(self.timestamp.timetuple()),
            "object": self.managed_object.id,
            "data": data,
        }
        nsq_pub("events.%s" % self.managed_object.get_effective_fm_pool().name, msg)
        self.delete()

    def log_message(self, message):
        self.log += [
            EventLog(
                timestamp=datetime.datetime.now(),
                from_status=self.status,
                to_status=self.status,
                message=message,
            )
        ]
        self.save()
