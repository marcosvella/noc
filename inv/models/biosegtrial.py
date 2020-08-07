# ----------------------------------------------------------------------
# BioSegTrial model
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional

# Third-party modules
from mongoengine.document import Document
from mongoengine.fields import (
    StringField,
    ObjectIdField,
    IntField,
    BooleanField,
)

# NOC modules
from noc.inv.models.networksegment import NetworkSegment
from noc.sa.models.managedobject import ManagedObject


class BioSegTrial(Document):
    meta = {"collection": "biosegtrials", "strict": False, "auto_create_index": False}

    # Reason of the trial
    reason = StringField()
    # Attacker segment
    attacker_id = ObjectIdField()
    # Target segment
    target_id = ObjectIdField()
    # Optional attacker object id
    attacker_object_id = IntField()
    # Optional target object id
    target_object_id = IntField()
    # Trial is processed
    processed = BooleanField(default=False)
    # Trial outcome, i.e. keep, eat, feed, calcify
    outcome = StringField()
    # Error report
    error = StringField()

    def __str__(self):
        return str(self.id)

    @classmethod
    def schedule_trial(
        cls,
        attacker: NetworkSegment,
        target: NetworkSegment,
        attacker_object: Optional[ManagedObject] = None,
        target_object: Optional[ManagedObject] = None,
        reason="manual",
    ) -> Optional["BioSegTrial"]:
        if attacker.profile.is_persistent or target.id == attacker.id:
            return None
        trial = BioSegTrial(
            reason=reason, attacker_id=attacker.id, target_id=target.id, processed=False
        )
        if attacker_object and target_object:
            trial.attacker_object_id = attacker_object.id
            trial.target_object_id = target_object.id
        trial.save()
        return trial

    def set_outcome(self, outcome: str) -> None:
        self.outcome = outcome
        self.processed = True
        self.error = None
        self.save()

    def set_error(self, error: str, fatal: bool = False) -> None:
        self.error = error
        if fatal:
            self.processed = True
        self.save()

    def retry(self) -> None:
        """
        Restart trial

        :return:
        """
        self.processed = None
        self.error = None
        self.outcome = None
        self.save()
