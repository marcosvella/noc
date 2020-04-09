# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# InterfaceValidationPolicy
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import threading
import operator

# Third-party modules
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import (
    StringField,
    BooleanField,
    ListField,
    EmbeddedDocumentField,
    DictField,
)
from jinja2 import Template
import six
import cachetools

# NOC modules
from noc.core.mongo.fields import PlainReferenceField
from noc.core.model.decorator import on_delete_check
from noc.fm.models.alarmclass import AlarmClass
from .confdbquery import ConfDBQuery

id_lock = threading.Lock()


@six.python_2_unicode_compatible
class InterfaceValidationRule(EmbeddedDocument):
    query = PlainReferenceField(ConfDBQuery)
    query_params = DictField()
    filter_query = PlainReferenceField(ConfDBQuery)
    is_active = BooleanField(default=True)
    error_code = StringField()
    error_text_template = StringField(default="{{error}}")
    alarm_class = PlainReferenceField(AlarmClass)
    is_fatal = BooleanField(default=False)

    def __str__(self):
        return self.query.name


@on_delete_check(check=[("inv.InterfaceProfile", "interface_validation_policy")])
@six.python_2_unicode_compatible
class InterfaceValidationPolicy(Document):
    meta = {
        "collection": "interfacevalidationpolicies",
        "strict": False,
        "auto_create_index": False,
    }

    name = StringField(unique=True)
    description = StringField()
    filter_query = PlainReferenceField(ConfDBQuery)
    rules = ListField(EmbeddedDocumentField(InterfaceValidationRule))

    _id_cache = cachetools.TTLCache(maxsize=100, ttl=60)

    def __str__(self):
        return self.name

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_id_cache"), lock=lambda _: id_lock)
    def get_by_id(cls, id):
        return InterfaceValidationPolicy.objects.filter(id=id).first()

    def iter_problems(self, engine, ifname):
        """
        Check rules against ConfDB engine

        :param engine: ConfDB Engine instance
        :param ifname: Interface name
        :return: List of problems
        """
        # Check filter query, if any
        if self.filter_query:
            if not self.filter_query.any(engine, ifname=ifname):
                raise StopIteration
        # Process rules
        for rule in self.rules:
            if not rule.is_active:
                continue
            if rule.filter_query:
                if not rule.filter_query.any(engine, ifname=ifname):
                    continue
            for ctx in rule.query.query(engine, ifname=ifname, **rule.query_params):
                if "error" in ctx:
                    tpl = Template(rule.error_text_template)
                    path = [ifname]
                    if rule.error_code:
                        path += [rule.error_code]
                    problem = {
                        "alarm_class": rule.alarm_class.name if rule.alarm_class else None,
                        "path": path,
                        "message": tpl.render(ctx),
                        "code": rule.error_code or None,
                    }
                    yield problem
                    if rule.is_fatal:
                        raise StopIteration
