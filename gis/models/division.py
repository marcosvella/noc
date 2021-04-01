# ---------------------------------------------------------------------
# Division object
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
from mongoengine.document import Document
from mongoengine.fields import (
    StringField,
    DictField,
    BooleanField,
    DateTimeField,
    IntField,
    ListField,
)

# NOC modules
from noc.main.models.label import Label
from noc.core.mongo.fields import PlainReferenceField
from noc.core.comp import smart_text
from noc.core.model.decorator import on_delete_check


@Label.model
@on_delete_check(
    check=[("gis.Street", "parent"), ("gis.Division", "parent"), ("gis.Building", "adm_division")]
)
class Division(Document):
    meta = {
        "collection": "noc.divisions",
        "strict": False,
        "auto_create_index": False,
        "indexes": ["parent", "data", "name"],
    }
    # Division type
    type = StringField(default="A", choices=[("A", "Administrative")])
    #
    parent = PlainReferenceField("self")
    # Normalized name
    name = StringField()
    # street/town/city, etc
    short_name = StringField()
    #
    is_active = BooleanField(default=True)
    # Division level
    level = IntField()
    # Additional data
    # Depends on importer
    data = DictField()
    #
    start_date = DateTimeField()
    end_date = DateTimeField()
    # Labels
    labels = ListField(StringField())
    effective_labels = ListField(StringField())

    def __str__(self):
        if self.short_name:
            return self.short_name
        else:
            return self.name

    def get_children(self):
        return Division.objects.filter(parent=self.id)

    @classmethod
    def get_top(cls, type="A"):
        return Division.objects.filter(parent__exists=False, type=type)

    def get_buildings(self):
        from .building import Building

        return Building.objects.filter(adm_division=self.id).order_by("sort_order")

    @classmethod
    def update_levels(cls):
        """
        Update divisions levels
        """

        def _update(root, level):
            if root.level != level:
                root.level = level
                root.save()
            for c in root.get_children():
                _update(c, level + 1)

        for d in cls.get_top():
            _update(d, 0)

    @property
    def full_path(self):
        r = [smart_text(self)]
        p = self.parent
        while p:
            r = [smart_text(p)] + r
            p = p.parent
        return " | ".join(r)

    @classmethod
    def can_set_label(cls, label):
        if label.enable_division:
            return True
        return False
