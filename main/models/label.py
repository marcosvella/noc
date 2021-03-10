# ----------------------------------------------------------------------
# Label model
# ----------------------------------------------------------------------
# Copyright (C) 2007-2021 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List, Set, Iterable
from threading import Lock
import operator
from dataclasses import dataclass

# Third-party modules
from mongoengine.document import Document
from mongoengine.fields import StringField, IntField, BooleanField, ReferenceField
import cachetools

# NOC modules
from noc.core.model.decorator import on_save, on_delete, is_document
from noc.main.models.remotesystem import RemoteSystem


id_lock = Lock()


@on_save
@on_delete
class Label(Document):
    meta = {
        "collection": "labels",
        "strict": False,
        "auto_create_index": False,
    }

    name = StringField(unique=True)
    description = StringField()
    bg_color1 = IntField(default=0x000000)
    fg_color1 = IntField(default=0xFFFFFF)
    bg_color2 = IntField(default=0x000000)
    fg_color2 = IntField(default=0xFFFFFF)
    # Restrict UI operations
    is_protected = BooleanField(default=False)
    # Label scope
    enable_agent = BooleanField()
    enable_service = BooleanField()
    # Exposition scope
    expose_metric = BooleanField()
    # Integration with external NRI and TT systems
    # Reference to remote system object has been imported from
    remote_system = ReferenceField(RemoteSystem)
    # Object id in remote system
    remote_id = StringField()
    # Caches
    _name_cache = cachetools.TTLCache(maxsize=1000, ttl=60)

    def __str__(self):
        return self.name

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_name_cache"), lock=lambda _: id_lock)
    def get_by_name(cls, name: str) -> Optional["Label"]:
        return Label.objects.filter(name=name).first()

    def clean(self):
        # Wildcard labels are protected
        if self.is_wildcard:
            self.is_protected = True

    def on_save(self):
        if self.is_scoped and not self.is_wildcard:
            self._ensure_wildcards()

    def on_delete(self):
        if self.is_wildcard and any(Label.objects.filter(name__startswith=self.name[:-1])):
            raise ValueError("Cannot delete wildcard label with matched labels")

    @classmethod
    def merge_labels(cls, iter_labels: Iterable[List[str]]) -> List[str]:
        """
        Merge sets of labels, processing the scopes.

        :param iter_labels: Iterator yielding lists of labels
        :return:
        """
        seen_scopes: Set[str] = set()
        seen: Set[str] = set()
        r: List[str] = []
        for labels in iter_labels:
            for label in labels:
                if label in seen:
                    continue
                elif "::" in label:
                    scope = label.rsplit("::", 1)[0]
                    if scope in seen_scopes:
                        continue
                    seen_scopes.add(scope)
                r.append(label)
                seen.add(label)
        return r

    @property
    def is_scoped(self) -> bool:
        """
        Returns True if the label is scoped
        :return:
        """
        return "::" in self.name

    @property
    def is_wildcard(self) -> bool:
        """
        Returns True if the label is protected
        :return:
        """
        return self.name.endswith("::*")

    def iter_scopes(self) -> Iterable[str]:
        """
        Yields all scopes
        :return:
        """
        r = []
        for p in self.name.split("::")[:-1]:
            r.append(p)
            yield "::".join(r)

    def _ensure_wildcards(self):
        """
        Create all necessary wildcards for a scoped labels
        :return:
        """
        for scope in self.iter_scopes():
            wildcard = f"{scope}::*"
            if Label.get_by_name(wildcard):
                continue  # Exists
            # Create wildcard
            Label(
                name=wildcard,
                description=f"Wildcard label for scope {scope}",
                is_protected=True,
                bg_color1=self.bg_color1,
                fg_color1=self.fg_color1,
                bg_color2=self.bg_color2,
                fg_color2=self.fg_color2,
            ).save()

    def get_matched_labels(self) -> List[str]:
        """
        Get list of matched labels for wildcard label
        :return:
        """
        label = self.name
        if label.endswith("::*"):
            return [
                x.name
                for x in Label.objects.filter(name__startswith=label[:-1]).only("name")
                if not x.name.endswith("::*")
            ]
        return [label]

    @classmethod
    def model(cls, m_cls):
        """
        Decorator to denote models with labels.
        Contains field validation and `effective_labels` generation.

        Usage:
        ```
        @Label.model
        class MyModel(...)
        ```

        Adds pre-save hook to check and process `.labels` fields. Raises ValueError
        if any of the labels is not exists.

        Target model may have `iter_effective_labels` method with following signature:
        ```
        def iter_effective_labels(self) -> Iterable[List[str]]
        ```
        which may yield a list of effective labels from related objects to form
        `effective_labels` field.

        :param m_cls: Target model class
        :return:
        """

        def default_iter_effective_labels(instance) -> Iterable[List[str]]:
            yield instance.labels

        def on_pre_save(sender, instance=None, document=None, *args, **kwargs):
            instance = instance or document
            # Clean up labels
            labels = Label.merge_labels(default_iter_effective_labels(instance))
            instance.labels = labels
            # Build and clean up effective labels
            can_expose_label = getattr(sender, "can_expose_label", lambda x: True)
            labels_iter = getattr(sender, "iter_effective_labels", default_iter_effective_labels)
            instance.effective_labels = [
                ll.name
                for ll in Label.objects.filter(name__in=Label.merge_labels(labels_iter(instance)))
                if can_expose_label(ll)
            ]
            # Validate all labels
            all_labels = set(instance.labels) | set(instance.effective_labels)
            can_set_label = getattr(sender, "can_set_label", lambda x: True)
            for label in Label.objects.filter(name__in=list(all_labels)):
                if not can_set_label(label):
                    # Check can_set_label method
                    raise ValueError(f"Invalid label: {label.name}")
                all_labels.discard(label.name)
            if all_labels:
                raise ValueError(f"Invalid labels: {', '.join(all_labels)}")

        # Install handlers
        if is_document(m_cls):
            from mongoengine import signals as mongo_signals

            mongo_signals.pre_save.connect(on_pre_save, sender=m_cls, weak=False)
        else:
            from django.db.models import signals as django_signals

            django_signals.pre_save.connect(on_pre_save, sender=m_cls, weak=False)
        return m_cls
