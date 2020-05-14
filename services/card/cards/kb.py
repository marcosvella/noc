# ----------------------------------------------------------------------
# KB card
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from noc.kb.models.kbentry import KBEntry
from noc.config import config
from .base import BaseCard


class KBCard(BaseCard):
    name = "kb"
    default_template_name = "kbentry"
    model = KBEntry

    def get_object(self, id):
        if id == "0":
            return "Knowlegde DB"
        return super().get_object(id)

    def get_template_name(self):
        if self.id == "0":
            return "kb"
        return self.default_template_name

    def get_data(self):
        return {
            "object": self.object if self.object != "Knowlegde DB" else KBEntry,
            "config": config,
        }
