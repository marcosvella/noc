# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# KBEntryTemplate model
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# Third-party modules
import six
from django.db import models

# NOC modules
from noc.core.model.base import NOCModel
from noc.lib.app.site import site
from noc.core.model.fields import AutoCompleteTagsField
from noc.main.models.language import Language
from noc.services.web.apps.kb.parsers.loader import loader


@six.python_2_unicode_compatible
class KBEntryTemplate(NOCModel):
    """
    KB Entry Template
    """

    class Meta(object):
        verbose_name = "KB Entry Template"
        verbose_name_plural = "KB Entry Templates"
        app_label = "kb"
        db_table = "kb_kbentrytemplate"
        ordering = ("id",)

    name = models.CharField("Name", max_length=128, unique=True)
    subject = models.CharField("Subject", max_length=256)
    body = models.TextField("Body")
    language = models.ForeignKey(
        Language,
        verbose_name="Language",
        limit_choices_to={"is_active": True},
        on_delete=models.CASCADE,
    )
    markup_language = models.CharField(
        "Markup Language", max_length="16", choices=[(x, x) for x in loader]
    )
    tags = AutoCompleteTagsField("Tags", null=True, blank=True)

    rx_template_var = re.compile("{{([^}]+)}}", re.MULTILINE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return site.reverse("kb:kbentrytemplate:change", self.id)

    @property
    def _var_list(self):
        """
        Returns template variables list
        """
        var_set = set(self.rx_template_var.findall(self.subject))
        var_set.update(self.rx_template_var.findall(self.body))
        return sorted(var_set)
