# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Test models references
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from collections import defaultdict

# Third-party modules
from django.db.models import ForeignKey
import pytest

# NOC modules
from noc.core.mongo.fields import PlainReferenceField, ForeignKeyField
from noc.core.model.fields import DocumentReferenceField
from noc.models import is_document, iter_model_id, get_model


def iter_references():
    for model_id in iter_model_id():
        model = get_model(model_id)
        if not model:
            continue
        if is_document(model):
            # MongoEngine document
            for fn in model._fields:
                f = model._fields[fn]
                if isinstance(f, PlainReferenceField):
                    yield f.document_type, model_id, fn
                elif isinstance(f, ForeignKeyField):
                    yield f.document_type, model_id, fn
        else:
            # Django model
            for f in model._meta.fields:
                if isinstance(f, ForeignKey):
                    yield f.remote_field.model, model_id, f.name
                elif isinstance(f, DocumentReferenceField):
                    yield f.document, model_id, f.name


def iter_referred_models():
    referred = defaultdict(list)
    for model, remote_model, remote_field in iter_references():
        referred[model] += [(remote_model, remote_field)]
    for model in referred:
        yield model, referred[model]


@pytest.mark.parametrize("model,refs", iter_referred_models())
def test_on_delete_check(model, refs):
    assert hasattr(model, "_on_delete"), (
        "Must have @on_delete_check decorator (Referenced from %s)" % refs
    )
    x_checks = set(model._on_delete["check"])
    x_checks |= set(model._on_delete["clean"])
    x_checks |= set(model._on_delete["delete"])
    x_checks |= set(model._on_delete["ignore"])
    for c in x_checks:
        assert isinstance(c, tuple), "@on_delete_check decorator must contain only tuples"
        assert len(c) == 2, "@on_delete_check decorator must contain only two-item tuples"


@pytest.mark.parametrize("model,remote_model,remote_field", iter_references())
def test_on_delete_check_reference(model, remote_model, remote_field):
    if not hasattr(model, "_on_delete"):
        pytest.skip("No @on_delete decorator")
    x_checks = set(model._on_delete["check"])
    x_checks |= set(model._on_delete["clean"])
    x_checks |= set(model._on_delete["delete"])
    x_checks |= set(model._on_delete["ignore"])
    assert (
        remote_model,
        remote_field,
    ) in x_checks, '@on_delete_check decorator must refer to ("%s", "%s")' % (
        remote_model,
        remote_field,
    )
