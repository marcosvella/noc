# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# PyRule.handler
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
from django.db import models
from south.db import db
# NOC modules
from noc.core.migration.base import BaseMigration


class Migration(BaseMigration):
    def migrate(self):
        db.add_column("main_pyrule", "handler", models.CharField("Handler", max_length=255, null=True, blank=True))
        db.drop_column("main_pyrule", "is_builtin")
        db.execute("ALTER TABLE main_pyrule ALTER \"text\" DROP NOT NULL")
