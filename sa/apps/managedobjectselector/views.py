# -*- coding: utf-8 -*-
##----------------------------------------------------------------------
## sa.managedobjectselector application
##----------------------------------------------------------------------
## Copyright (C) 2007-2014 The NOC Project
## See LICENSE for details
##----------------------------------------------------------------------

## NOC modules
from noc.lib.app import ExtModelApplication, view
from noc.lib.app.modelinline import ModelInline
from noc.sa.models.managedobjectselector import (
    ManagedObjectSelector, ManagedObjectSelectorByAttribute)


class ManagedObjectSelectorApplication(ExtModelApplication):
    """
    ManagedObjectSelector application
    """
    title = "ManagedObjectSelector"
    menu = "Setup | ManagedObjectSelector"
    model = ManagedObjectSelector
    query_fields = ["name__icontains", "description__icontains"]
    attrs = ModelInline(ManagedObjectSelectorByAttribute)

    def field_expression(self, o):
        return o.expr

    # @todo: test