#!./bin/python
# ---------------------------------------------------------------------
# noc-correlator daemon
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import sys
import datetime
import re
from collections import defaultdict
from typing import Optional, Dict, List
import operator

# Third-party modules
import orjson

# NOC modules
from noc.config import config
from noc.core.service.tornado import TornadoService
from noc.core.scheduler.scheduler import Scheduler
from noc.core.mongo.connection import connect
from services.correlator.rule import Rule
from services.correlator.rcacondition import RCACondition
from services.correlator.trigger import Trigger
from noc.fm.models.activeevent import ActiveEvent
from noc.fm.models.eventclass import EventClass
from noc.fm.models.activealarm import ActiveAlarm
from noc.fm.models.alarmlog import AlarmLog
from noc.fm.models.alarmclass import AlarmClass
from noc.fm.models.alarmtrigger import AlarmTrigger
from noc.fm.models.archivedalarm import ArchivedAlarm
from noc.fm.models.alarmescalation import AlarmEscalation
from noc.fm.models.alarmdiagnosticconfig import AlarmDiagnosticConfig
from noc.sa.models.servicesummary import ServiceSummary, SummaryItem, ObjectSummaryItem
from noc.core.version import version
from noc.core.debug import format_frames, get_traceback_frames, error_report
from services.correlator import utils
from noc.core.perf import metrics
from noc.core.fm.enum import RCA_RULE, RCA_TOPOLOGY, RCA_DOWNLINK_MERGE
from noc.core.liftbridge.message import Message
from noc.services.correlator.rcalock import RCALock

ALARM_REPEAT = "NOC | Alarm | Repeat Threshold"


class CorrelatorService(TornadoService):
    name = "correlator"
    pooled = True
    use_mongo = True
    process_name = "noc-%(name).10s-%(pool).5s"

    def __init__(self):
        super().__init__()
        self.version = version.version
        self.rules = {}  # event_class -> [Rule]
        self.back_rules = {}  # event_class -> [Rule]
        self.triggers = {}  # alarm_class -> [Trigger1, .. , TriggerN]
        self.rca_forward = {}  # alarm_class -> [RCA condition, ..., RCA condititon]
        self.rca_reverse = defaultdict(set)  # alarm_class -> set([alarm_class])
        #
        self.slot_number = 0
        self.total_slots = 0
        self.is_distributed = False
        self.repeat: Dict[str, List[int]] = {}
        # Scheduler
        self.scheduler: Optional[Scheduler] = None
        # Locks
        self.topo_rca_lock: Optional[RCALock] = None

    async def on_activate(self):
        self.slot_number, self.total_slots = await self.acquire_slot()
        self.is_distributed = self.total_slots > 1
        # Prepare scheduler
        if self.is_distributed:
            self.logger.info(
                "Enabling distributed mode: Slot %d/%d", self.slot_number, self.total_slots
            )
            ifilter = {"shard": {"$mod": [self.total_slots, self.slot_number]}}
        else:
            self.logger.info("Enabling standalone mode")
            ifilter = None
        self.scheduler = Scheduler(
            self.name,
            pool=config.pool,
            reset_running=True,
            max_threads=config.correlator.max_threads,
            # @fixme have to be configured ?
            submit_threshold=100,
            max_chunk=100,
            filter=ifilter,
        )
        self.scheduler.correlator = self
        self.scheduler.run()
        # Subscribe stream, move to separate task to let the on_activate to terminate
        self.loop.create_task(
            self.subscribe_stream(
                "dispose.%s" % config.pool, self.slot_number, self.on_dispose_event
            )
        )

    def on_start(self):
        """
        Load rules from database just after loading config
        """
        super().on_start()
        connect()  # use_mongo connect do after on_start.
        self.load_rules()
        self.load_triggers()
        self.load_rca_rules()

    def load_rules(self):
        """
        Load rules from database
        """
        self.logger.debug("Loading rules")
        self.rules = {}
        self.back_rules = {}
        nr = 0
        nbr = 0
        for c in EventClass.objects.all():
            if c.disposition:
                r = []
                for dr in c.disposition:
                    rule = Rule(c, dr)
                    r += [rule]
                    nr += 1
                    if dr.combo_condition != "none" and dr.combo_window:
                        for cc in dr.combo_event_classes:
                            try:
                                self.back_rules[cc.id] += [dr]
                            except KeyError:
                                self.back_rules[cc.id] = [dr]
                            nbr += 1
                self.rules[c.id] = r
        self.logger.debug("%d rules are loaded. %d combos" % (nr, nbr))

    def load_triggers(self):
        self.logger.info("Loading triggers")
        self.triggers = {}
        n = 0
        cn = 0
        ec = [(c.name, c.id) for c in AlarmClass.objects.all()]
        for t in AlarmTrigger.objects.filter(is_enabled=True):
            self.logger.debug("Trigger '%s' for classes:" % t.name)
            for c_name, c_id in ec:
                if re.search(t.alarm_class_re, c_name, re.IGNORECASE):
                    try:
                        self.triggers[c_id] += [Trigger(t)]
                    except KeyError:
                        self.triggers[c_id] = [Trigger(t)]
                    cn += 1
                    self.logger.debug("    %s" % c_name)
            n += 1
        self.logger.info("%d triggers has been loaded to %d classes" % (n, cn))

    def load_rca_rules(self):
        """
        Load root cause analisys rules
        """
        self.logger.info("Loading RCA Rules")
        n = 0
        self.rca_forward = {}
        self.rca_reverse = {}
        for a in AlarmClass.objects.filter(root_cause__0__exists=True):
            if not a.root_cause:
                continue
            self.rca_forward[a.id] = []
            for c in a.root_cause:
                rc = RCACondition(a, c)
                self.rca_forward[a.id] += [rc]
                if rc.root.id not in self.rca_reverse:
                    self.rca_reverse[rc.root.id] = []
                self.rca_reverse[rc.root.id] += [rc]
                n += 1
        self.logger.info("%d RCA Rules have been loaded" % n)

    def mark_as_failed(self, event):
        """
        Write error log and mark event as failed
        """
        self.logger.error("Failed to process event %s" % str(event.id))
        # Prepare traceback
        t, v, tb = sys.exc_info()
        now = datetime.datetime.now()
        r = ["UNHANDLED EXCEPTION (%s)" % str(now)]
        r += [str(t), str(v)]
        r += [format_frames(get_traceback_frames(tb))]
        r = "\n".join(r)
        event.mark_as_failed(version=self.version, traceback=r)

    def set_root_cause(self, a):
        """
        Search for root cause and set, if found
        :returns: Boolean. True, if root cause set
        """
        for rc in self.rca_forward[a.alarm_class.id]:
            # Check condition
            if not rc.check_condition(a):
                continue
            # Check match condition
            q = rc.get_match_condition(a)
            root = ActiveAlarm.objects.filter(**q).first()
            if root:
                # Root cause found
                self.logger.info("%s is root cause for %s (Rule: %s)", root.id, a.id, rc.name)
                metrics["alarm_correlated_rule"] += 1
                a.set_root(root, rca_type=RCA_RULE)
                return True
        return False

    def set_reverse_root_cause(self, a):
        """
        Set *a* as root cause for existing events
        :param a:
        :return:
        """
        found = False
        for rc in self.rca_reverse[a.alarm_class.id]:
            # Check reverse match condition
            q = rc.get_reverse_match_condition(a)
            for ca in ActiveAlarm.objects.filter(**q):
                # Check condition
                if not rc.check_condition(ca):
                    continue
                # Try to set root cause
                qq = rc.get_match_condition(ca, id=a.id)
                rr = ActiveAlarm.objects.filter(**qq).first()
                if rr:
                    # Reverse root cause found
                    self.logger.info(
                        "%s is root cause for %s (Reverse rule: %s)", a.id, ca.id, rc.name
                    )
                    metrics["alarm_correlated_rule"] += 1
                    ca.set_root(a, rca_type=RCA_RULE)
                    found = True
        return found

    async def check_repeat(self, rule: Rule, alarm: ActiveAlarm, event: ActiveEvent):
        """
        Check thresholds
        :param discriminator: Unique
        :param alarm: ActiveAlarm
        :param event: ActiveEvent
        """
        intervals = (
            ("weeks", 604800),  # 60 * 60 * 24 * 7
            ("days", 86400),  # 60 * 60 * 24
            ("hours", 3600),  # 60 * 60
            ("minutes", 60),
            ("seconds", 1),
        )

        def display_time(seconds, granularity=2):
            result = []

            for name, count in intervals:
                value = seconds // count
                if value:
                    seconds -= value * count
                    if value == 1:
                        name = name.rstrip("s")
                    result.append("{} {}".format(value, name))
            return ", ".join(result[:granularity])

        # Build window state key
        managed_object = self.eval_expression(rule.managed_object, event=event)
        discriminator, vars = rule.get_vars(event)
        alarm_class = AlarmClass.get_by_name(ALARM_REPEAT)
        key = "%s|%s" % (alarm.alarm_class.id, discriminator)
        ts = int(alarm.timestamp.timestamp())
        ets = int(event.timestamp.timestamp())
        acrw = alarm.alarm_class.repeat_window
        acrt = alarm.alarm_class.repeat_threshold
        window = self.repeat.get(key, [])

        if ets - ts > acrw:
            ts = ets
        window.append(ts)
        # Trim window according to policy
        window_full = ts - window[0] >= acrw >= ts - window[-1:][0]
        while ts - window[0] > acrw:
            window.pop(0)
        self.repeat[key] = window
        if not window_full:
            self.logger.debug(
                "Cannot calculate thresholds for %s: Window is not filled", alarm.alarm_class
            )
            return
        if len(window) >= acrt:
            a = ActiveAlarm.objects.filter(
                managed_object=managed_object.id, discriminator=key
            ).first()
            if not a:
                vars.update(
                    {
                        "alarm_class_name": alarm.alarm_class.name,
                        "repeat_window": display_time(alarm.alarm_class.repeat_window),
                        "repeat_threshold": alarm.alarm_class.repeat_threshold,
                    }
                )
                a = ActiveAlarm(
                    timestamp=datetime.datetime.now(),
                    last_update=datetime.datetime.now(),
                    managed_object=managed_object.id,
                    alarm_class=alarm_class,
                    severity=alarm_class.default_severity.severity,
                    vars=vars,
                    discriminator=key,
                    log=[
                        AlarmLog(
                            timestamp=datetime.datetime.now(),
                            from_status="A",
                            to_status="A",
                            message="Alarm risen from alarm %s (%s)"
                            % (str(alarm.id), str(alarm.alarm_class.name)),
                        )
                    ],
                )
                a.save()
                self.logger.info(
                    "[%s|%s|%s] %s raises alarm %s(%s): %r",
                    a.id,
                    managed_object.name,
                    managed_object.address,
                    a.alarm_class.name,
                    a.vars,
                )
                metrics["alarm_raise"] += 1
                # Gather diagnostics when necessary
                AlarmDiagnosticConfig.on_raise(a)
                # Watch for escalations, when necessary
                if config.correlator.auto_escalation and not a.root:
                    AlarmEscalation.watch_escalations(a)
            if a:
                if datetime.datetime.now() > a.last_update:
                    # Refresh last update
                    a.last_update = datetime.datetime.now()
                    a.save()

    async def raise_alarm(self, r, e):
        managed_object = self.eval_expression(r.managed_object, event=e)
        if not managed_object:
            self.logger.info("Empty managed object, ignoring")
            return
        # @todo: Make configurable
        if not managed_object.is_managed:
            self.logger.info("Managed object is not managed. Do not raise alarm")
            return
        if e.managed_object.id != managed_object.id:
            metrics["alarm_change_mo"] += 1
            self.logger.info("Changing managed object to %s", managed_object.name)
        discriminator, vars = r.get_vars(e)
        if r.unique:
            assert discriminator is not None
            a = ActiveAlarm.objects.filter(
                managed_object=managed_object.id, discriminator=discriminator
            ).first()
            if not a:
                # Try to reopen alarm
                a = ArchivedAlarm.objects.filter(
                    managed_object=managed_object.id,
                    discriminator=discriminator,
                    control_time__gte=e.timestamp,
                ).first()
                if a:
                    # Reopen alarm
                    self.logger.info(
                        "[%s|%s|%s] %s reopens alarm %s(%s)",
                        e.id,
                        managed_object.name,
                        managed_object.address,
                        e.event_class.name,
                        a.alarm_class.name,
                        a.id,
                    )
                    a = a.reopen("Reopened by disposition rule '%s'" % r.u_name)
                    if r.alarm_class.repeat_window and r.alarm_class.repeat_threshold:
                        await self.check_repeat(r, a, e)
                    metrics["alarm_reopen"] += 1
            if a:
                # Active alarm found, refresh
                self.logger.info(
                    "[%s|%s|%s] Contributing event %s to active alarm %s(%s)",
                    e.id,
                    managed_object.name,
                    managed_object.address,
                    e.event_class.name,
                    a.alarm_class.name,
                    a.id,
                )
                # Contribute event to alarm
                e.contribute_to_alarm(a)
                if e.timestamp < a.timestamp:
                    # Set to earlier date
                    a.timestamp = e.timestamp
                    a.save()
                    if r.alarm_class.repeat_window and r.alarm_class.repeat_threshold:
                        await self.check_repeat(r, a, e)
                elif e.timestamp > a.last_update:
                    # Refresh last update
                    a.last_update = e.timestamp
                    a.save()
                    if r.alarm_class.repeat_window and r.alarm_class.repeat_threshold:
                        await self.check_repeat(r, a, e)
                metrics["alarm_contribute"] += 1
                return
        # Calculate alarm coverage
        summary = ServiceSummary.get_object_summary(managed_object)
        summary["object"] = {managed_object.object_profile.id: 1}
        #
        severity = max(ServiceSummary.get_severity(summary), 1)
        self.logger.info(
            "[%s|%s|%s] %s: Calculated alarm severity is: %s",
            e.id,
            managed_object.name,
            managed_object.address,
            r.u_name,
            severity,
        )
        # Create new alarm
        direct_services = SummaryItem.dict_to_items(summary["service"])
        direct_subscribers = SummaryItem.dict_to_items(summary["subscriber"])
        a = ActiveAlarm(
            timestamp=e.timestamp,
            last_update=e.timestamp,
            managed_object=managed_object.id,
            alarm_class=r.alarm_class,
            severity=severity,
            vars=vars,
            discriminator=discriminator,
            direct_services=direct_services,
            direct_subscribers=direct_subscribers,
            total_objects=ObjectSummaryItem.dict_to_items(summary["object"]),
            total_services=direct_services,
            total_subscribers=direct_subscribers,
            log=[
                AlarmLog(
                    timestamp=datetime.datetime.now(),
                    from_status="A",
                    to_status="A",
                    message="Alarm risen from event %s(%s) by rule '%s'"
                    % (str(e.id), str(e.event_class.name), r.u_name),
                )
            ],
            opening_event=e.id,
        )
        a.save()
        if r.alarm_class.repeat_window and r.alarm_class.repeat_threshold:
            await self.check_repeat(r, a, e)
        e.contribute_to_alarm(a)
        self.logger.info(
            "[%s|%s|%s] %s raises alarm %s(%s): %r",
            e.id,
            managed_object.name,
            managed_object.address,
            e.event_class.name,
            a.alarm_class.name,
            a.id,
            a.vars,
        )
        metrics["alarm_raise"] += 1
        await self.correlate(r, a)
        # Notify about new alarm
        if not a.root:
            a.managed_object.event(
                a.managed_object.EV_ALARM_RISEN,
                {
                    "alarm": a,
                    "subject": a.subject,
                    "body": a.body,
                    "symptoms": a.alarm_class.symptoms,
                    "recommended_actions": a.alarm_class.recommended_actions,
                    "probable_causes": a.alarm_class.probable_causes,
                },
                delay=a.alarm_class.get_notification_delay(),
            )
        # Gather diagnostics when necessary
        AlarmDiagnosticConfig.on_raise(a)
        # Watch for escalations, when necessary
        if config.correlator.auto_escalation and not a.root:
            AlarmEscalation.watch_escalations(a)

    async def correlate(self, r, a):
        # Topology RCA
        if a.alarm_class.topology_rca:
            await self.topology_rca(a)
        # Rule-based RCA
        if a.alarm_class.id in self.rca_forward:
            # Check alarm is a consequence of existing one
            self.set_root_cause(a)
        if a.alarm_class.id in self.rca_reverse:
            # Check alarm is the root cause for existing ones
            self.set_reverse_root_cause(a)
        # Call handlers
        for h in a.alarm_class.get_handlers():
            try:
                has_root = bool(a.root)
                h(a)
                if not has_root and a.root:
                    self.logger.info(
                        "[%s|%s|%s] Set root to %s (handler %s)",
                        a.id,
                        a.managed_object.name,
                        a.managed_object.address,
                        a.root,
                        h,
                    )
            except Exception:  # noqa. Can probable happens anything from handler
                error_report()
                metrics["error", ("type", "alarm_handler")] += 1
        # Call triggers if necessary
        if r.alarm_class.id in self.triggers:
            for t in self.triggers[r.alarm_class.id]:
                try:
                    t.call(a)
                except:  # noqa. Can probable happens anything from trigger
                    error_report()
        #
        if not a.severity:
            # Alarm severity has been reset to 0 by handlers
            # Silently drop alarm
            self.logger.debug("Alarm severity is 0, dropping")
            a.delete()
            metrics["alarm_drop"] += 1
            return

    def clear_alarm(self, r, e):
        managed_object = self.eval_expression(r.managed_object, event=e)
        if not managed_object:
            self.logger.info(
                "[%s|Unknown|Unknown] Referred to unknown managed object, ignoring", e.id
            )
            metrics["unknown_object"] += 1
            return
        if r.unique:
            discriminator, vars = r.get_vars(e)
            assert discriminator is not None
            a = ActiveAlarm.objects.filter(
                managed_object=managed_object.id, discriminator=discriminator
            ).first()
            if a:
                self.logger.info(
                    "[%s|%s|%s] %s clears alarm %s(%s)",
                    e.id,
                    managed_object.name,
                    managed_object.address,
                    e.event_class.name,
                    a.alarm_class.name,
                    a.id,
                )
                e.contribute_to_alarm(a)
                a.closing_event = e.id
                a.last_update = max(a.last_update, e.timestamp)
                a.clear_alarm("Cleared by disposition rule '%s'" % r.u_name, ts=e.timestamp)
                metrics["alarm_clear"] += 1

    def get_delayed_event(self, r, e):
        """
        Check wrether all delayed conditions are met

        :param r: Delayed rule
        :param e: Event which can trigger delayed rule
        """
        # @todo: Rewrite to scheduler
        discriminator, vars = r.get_vars(e)
        ws = e.timestamp - datetime.timedelta(seconds=r.combo_window)
        de = ActiveEvent.objects.filter(
            managed_object=e.managed_object_id,
            event_class=r.event_class,
            discriminator=discriminator,
            timestamp__gte=ws,
        ).first()
        if not de:
            # No starting event
            return None
        # Probable starting event found, get all interesting following event
        # classes
        fe = [
            ee.event_class.id
            for ee in ActiveEvent.objects.filter(
                managed_object=e.managed_object_id,
                event_class__in=r.combo_event_classes,
                discriminator=discriminator,
                timestamp__gte=ws,
            ).order_by("timestamp")
        ]
        if r.combo_condition == "sequence":
            # Exact match
            if fe == self.combo_event_classes:
                return de
        elif r.combo_condition == "all":
            # All present
            if not any([c for c in r.combo_event_classes if c not in fe]):
                return de
        elif r.combo_condition == "any":
            # Any found
            if fe:
                return de
        return None

    def eval_expression(self, expression, **kwargs):
        """
        Evaluate expression in given context
        """
        env = {"re": re, "utils": utils}
        env.update(kwargs)
        return eval(expression, {}, env)

    async def on_dispose_event(self, msg: Message) -> None:
        """
        Called on new dispose message
        """
        data = orjson.loads(msg.value)
        event_id = data["event_id"]
        hint = data["event"]
        self.logger.info("[%s] Receiving message", event_id)
        metrics["alarm_dispose"] += 1
        try:
            event = ActiveEvent.from_json(hint)
            event.timestamp = event.timestamp.replace(tzinfo=None)
            await self.dispose_event(event)
        except Exception:
            metrics["alarm_dispose_error"] += 1
            error_report()
        finally:
            if self.topo_rca_lock:
                # Release pending RCA Lock
                await self.topo_rca_lock.release()
                self.topo_rca_lock = None

    async def dispose_event(self, e):
        """
        Dispose event according to disposition rule
        """
        event_id = str(e.id)
        self.logger.info("[%s] Disposing", event_id)
        drc = self.rules.get(e.event_class.id)
        if not drc:
            self.logger.info(
                "[%s] No disposition rules for class %s, skipping", event_id, e.event_class.name
            )
            return
        # Apply disposition rules
        for r in drc:
            if self.eval_expression(r.condition, event=e):
                # Process action
                if r.action == "drop":
                    self.logger.info("[%s] Dropped by action", event_id)
                    e.delete()
                    return
                elif r.action == "ignore":
                    self.logger.info("[%s] Ignored by action", event_id)
                    return
                elif r.action == "raise" and r.combo_condition == "none":
                    await self.raise_alarm(r, e)
                elif r.action == "clear" and r.combo_condition == "none":
                    self.clear_alarm(r, e)
                if r.action in ("raise", "clear"):
                    # Write discriminator if can trigger delayed event
                    if r.unique and r.event_class.id in self.back_rules:
                        discriminator, vars = r.get_vars(e)
                        e.discriminator = discriminator
                        e.save()
                    # Process delayed combo conditions
                    if e.event_class.id in self.back_rules:
                        for br in self.back_rules[e.event_class.id]:
                            de = self.get_delayed_event(br, e)
                            if de:
                                if br.action == "raise":
                                    await self.raise_alarm(br, de)
                                elif br.action == "clear":
                                    self.clear_alarm(br, de)
                if r.stop_disposition:
                    break
        self.logger.info("[%s] Disposition complete", event_id)

    async def topology_rca(self, alarm):
        """
        Topology-based RCA
        :param alarm:
        :return:
        """

        def can_correlate(a1, a2):
            """
            Check if alarms can be correlated together (within corellation window)
            :param a1:
            :param a2:
            :return:
            """
            return (
                not config.correlator.topology_rca_window
                or (a1.timestamp - a2.timestamp).total_seconds()
                <= config.correlator.topology_rca_window
            )

        def all_uplinks_failed(a1):
            """
            Check if all uplinks for alarm is failed
            :param a1:
            :return:
            """
            if not a1.uplinks:
                return False
            return sum(1 for mo in a1.uplinks if mo in neighbor_alarms) == len(a1.uplinks)

        def get_root(a1) -> Optional[ActiveAlarm]:
            """
            Get root cause for failed uplinks.
            Considering all uplinks are failed.
            Uplinks are ordered according to path length.
            Return first applicable

            :param a1:
            :return:
            """
            for u in a1.uplinks:
                na = neighbor_alarms[u]
                if can_correlate(a1, na):
                    return na
            return None

        def get_neighboring_alarms(ca: ActiveAlarm) -> Dict[int, ActiveAlarm]:
            r = {
                na.managed_object.id: na
                for na in ActiveAlarm.objects.filter(
                    alarm_class=ca.alarm_class.id, rca_neighbors__in=[ca.managed_object.id]
                )
            }
            # Add current alarm to correlate downlink alarms properly
            r[alarm.managed_object.id] = ca
            return r

        def iter_downlink_alarms(a1):
            """
            Yield all downlink alarms
            :param a1:
            :return:
            """
            mo = a1.managed_object.id
            for na in neighbor_alarms.values():
                if na.uplinks and mo in na.uplinks:
                    yield na

        def correlate_uplinks(ca: ActiveAlarm) -> bool:
            """
            Correlate with uplink alarms if all uplinks are faulty.
            :param a1:
            :return:
            """
            if not all_uplinks_failed(ca):
                return False
            self.logger.info("[%s] All uplinks are faulty. Correlating", ca.id)
            ra = get_root(ca)
            if not ra:
                return False
            self.logger.info("[%s] Set root to %s", ca.id, ra.id)
            ca.set_root(ra, rca_type=RCA_TOPOLOGY)
            metrics["alarm_correlated_topology"] += 1
            return True

        def correlate_merge_downlinks(ca: ActiveAlarm) -> bool:
            """
            Donwlink merge correlation
            :param ca:
            :return:
            """
            if not ca.uplinks or not ca.rca_neighbors:
                return False
            dlm_neighbors = {mo: w for mo, w in zip(ca.rca_neighbors, ca.dlm_windows) if w > 0}
            dlm_candidates = set(neighbor_alarms) & set(dlm_neighbors)
            if not dlm_candidates:
                return False
            # Get possible candidates
            t0 = ca.timestamp
            candidates = list(
                sorted(
                    (
                        neighbor_alarms[mo]
                        for mo in dlm_candidates
                        if (t0 - neighbor_alarms[mo].timestamp).total_seconds() <= dlm_neighbors[mo]
                    ),
                    key=operator.attrgetter("timestamp"),
                )
            )
            if not candidates:
                return False
            ra = candidates[0]
            self.logger.info("[%s] Set root to %s (downlink merge)", ca.id, ra.id)
            ca.set_root(ra, rca_type=RCA_DOWNLINK_MERGE)
            metrics["alarm_correlated_topology"] += 1
            return True

        self.logger.debug("[%s] Topology RCA", alarm.id)
        # Acquire lock
        if self.is_distributed:
            # Set lock until the end of dispose
            mo = alarm.managed_object
            self.topo_rca_lock = RCALock(mo.data.rca_neighbors + [mo.id])
            await self.topo_rca_lock.acquire()
        # Get neighboring alarms
        neighbor_alarms = get_neighboring_alarms(alarm)
        # Correlate current alarm
        correlate_uplinks(alarm) or correlate_merge_downlinks(alarm)
        # Correlate all downlink alarms
        for a in iter_downlink_alarms(alarm):
            correlate_uplinks(a)
        self.logger.debug("[%s] Correlation completed", alarm.id)


if __name__ == "__main__":
    CorrelatorService().start()
