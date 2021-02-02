# ---------------------------------------------------------------------
# ActiveAlarm model
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import datetime
from collections import defaultdict

# Third-party modules
from django.template import Template as DjangoTemplate
from django.template import Context
from pymongo import UpdateOne
from mongoengine.document import Document
from mongoengine.fields import (
    StringField,
    DateTimeField,
    ListField,
    EmbeddedDocumentField,
    IntField,
    LongField,
    BooleanField,
    ObjectIdField,
    DictField,
)
from mongoengine.errors import SaveConditionError

# NOC modules
from noc.core.mongo.fields import ForeignKeyField, PlainReferenceField
from noc.aaa.models.user import User
from noc.main.models.style import Style
from noc.main.models.notificationgroup import NotificationGroup
from noc.main.models.template import Template
from noc.sa.models.managedobject import ManagedObject
from noc.sa.models.servicesummary import ServiceSummary, SummaryItem, ObjectSummaryItem
from noc.core.datastream.decorator import datastream
from noc.core.defer import call_later
from noc.core.debug import error_report
from noc.config import config
from noc.core.span import get_current_span
from noc.core.fm.enum import RCA_NONE, RCA_OTHER
from .alarmseverity import AlarmSeverity
from .alarmclass import AlarmClass
from .alarmlog import AlarmLog


@datastream
class ActiveAlarm(Document):
    meta = {
        "collection": "noc.alarms.active",
        "strict": False,
        "auto_create_index": False,
        "indexes": [
            "timestamp",
            "root",
            "-severity",
            ("alarm_class", "managed_object"),
            ("discriminator", "managed_object"),
            ("timestamp", "managed_object"),
            "escalation_tt",
            "escalation_ts",
            "adm_path",
            "segment_path",
            "container_path",
            "uplinks",
            ("alarm_class", "rca_neighbors"),
        ],
    }
    status = "A"

    timestamp = DateTimeField(required=True)
    last_update = DateTimeField(required=True)
    managed_object = ForeignKeyField(ManagedObject)
    alarm_class = PlainReferenceField(AlarmClass)
    severity = IntField(required=True)
    vars = DictField()
    # Calculated alarm discriminator
    # Has meaning only for alarms with is_unique flag set
    # Calculated as sha1("value1\x00....\x00valueN").hexdigest()
    discriminator = StringField(required=False)
    log = ListField(EmbeddedDocumentField(AlarmLog))
    # Manual acknowledgement timestamp
    ack_ts = DateTimeField(required=False)
    # Manual acknowledgement user name
    ack_user = StringField(required=False)
    #
    opening_event = ObjectIdField(required=False)
    closing_event = ObjectIdField(required=False)
    # List of subscribers
    subscribers = ListField(ForeignKeyField(User))
    #
    custom_subject = StringField(required=False)
    custom_style = ForeignKeyField(Style, required=False)
    #
    reopens = IntField(required=False)
    # RCA
    # Reference to root cause (Active Alarm or Archived Alarm instance)
    root = ObjectIdField(required=False)
    # Escalated TT ID in form
    # <external system name>:<external tt id>
    escalation_ts = DateTimeField(required=False)
    escalation_tt = StringField(required=False)
    escalation_error = StringField(required=False)
    # span context
    escalation_ctx = LongField(required=False)
    # Close tt when alarm cleared
    close_tt = BooleanField(default=False)
    # Do not clear alarm until *wait_tt* is closed
    wait_tt = StringField()
    wait_ts = DateTimeField()
    # Directly affected services summary, grouped by profiles
    # (connected to the same managed object)
    direct_services = ListField(EmbeddedDocumentField(SummaryItem))
    direct_subscribers = ListField(EmbeddedDocumentField(SummaryItem))
    # Indirectly affected services summary, groupped by profiles
    # (covered by this and all inferred alarms)
    total_objects = ListField(EmbeddedDocumentField(ObjectSummaryItem))
    total_services = ListField(EmbeddedDocumentField(SummaryItem))
    total_subscribers = ListField(EmbeddedDocumentField(SummaryItem))
    # Template and notification group to send close notification
    clear_template = ForeignKeyField(Template, required=False)
    clear_notification_group = ForeignKeyField(NotificationGroup, required=False)
    # Paths
    adm_path = ListField(IntField())
    segment_path = ListField(ObjectIdField())
    container_path = ListField(ObjectIdField())
    # Uplinks, for topology_rca only
    uplinks = ListField(IntField())
    # RCA neighbor cache, for topology_rca only
    rca_neighbors = ListField(IntField())
    dlm_windows = ListField(IntField())
    # RCA_* enums
    rca_type = IntField(default=RCA_NONE)
    # tags
    tags = ListField(StringField())

    def __str__(self):
        return "%s" % self.id

    def iter_changed_datastream(self, changed_fields=None):
        if config.datastream.enable_alarm:
            yield "alarm", self.id

    def clean(self):
        super().clean()
        if not self.last_update:
            self.last_update = self.timestamp
        data = self.managed_object.data
        self.adm_path = data.adm_path
        self.segment_path = data.segment_path
        self.container_path = data.container_path
        self.uplinks = data.uplinks
        self.rca_neighbors = data.rca_neighbors
        self.dlm_windows = data.dlm_windows
        if not self.id:
            tags = set(self.managed_object.tags or [])
            tags |= set(self.managed_object.object_profile.tags or [])
            self.tags = list(tags)

    def safe_save(self, **kwargs):
        """
        Create new alarm or update existing if still exists
        :param kwargs:
        :return:
        """
        if self.id:
            # Update existing only if exists
            if "save_condition" not in kwargs:
                kwargs["save_condition"] = {"id": self.id}
            try:
                self.save(**kwargs)
            except SaveConditionError:
                pass  # Race condition, closed during update
        else:
            self.save()

    def change_severity(self, user="", delta=None, severity=None, to_save=True):
        """
        Change alarm severity
        """
        if isinstance(user, User):
            user = user.username
        if delta:
            self.severity = max(0, self.severity + delta)
            if delta > 0:
                self.log_message("%s has increased alarm severity by %s" % (user, delta))
            else:
                self.log_message("%s has decreased alarm severity by %s" % (user, delta))
        elif severity:
            if isinstance(severity, int) or isinstance(severity, float):
                self.severity = int(severity)
                self.log_message("%s has changed severity to %s" % (user, severity))
            else:
                self.severity = severity.severity
                self.log_message("%s has changed severity to %s" % (user, severity.name))
        if to_save:
            self.safe_save()

    def log_message(self, message, to_save=True, bulk=None, source=None):
        if bulk:
            bulk += [
                UpdateOne(
                    {"_id": self.id},
                    {
                        "$push": {
                            "log": {
                                "timestamp": datetime.datetime.now(),
                                "from_status": self.status,
                                "to_status": self.status,
                                "message": message,
                                "source": source,
                            }
                        }
                    },
                )
            ]
        self.log += [
            AlarmLog(
                timestamp=datetime.datetime.now(),
                from_status=self.status,
                to_status=self.status,
                message=message,
                source=source,
            )
        ]
        if to_save and not bulk:
            self.safe_save()

    def clear_alarm(self, message, ts=None, force=False, source=None):
        """
        Clear alarm
        :param message: Log clearing message
        :param ts: Clearing timestamp
        :param force: Clear ever if wait_tt seg
        :param source: Source clear alarm
        """
        ts = ts or datetime.datetime.now()
        if self.wait_tt and not force:
            # Wait for escalated tt to close
            if not self.wait_ts:
                self.wait_ts = ts
                self.log_message("Waiting for TT to close")
                call_later(
                    "noc.services.escalator.wait_tt.wait_tt",
                    scheduler="escalator",
                    pool=self.managed_object.escalator_shard,
                    alarm_id=self.id,
                )
            return
        if self.alarm_class.clear_handlers:
            # Process clear handlers
            for h in self.alarm_class.get_clear_handlers():
                try:
                    h(self)
                except Exception:
                    error_report()
        log = self.log + [
            AlarmLog(timestamp=ts, from_status="A", to_status="C", message=message, source=source)
        ]
        a = ArchivedAlarm(
            id=self.id,
            timestamp=self.timestamp,
            clear_timestamp=ts,
            managed_object=self.managed_object,
            alarm_class=self.alarm_class,
            severity=self.severity,
            vars=self.vars,
            log=log,
            ack_ts=self.ack_ts,
            ack_user=self.ack_user,
            root=self.root,
            escalation_ts=self.escalation_ts,
            escalation_tt=self.escalation_tt,
            escalation_error=self.escalation_error,
            escalation_ctx=self.escalation_ctx,
            opening_event=self.opening_event,
            closing_event=self.closing_event,
            discriminator=self.discriminator,
            reopens=self.reopens,
            direct_services=self.direct_services,
            direct_subscribers=self.direct_subscribers,
            total_objects=self.total_objects,
            total_services=self.total_services,
            total_subscribers=self.total_subscribers,
            adm_path=self.adm_path,
            segment_path=self.segment_path,
            container_path=self.container_path,
            uplinks=self.uplinks,
            rca_neighbors=self.rca_neighbors,
            rca_type=self.rca_type,
            tags=self.tags,
        )
        ct = self.alarm_class.get_control_time(self.reopens)
        if ct:
            a.control_time = datetime.datetime.now() + datetime.timedelta(seconds=ct)
        a.save()
        # Send notifications
        if not a.root and not self.reopens:
            a.managed_object.event(
                a.managed_object.EV_ALARM_CLEARED,
                {
                    "alarm": a,
                    "subject": a.subject,
                    "body": a.body,
                    "symptoms": a.alarm_class.symptoms,
                    "recommended_actions": a.alarm_class.recommended_actions,
                    "probable_causes": a.alarm_class.probable_causes,
                },
            )
        elif ct:
            pass
        # Set checks on all consequences
        for d in self._get_collection().find(
            {"root": self.id}, {"_id": 1, "alarm_class": 1, "managed_object": 1}
        ):
            ac = AlarmClass.get_by_id(d["alarm_class"])
            if not ac:
                continue
            t = ac.recover_time
            if not t:
                continue
            call_later(
                "noc.services.correlator.check.check_close_consequence",
                scheduler="correlator",
                pool=self.managed_object.get_effective_fm_pool().name,
                delay=t,
                shard=d.get("managed_object"),
                alarm_id=d["_id"],
            )
        # Clear alarm
        self.delete()
        # Close TT
        # MUST be after .delete() to prevent race conditions
        if a.escalation_tt or self.clear_template:
            if self.clear_template:
                ctx = {"alarm": a}
                subject = self.clear_template.render_subject(**ctx)
                body = self.clear_template.render_body(**ctx)
            else:
                subject = "Alarm cleared"
                body = "Alarm has been cleared"
            call_later(
                "noc.services.escalator.escalation.notify_close",
                scheduler="escalator",
                pool=self.managed_object.escalator_shard,
                max_runs=config.fm.alarm_close_retries,
                alarm_id=self.id,
                tt_id=self.escalation_tt,
                subject=subject,
                body=body,
                notification_group_id=self.clear_notification_group.id
                if self.clear_notification_group
                else None,
                close_tt=self.close_tt,
                login="correlator",
                queue=a.managed_object.tt_queue,
            )
        # Gather diagnostics
        AlarmDiagnosticConfig.on_clear(a)
        # Return archived
        return a

    def get_template_vars(self):
        """
        Prepare template variables
        """
        vars = self.vars.copy()
        vars.update({"alarm": self})
        return vars

    @property
    def subject(self):
        if self.custom_subject:
            s = self.custom_subject
        else:
            ctx = Context(self.get_template_vars())
            s = DjangoTemplate(self.alarm_class.subject_template).render(ctx)
        if len(s) >= 255:
            s = s[:125] + " ... " + s[-125:]
        return s

    @property
    def body(self):
        ctx = Context(self.get_template_vars())
        s = DjangoTemplate(self.alarm_class.body_template).render(ctx)
        return s

    def subscribe(self, user):
        """
        Change alarm's subscribers
        """
        if user.id not in self.subscribers:
            self.subscribers += [user.id]
            self.log_message(
                "%s(%s): has been subscribed"
                % ((" ".join([user.first_name, user.last_name]), user.username)),
                to_save=False,
                source=user.username,
            )
            self.save()

    def unsubscribe(self, user):
        if self.is_subscribed(user):
            self.subscribers = [u.id for u in self.subscribers if u != user.id]
            self.log_message(
                "%s(%s) has been unsubscribed"
                % ((" ".join([user.first_name, user.last_name]), user.username)),
                to_save=False,
                source=user.username,
            )
            self.save()

    def is_subscribed(self, user):
        return user.id in self.subscribers

    def acknowledge(self, user, msg=""):
        self.ack_ts = datetime.datetime.now()
        self.ack_user = user.username
        self.log = self.log + [
            AlarmLog(
                timestamp=self.ack_ts,
                from_status="A",
                to_status="A",
                message="Acknowledged by %s(%s): %s" % (user.get_full_name(), user.username, msg),
                source=user.username,
            )
        ]
        self.save()

    def unacknowledge(self, user, msg=""):
        self.ack_ts = None
        self.ack_user = None
        self.log = self.log + [
            AlarmLog(
                timestamp=datetime.datetime.now(),
                from_status="A",
                to_status="A",
                message="Unacknowledged by %s(%s): %s" % (user.get_full_name(), user.username, msg),
                source=user.username,
            )
        ]
        self.save()

    @property
    def duration(self):
        dt = datetime.datetime.now() - self.timestamp
        return dt.days * 86400 + dt.seconds

    @property
    def display_duration(self):
        duration = datetime.datetime.now() - self.timestamp
        secs = duration.seconds % 60
        mins = (duration.seconds / 60) % 60
        hours = (duration.seconds / 3600) % 24
        days = duration.days
        r = "%02d:%02d:%02d" % (hours, mins, secs)
        if days:
            r = "%dd %s" % (days, r)
        return r

    @property
    def effective_style(self):
        if self.custom_style:
            return self.custom_style
        else:
            return AlarmSeverity.get_severity(self.severity).style

    def get_root(self):
        """
        Get top-level root alarm
        """
        root = self
        while root.root:
            root = get_alarm(root.root)
        return root

    def update_summary(self):
        """
        Recalculate all summaries for given alarm.
        Performs recursive descent
        :return:
        """

        def update_dict(d1, d2):
            for k in d2:
                if k in d1:
                    d1[k] += d2[k]
                else:
                    d1[k] = d2[k]

        services = SummaryItem.items_to_dict(self.direct_services)
        subscribers = SummaryItem.items_to_dict(self.direct_subscribers)
        objects = {self.managed_object.object_profile.id: 1}

        for a in ActiveAlarm.objects.filter(root=self.id):
            a.update_summary()
            update_dict(objects, SummaryItem.items_to_dict(a.total_objects))
            update_dict(services, SummaryItem.items_to_dict(a.total_services))
            update_dict(subscribers, SummaryItem.items_to_dict(a.total_subscribers))
        obj_list = ObjectSummaryItem.dict_to_items(objects)
        svc_list = SummaryItem.dict_to_items(services)
        sub_list = SummaryItem.dict_to_items(subscribers)
        if (
            svc_list != self.total_services
            or sub_list != self.total_subscribers
            or obj_list != self.total_objects
        ):
            ns = ServiceSummary.get_severity(
                {"service": services, "subscriber": subscribers, "objects": objects}
            )
            self.total_objects = obj_list
            self.total_services = svc_list
            self.total_subscribers = sub_list
            if ns != self.severity:
                self.change_severity(severity=ns, to_save=False)
            self.safe_save()

    def _get_path_summary_bulk(self):
        def list_to_dict(summary):
            if not summary:
                return {}
            return {d["profile"]: d["summary"] for d in summary}

        def e_list_to_dict(summary):
            if not summary:
                return {}
            return {d.profile: d.summary for d in summary}

        def dict_to_list(d):
            return [{"profile": k, "summary": d[k]} for k in sorted(d)]

        def get_summary(docs, key, direct=None):
            r = direct.copy() if direct else {}
            for doc in docs:
                dv = doc.get(key)
                if not dv:
                    continue
                for k in dv:
                    nv = dv[k]
                    if nv:
                        r[k] = r.get(k, 0) + nv
            return r

        def get_root_path(alarm_id, path=None):
            path = path or []
            if alarm_id in path:
                raise ValueError("Loop detected: %s" % (str(x) for x in path))
            path = path + [alarm_id]
            root = alarms[alarm_id].get("root")
            if not root:
                return path
            return get_root_path(root, path)

        alarms = {}  # id -> alarm doc
        children = defaultdict(list)  # id -> [alarm doc, ..]
        # Inject current alarm
        alarms[self.id] = {
            "_id": self.id,
            "root": self.root,
            "severity": self.severity,
            "total_objects": e_list_to_dict(self.total_objects),
            "total_services": e_list_to_dict(self.total_services),
            "total_subscribers": e_list_to_dict(self.total_subscribers),
        }
        # Collect relevant neighbors
        for doc in ActiveAlarm._get_collection().aggregate(
            [
                # Starting from given alarm
                {"$match": {"_id": self.root}},
                # Add to 'path' field all alarm upwards
                {
                    "$graphLookup": {
                        "from": "noc.alarms.active",
                        "connectFromField": "root",
                        "connectToField": "_id",
                        "startWith": "$root",
                        "as": "path",
                        "maxDepth": 50,
                    }
                },
                # Append the necessary fields of given alarm to 'path' field
                # and wipe out all other fields
                {
                    "$project": {
                        "_id": 0,
                        "path": {
                            "$concatArrays": [
                                "$path",
                                [
                                    {
                                        "_id": "$_id",
                                        "root": "$root",
                                        "severity": "$severity",
                                        "direct_services": "$direct_services",
                                        "direct_subscribers": "$direct_subscribers",
                                        "total_objects": "$total_objects",
                                        "total_services": "$total_services",
                                        "total_subscribers": "$total_subscribers",
                                    }
                                ],
                            ]
                        },
                    }
                },
                # Convert path field to the list of documents
                {"$unwind": "$path"},
                # Normalize resulting documents
                {
                    "$project": {
                        "_id": "$path._id",
                        "root": "$path.root",
                        "severity": "$path.severity",
                        "direct_services": "$path.direct_services",
                        "direct_subscribers": "$path.direct_subscribers",
                        "total_objects": "$path.total_objects",
                        "total_services": "$path.total_services",
                        "total_subscribers": "$path.total_subscribers",
                    }
                },
                # Add all children alarms to 'children' field
                {
                    "$lookup": {
                        "from": "noc.alarms.active",
                        "localField": "_id",
                        "foreignField": "root",
                        "as": "children",
                    }
                },
                # Append the neccessary fields of path alarms to `children` field
                # and wipe out all other fields
                {
                    "$project": {
                        "_id": 0,
                        "children": {
                            "$concatArrays": [
                                "$children",
                                [
                                    {
                                        "_id": "$_id",
                                        "root": "$root",
                                        "severity": "$severity",
                                        "direct_services": "$direct_services",
                                        "direct_subscribers": "$direct_subscribers",
                                        "total_objects": "$total_objects",
                                        "total_services": "$total_services",
                                        "total_subscribers": "$total_subscribers",
                                    }
                                ],
                            ]
                        },
                    }
                },
                # Convert path field to the list of documents
                {"$unwind": "$children"},
                # Normalize resulting documents
                {
                    "$project": {
                        "_id": "$children._id",
                        "root": "$children.root",
                        "severity": "$children.severity",
                        "direct_services": "$children.direct_services",
                        "direct_subscribers": "$children.direct_subscribers",
                        "total_objects": "$children.total_objects",
                        "total_services": "$children.total_services",
                        "total_subscribers": "$children.total_subscribers",
                    }
                },
            ]
        ):
            # May contains duplicates, perform deduplication
            doc["direct_services"] = list_to_dict(doc.get("direct_services"))
            doc["direct_subscribers"] = list_to_dict(doc.get("direct_subscribers"))
            doc["total_objects"] = list_to_dict(doc.get("total_objects"))
            doc["total_services"] = list_to_dict(doc.get("total_services"))
            doc["total_subscribers"] = list_to_dict(doc.get("total_subscribers"))
            if doc["_id"] == self.id:
                doc["root"] = self.root
            alarms[doc["_id"]] = doc

        for doc in alarms.values():
            children[doc.get("root")] += [doc]

        # Get path to from current root upwards to global root
        # Check for loops, raise Value error if loop detected
        root_path = get_root_path(self.root)
        bulk = []
        now = datetime.datetime.now()
        for root in root_path:
            doc = alarms[root]
            consequences = children[root]
            total_objects = get_summary(
                consequences, "total_objects", {self.managed_object.object_profile.id: 1}
            )
            total_services = get_summary(consequences, "total_services", doc.get("direct_services"))
            total_subscribers = get_summary(
                consequences, "total_subscribers", doc.get("direct_subscribers")
            )
            if (
                doc["total_objects"] != total_objects
                or doc["total_services"] != total_services
                or doc["total_subscribers"] != total_subscribers
            ):
                # Changed
                severity = ServiceSummary.get_severity(
                    {
                        "service": total_services,
                        "subscriber": total_subscribers,
                        "objects": total_objects,
                    }
                )
                op = {
                    "$set": {
                        "severity": severity,
                        "total_objects": dict_to_list(total_objects),
                        "total_services": dict_to_list(total_services),
                        "total_subscribers": dict_to_list(total_subscribers),
                    }
                }
                if severity != doc.get("severity"):
                    op["$push"] = {
                        "log": {
                            "timestamp": now,
                            "from_status": "A",
                            "to_status": "A",
                            "message": "Severity changed to %d" % severity,
                        }
                    }
                bulk += [UpdateOne({"_id": root}, op)]
        return bulk

    def set_root(self, root_alarm, rca_type=RCA_OTHER):
        """
        Set root cause
        """
        if self.root:
            return
        if self.id == root_alarm.id:
            raise Exception("Cannot set self as root cause")
        # Set root
        self.root = root_alarm.id
        self.rca_type = rca_type
        try:
            bulk = self._get_path_summary_bulk()
        except ValueError:
            return  # Loop detected
        bulk += [
            UpdateOne({"_id": self.id}, {"$set": {"root": root_alarm.id, "rca_type": rca_type}})
        ]
        self.log_message("Alarm %s has been marked as root cause" % root_alarm.id, bulk=bulk)
        # self.save()  Saved by log_message
        root_alarm.log_message("Alarm %s has been marked as child" % self.id, bulk=bulk)
        if self.id:
            ActiveAlarm._get_collection().bulk_write(bulk, ordered=True)

    def escalate(self, tt_id, close_tt=False, wait_tt=None):
        self.escalation_tt = tt_id
        self.escalation_ts = datetime.datetime.now()
        self.close_tt = close_tt
        self.wait_tt = wait_tt
        self.log_message("Escalated to %s" % tt_id)
        q = {"_id": self.id}
        op = {
            "$set": {
                "escalation_tt": self.escalation_tt,
                "escalation_ts": self.escalation_ts,
                "close_tt": self.close_tt,
                "wait_tt": self.wait_tt,
                "escalation_error": None,
            }
        }
        r = ActiveAlarm._get_collection().update_one(q, op)
        if r.acknowledged and not r.modified_count:
            # Already closed, update archive
            ArchivedAlarm._get_collection().update_one(q, op)

    def set_escalation_error(self, error):
        self.escalation_error = error
        self._get_collection().update_one({"_id": self.id}, {"$set": {"escalation_error": error}})

    def set_escalation_context(self):
        current_context, current_span = get_current_span()
        if current_context or self.escalation_ctx:
            self.escalation_ctx = current_context
            self._get_collection().update_one(
                {"_id": self.id}, {"$set": {"escalation_ctx": current_context}}
            )

    def set_clear_notification(self, notification_group, template):
        self.clear_notification_group = notification_group
        self.clear_template = template
        self.safe_save(save_condition={"managed_object": {"$exists": True}, "id": self.id})

    def iter_consequences(self):
        """
        Generator yielding all consequences alarm
        """
        for a in ActiveAlarm.objects.filter(root=self.id):
            yield a
            yield from a.iter_consequences()

    def iter_affected(self):
        """
        Generator yielding all affected managed objects
        """
        seen = {self.managed_object}
        yield self.managed_object
        for a in self.iter_consequences():
            if a.managed_object not in seen:
                seen.add(a.managed_object)
                yield a.managed_object

    def iter_escalated(self):
        """
        Generator yielding all escalated consequences
        """
        for a in self.iter_consequences():
            if a.escalation_tt:
                yield a


# Avoid circular references
from .archivedalarm import ArchivedAlarm
from .utils import get_alarm
from .alarmdiagnosticconfig import AlarmDiagnosticConfig
