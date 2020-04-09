# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Validation Policy
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
import six
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import (
    EmbeddedDocumentField,
    StringField,
    BooleanField,
    ListField,
    ReferenceField,
)

# NOC modules
from .validationrule import ValidationRule


@six.python_2_unicode_compatible
class RuleItem(EmbeddedDocument):
    rule = ReferenceField(ValidationRule)
    is_active = BooleanField(default=True)

    def __str__(self):
        return self.rule.name


@six.python_2_unicode_compatible
class ValidationPolicy(Document):
    meta = {"collection": "noc.validationpolicy", "strict": False, "auto_create_index": False}

    name = StringField(unique=True)
    is_active = BooleanField(default=True)
    description = StringField()
    rules = ListField(EmbeddedDocumentField(RuleItem))

    def __str__(self):
        return self.name
