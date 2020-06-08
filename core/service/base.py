# ----------------------------------------------------------------------
# Base service
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import os
import sys
import logging
import signal
import uuid
import argparse
from collections import defaultdict
import time
import threading
from time import perf_counter
import datetime
import asyncio
from typing import Optional, Dict, List, Tuple, Callable, Any, TypeVar, NoReturn

# Third-party modules
import tornado.web
import tornado.netutil
import tornado.httpserver
import setproctitle
import ujson

# NOC modules
from noc.config import config, CH_UNCLUSTERED, CH_REPLICATED, CH_SHARDED
from noc.core.debug import excepthook, error_report, ErrorReport
from noc.core.log import ErrorFormatter
from noc.core.perf import metrics, apply_metrics
from noc.core.hist.monitor import apply_hists
from noc.core.quantile.monitor import apply_quantiles
from noc.core.dcs.loader import get_dcs, DEFAULT_DCS
from noc.core.threadpool import ThreadPoolExecutor
from noc.core.nsq.reader import Reader as NSQReader
from noc.core.span import get_spans, span_to_dict
from noc.core.tz import setup_timezone
from noc.core.nsq.topic import TopicQueue
from noc.core.nsq.pub import mpub
from noc.core.nsq.error import NSQPubError
from noc.core.clickhouse.shard import ShardingFunction
from noc.core.ioloop.util import setup_asyncio
from noc.core.ioloop.timers import PeriodicCallback
from .api import API, APIRequestHandler
from .doc import DocRequestHandler
from .mon import MonRequestHandler
from .metrics import MetricsHandler
from .health import HealthRequestHandler
from .sdl import SDLRequestHandler
from .rpc import RPCProxy
from .ctl import CtlAPI
from .loader import set_service

T = TypeVar("T")


class Service(object):
    """
    Basic service implementation.

    * on_change_<var> - subscribed to changes of config variable <var>
    """

    # Service name
    name = None
    # Leader lock name
    # Only one active instace per leader lock can be active
    # at given moment
    # Config variables can be expanded as %(varname)s
    leader_lock_name = None

    # Leader group name
    # Only one service in leader group can be running at a time
    # Config variables can be expanded as %(varname)s
    # @todo: Deprecated, must be removed
    leader_group_name = None
    # Pooled service are used to distribute load between services.
    # Pool name set in NOC_POOL parameter or --pool option.
    # May be used in conjunction with leader_group_name
    # to allow only one instance of services per node or datacenter
    pooled = False

    # Format string to set process name
    # config variables can be expanded as %(name)s
    process_name = "noc-%(name).10s"
    # Connect to MongoDB on activate
    use_mongo = False
    # List of API instances
    api: List[API] = []
    # Request handler class
    api_request_handler = APIRequestHandler
    # Initialize gettext and process *language* configuration
    use_translation = False
    # Initialize jinja2 templating engine
    use_jinja = False
    # Collect and send spans
    use_telemetry = False
    # Register traefik backend if not None
    traefik_backend = None
    # Traefik frontend rule
    # i.e. PathPrefix:/api/<name>
    traefik_frontend_rule = None
    # Require DCS health status to be considered healthy
    # Usually means resolution error to required services
    # temporary leads service to unhealthy state
    require_dcs_health = True

    LOG_FORMAT = config.log_format

    LOG_LEVELS = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    DEFAULT_SHARDING_KEY = "managed_object"

    SHARDING_KEYS = {"span": "ctx"}

    # Timeout to wait NSQ writer is to close
    NSQ_WRITER_CLOSE_TRY_TIMEOUT = 0.25
    # Times to try to close NSQ writer
    NSQ_WRITER_CLOSE_RETRIES = 5

    class RegistrationError(Exception):
        pass

    def __init__(self):
        set_service(self)
        sys.excepthook = excepthook
        self.loop: Optional[asyncio.BaseEventLoop] = None
        self.logger = None
        self.service_id = str(uuid.uuid4())
        self.executors = {}
        self.start_time = perf_counter()
        self.pid = os.getpid()
        self.nsq_readers = {}  # handler -> Reader
        self.nsq_writer = None
        self.startup_ts = None
        self.telemetry_callback = None
        self.dcs = None
        # Effective address and port
        self.server = None
        self.address = None
        self.port = None
        self.is_active = False
        self.close_callbacks = []
        # Can be initialized in subclasses
        self.scheduler = None
        # Depends on config
        topo = config.get_ch_topology_type()
        if topo == CH_UNCLUSTERED:
            self.register_metrics = self._register_unclustered_metrics
        elif topo == CH_REPLICATED:
            self.register_metrics = self._register_replicated_metrics
        elif topo == CH_SHARDED:
            self.register_metrics = self._register_sharded_metrics
            self.get_shards = ShardingFunction()
        else:
            self.die("Invalid ClickHouse cluster topology")
        # NSQ Topics
        # name -> TopicQueue()
        self.topic_queues: Dict[str, TopicQueue] = {}
        self.topic_queue_lock = threading.Lock()

    def create_parser(self) -> argparse.ArgumentParser:
        """
        Return argument parser
        """
        return argparse.ArgumentParser()

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Apply additional parser arguments
        """
        parser.add_argument(
            "--node", action="store", dest="node", default=config.node, help="NOC node name"
        )
        parser.add_argument(
            "--loglevel",
            action="store",
            choices=list(self.LOG_LEVELS),
            dest="loglevel",
            default=config.loglevel,
            help="Logging level",
        )
        parser.add_argument(
            "--instance",
            action="store",
            dest="instance",
            type=int,
            default=config.instance,
            help="Instance number",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            dest="debug",
            default=False,
            help="Dump additional debugging info",
        )
        parser.add_argument(
            "--dcs",
            action="store",
            dest="dcs",
            default=DEFAULT_DCS,
            help="Distributed Coordinated Storage URL",
        )
        if self.pooled:
            parser.add_argument(
                "--pool", action="store", dest="pool", default=config.pool, help="NOC pool name"
            )

    @classmethod
    def die(cls, msg: str = "") -> NoReturn:
        """
        Dump message to stdout and terminate process with error code
        """
        sys.stdout.write(str(msg) + "\n")
        sys.stdout.flush()
        os._exit(1)

    def setup_logging(self, loglevel=None):
        """
        Create new or setup existing logger
        """
        # @todo: Duplicates config.setup_logging
        if not loglevel:
            loglevel = config.loglevel
        logger = logging.getLogger()
        if len(logger.handlers):
            # Logger is already initialized
            fmt = ErrorFormatter(self.LOG_FORMAT, None)
            for h in logging.root.handlers:
                if isinstance(h, logging.StreamHandler):
                    h.stream = sys.stdout
                h.setFormatter(fmt)
            logging.root.setLevel(loglevel)
        else:
            # Initialize logger
            logging.basicConfig(stream=sys.stdout, format=self.LOG_FORMAT, level=loglevel)
        self.logger = logging.getLogger(self.name)
        logging.captureWarnings(True)

    def setup_test_logging(self):
        self.logger = logging.getLogger(self.name)

    def setup_translation(self):
        from noc.core.translation import set_translation, ugettext

        set_translation(self.name, config.language)
        if self.use_jinja:
            from jinja2.defaults import DEFAULT_NAMESPACE

            if "_" not in DEFAULT_NAMESPACE:
                DEFAULT_NAMESPACE["_"] = ugettext

    def on_change_loglevel(self, old_value, new_value):
        if new_value not in self.LOG_LEVELS:
            self.logger.error("Invalid loglevel '%s'. Ignoring", new_value)
            return
        self.logger.warning("Changing loglevel to %s", new_value)
        logging.getLogger().setLevel(self.LOG_LEVELS[new_value])

    def log_separator(self, symbol="*", length=72):
        """
        Log a separator string to visually split log
        """
        self.logger.warning(symbol * length)
        if config.features.forensic:
            self.logger.warning("[noc.core.forensic] [=Process restarted]")

    def setup_signal_handlers(self):
        """
        Set up signal handlers
        """
        signal.signal(signal.SIGTERM, self.on_SIGTERM)
        signal.signal(signal.SIGHUP, self.on_SIGHUP)

    def set_proc_title(self):
        """
        Set process title
        """
        v = {"name": self.name, "instance": config.instance or "", "pool": config.pool or ""}
        title = self.process_name % v
        self.logger.debug("Setting process title to: %s", title)
        setproctitle.setproctitle(title)

    def start(self):
        """
        Run main server loop
        """
        self.startup_ts = time.time()
        parser = self.create_parser()
        self.add_arguments(parser)
        options = parser.parse_args(sys.argv[1:])
        cmd_options = vars(options)
        args = cmd_options.pop("args", ())
        # Bootstrap logging with --loglevel
        self.setup_logging(cmd_options["loglevel"])
        self.log_separator()
        # Setup timezone
        try:
            self.logger.info("Setting timezone to %s", config.timezone)
            setup_timezone()
        except ValueError as e:
            self.die(str(e))
        # Setup title
        self.set_proc_title()
        # Setup signal handlers
        self.setup_signal_handlers()
        self.on_start()
        # Starting IOLoop
        self.is_active = True
        if self.pooled:
            self.logger.warning("Running service %s (pool: %s)", self.name, config.pool)
        else:
            self.logger.warning("Running service %s", self.name)
        try:
            setup_asyncio()
            self.loop = asyncio.get_event_loop()
            # Initialize DCS
            self.dcs = get_dcs(cmd_options["dcs"])
            # Activate service
            self.loop.create_task(self.activate())
            self.logger.warning("Starting IOLoop")
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.logger.warning("Interrupted by Ctrl+C")
        except self.RegistrationError:
            self.logger.info("Registration failed")
        except Exception:
            error_report()
        finally:
            if self.loop:
                self.loop.create_task(self.deactivate())
        for cb, args, kwargs in self.close_callbacks:
            cb(*args, **kwargs)
        self.logger.warning("Service %s has been terminated", self.name)

    def get_event_loop(self) -> asyncio.BaseEventLoop:
        return self.loop

    def on_start(self):
        """
        Reload config
        """
        if self.use_translation:
            self.setup_translation()

    def stop(self):
        self.logger.warning("Stopping")
        self.loop.create_task(self.deactivate())

    def on_SIGHUP(self, signo, frame):
        # self.logger.warning("SIGHUP caught, rereading config")
        pass

    def on_SIGTERM(self, signo, frame):
        self.logger.warning("SIGTERM caught, Stopping")
        self.stop()

    def get_service_address(self) -> Tuple[str, int]:
        """
        Returns an (address, port) for HTTP service listener
        """
        if self.address and self.port:
            return self.address, self.port
        if config.listen:
            addr, port = config.listen.split(":")
            port_tracker = config.instance
        else:
            addr, port = "auto", 0
            port_tracker = 0
        if addr == "auto":
            addr = config.node
            self.logger.info("Autodetecting address: auto -> %s", addr)
        addr = config.node
        port = int(port) + port_tracker
        return addr, port

    def update_service_address(self):
        """
        Update service address and port from tornado TCPServer
        :param server:
        :return:
        """
        for f in self.server._sockets:
            sock = self.server._sockets[f]
            self.address, self.port = sock.getsockname()
            break

    def get_handlers(self):
        """
        Returns a list of additional handlers
        """
        return []

    def get_app_settings(self):
        """
        Returns tornado application settings
        """
        return {
            "template_path": os.getcwd(),
            "cookie_secret": config.secret_key,
            "log_function": self.log_request,
        }

    async def activate(self):
        """
        Initialize services before run
        """
        self.logger.warning("Activating service")
        if self.use_mongo:
            from noc.core.mongo.connection import connect

            connect()
        handlers = [
            (r"^/mon/$", MonRequestHandler, {"service": self}),
            (r"^/metrics$", MetricsHandler, {"service": self}),
            (r"^/health/$", HealthRequestHandler, {"service": self}),
        ]
        api = [CtlAPI]
        if self.api:
            api += self.api
        addr, port = self.get_service_address()
        sdl = {}  # api -> [methods]
        # Collect and register exposed API
        for a in api:
            url = "^/api/%s/$" % a.name
            handlers += [(url, self.api_request_handler, {"service": self, "api_class": a})]
            # Populate sdl
            sdl[a.name] = a.get_methods()
        if self.api:
            handlers += [
                ("^/api/%s/doc/$" % self.name, DocRequestHandler, {"service": self}),
                ("^/api/%s/sdl.js" % self.name, SDLRequestHandler, {"sdl": sdl}),
            ]
        handlers += self.get_handlers()
        app = tornado.web.Application(handlers, **self.get_app_settings())
        self.server = tornado.httpserver.HTTPServer(app, xheaders=True, no_keep_alive=True)
        self.server.listen(port, addr)
        # Get effective address and port
        self.update_service_address()
        #
        self.logger.info("Running HTTP APIs at http://%s:%s/", self.address, self.port)
        for a in api:
            self.logger.info(
                "Supported API: %s at http://%s:%s/api/%s/", a.name, self.address, self.port, a.name
            )
        #
        if self.use_telemetry:
            self.start_telemetry_callback()
        self.loop.create_task(self.on_register())

    async def deactivate(self):
        if not self.is_active:
            return
        self.is_active = False
        self.logger.info("Deactivating")
        # Shutdown API
        self.logger.info("Stopping API")
        self.server.stop()
        # Release registration
        if self.dcs:
            self.logger.info("Deregistration")
            await self.dcs.deregister()
        # Shutdown schedulers
        if self.scheduler:
            try:
                self.logger.info("Shutting down scheduler")
                await self.scheduler.shutdown()
            except asyncio.TimeoutError:
                self.logger.info("Timed out when shutting down scheduler")
        # Shutdown executors
        await self.shutdown_executors()
        # Custom deactivation
        await self.on_deactivate()
        # Shutdown NSQ topics
        await self.shutdown_topic_queues()
        # Continue deactivation
        # Finally stop ioloop
        self.dcs = None
        self.logger.info("Stopping EventLoop")
        self.loop.stop()
        m = {}
        apply_metrics(m)
        apply_hists(m)
        apply_quantiles(m)
        self.logger.info("Post-mortem metrics: %s", m)
        self.die("")

    def get_register_tags(self):
        tags = ["noc"]
        if config.features.traefik:
            if self.traefik_backend and self.traefik_frontend_rule:
                tags += [
                    "traefik.tags=backend",
                    "traefik.backend=%s" % self.traefik_backend,
                    "traefik.frontend.rule=%s" % self.traefik_frontend_rule,
                    "traefik.backend.load-balancing=wrr",
                ]
                weight = self.get_backend_weight()
                if weight:
                    tags += ["traefik.backend.weight=%s" % weight]
                limit = self.get_backend_limit()
                if limit:
                    tags += ["traefik.backend.maxconn.amount=%s" % limit]
        return tags

    async def on_register(self):
        addr, port = self.get_service_address()
        r = await self.dcs.register(
            self.name,
            addr,
            port,
            pool=config.pool if self.pooled else None,
            lock=self.get_leader_lock_name(),
            tags=self.get_register_tags(),
        )
        if r:
            # Finally call on_activate
            await self.on_activate()
            self.logger.info("Service is active (in %.2fms)", self.uptime() * 1000)
        else:
            raise self.RegistrationError()

    async def on_activate(self):
        """
        Called when service activated
        """
        return

    async def acquire_lock(self):
        await self.dcs.acquire_lock("lock-%s" % self.name)

    async def acquire_slot(self):
        if self.pooled:
            name = "%s-%s" % (self.name, config.pool)
        else:
            name = self.name
        slot_number, total_slots = await self.dcs.acquire_slot(name, config.global_n_instances)
        if total_slots <= 0:
            self.die("Service misconfiguration detected: Invalid total_slots")
        return slot_number, total_slots

    async def on_deactivate(self):
        return

    def open_rpc(self, name, pool=None, sync=False, hints=None):
        """
        Returns RPC proxy object.
        """
        if pool:
            svc = "%s-%s" % (name, pool)
        else:
            svc = name
        return RPCProxy(self, svc, sync=sync, hints=hints)

    def get_mon_status(self):
        return True

    def get_mon_data(self):
        """
        Returns monitoring data
        """
        r = {
            "status": self.get_mon_status(),
            "service": self.name,
            "instance": str(self.service_id),
            "node": config.node,
            "pid": self.pid,
            # Current process uptime
            "uptime": perf_counter() - self.start_time,
        }
        if self.pooled:
            r["pool"] = config.pool
        if self.executors:
            for x in self.executors:
                self.executors[x].apply_metrics(r)
        apply_metrics(r)
        for topic in self.topic_queues:
            self.topic_queues[topic].apply_metrics(r)
        apply_hists(r)
        apply_quantiles(r)
        return r

    def iter_rpc_retry_timeout(self):
        """
        Yield timeout to wait after unsuccessful RPC connection
        """
        for t in config.rpc.retry_timeout.split(","):
            yield float(t)

    async def subscribe(self, topic, channel, handler, raw=False, **kwargs):
        """
        Subscribe message to channel
        """

        def call_json_handler(message):
            metrics[metric_in] += 1
            try:
                data = ujson.loads(message.body)
            except ValueError as e:
                metrics[metric_decode_fail] += 1
                self.logger.debug("Cannot decode JSON message: %s", e)
                return True  # Broken message
            if isinstance(data, dict):
                with ErrorReport():
                    r = handler(message, **data)
            else:
                with ErrorReport():
                    r = handler(message, data)
            if r:
                metrics[metric_processed] += 1
            elif message.is_async():
                message.on("finish", on_finish)
            else:
                metrics[metric_deferred] += 1
            return r

        def call_raw_handler(message):
            metrics[metric_in] += 1
            with ErrorReport():
                r = handler(message, message.body)
            if r:
                metrics[metric_processed] += 1
            elif message.is_async():
                message.on("finish", on_finish)
            else:
                metrics[metric_deferred] += 1
            return r

        def on_finish(*args, **kwargs):
            metrics[metric_processed] += 1

        t = topic.replace(".", "_")
        metric_in = "nsq_msg_in_%s" % t
        metric_decode_fail = "nsq_msg_decode_fail_%s" % t
        metric_processed = "nsq_msg_processed_%s" % t
        metric_deferred = "nsq_msg_deferred_%s" % t
        lookupd = [str(a) for a in config.nsqlookupd.http_addresses]
        self.logger.info("Subscribing to %s/%s (lookupd: %s)", topic, channel, ", ".join(lookupd))
        self.nsq_readers[handler] = NSQReader(
            message_handler=call_raw_handler if raw else call_json_handler,
            topic=topic,
            channel=channel,
            lookupd_http_addresses=lookupd,
            snappy=config.nsqd.compression == "snappy",
            deflate=config.nsqd.compression == "deflate",
            deflate_level=config.nsqd.compression_level
            if config.nsqd.compression == "deflate"
            else 6,
            **kwargs,
        )

    def suspend_subscription(self, handler):
        """
        Suspend subscription for handler
        :param handler:
        :return:
        """
        self.logger.info("Suspending subscription for handler %s", handler)
        self.nsq_readers[handler].set_max_in_flight(0)

    def resume_subscription(self, handler):
        """
        Resume subscription for handler
        :param handler:
        :return:
        """
        self.logger.info("Resuming subscription for handler %s", handler)
        self.nsq_readers[handler].set_max_in_flight(config.nsqd.max_in_flight)

    def get_topic_queue(self, topic: str) -> TopicQueue:
        q = self.topic_queues.get(topic)
        if q:
            return q
        # Create when necessary
        with self.topic_queue_lock:
            q = self.topic_queues.get(topic)
            if q:
                return q  # Created in concurrent task
            q = TopicQueue(topic)
            self.topic_queues[topic] = q
            self.loop.create_task(self.nsq_publisher_guard(q))
            return q

    async def nsq_publisher_guard(self, queue: TopicQueue):
        while not queue.to_shutdown:
            try:
                await self.nsq_publisher(queue)
            except Exception as e:
                self.logger.error("Unhandled exception in NSQ publisher, restarting: %s", e)

    async def nsq_publisher(self, queue: TopicQueue):
        """
        Publisher for NSQ topic

        :return:
        """
        topic = queue.topic
        self.logger.info("[nsq|%s] Starting NSQ publisher", topic)
        while not queue.to_shutdown or not queue.is_empty():
            # Message throttling. Wait and allow to collect more messages
            await queue.wait(timeout=10, rate=config.nsqd.topic_mpub_rate)
            # Get next batch up to `mpub_messages` messages or up to `mpub_size` size
            messages = list(
                queue.iter_get(
                    n=config.nsqd.mpub_messages,
                    size=config.nsqd.mpub_size,
                    total_overhead=4,
                    message_overhead=4,
                )
            )
            if not messages:
                continue
            try:
                self.logger.debug("[nsq|%s] Publishing %d messages", topic, len(messages))
                await mpub(topic, messages, dcs=self.dcs)
            except NSQPubError:
                if queue.to_shutdown:
                    self.logger.debug(
                        "[nsq|%s] Failed to publish during shutdown. Dropping messages", topic
                    )
                else:
                    # Return to queue
                    self.logger.info(
                        "[nsq|%s] Failed to publish. %d messages returned to queue",
                        topic,
                        len(messages),
                    )
                    queue.return_messages(messages)
            del messages  # Release memory
        self.logger.info("[nsq|%s] Stopping NSQ publisher", topic)
        # Queue is shut down and empty, notify
        queue.notify_shutdown()

    async def shutdown_executors(self):
        if self.executors:
            self.logger.info("Shutting down executors")
            for x in self.executors:
                try:
                    self.logger.info("Shutting down %s", x)
                    await self.executors[x].shutdown()
                except asyncio.TimeoutError:
                    self.logger.info("Timed out when shutting down %s", x)

    async def shutdown_topic_queues(self):
        # Issue shutdown
        with self.topic_queue_lock:
            has_topics = bool(self.topic_queues)
            if has_topics:
                self.logger.info("Shutting down topic queues")
            for topic in self.topic_queues:
                self.topic_queues[topic].shutdown()
        # Wait for shutdown
        while has_topics:
            with self.topic_queue_lock:
                topic = next(iter(self.topic_queues.keys()))
                queue = self.topic_queues[topic]
                del self.topic_queues[topic]
                has_topics = bool(self.topic_queues)
            try:
                self.logger.info("Waiting shutdown of topic queue %s", topic)
                await queue.wait_for_shutdown(5.0)
            except asyncio.TimeoutError:
                self.logger.info("Failed to shutdown topic queue %s: Timed out", topic)

    def pub(self, topic, data, raw=False):
        """
        Publish message to topic
        :param topic: Topic name
        :param data: Message to send. Message will be automatically
          converted to JSON if *raw* is False, or passed as-is
          otherwise
        :param raw: True - pass message as-is, False - convert to JSON
        """
        q = self.get_topic_queue(topic)
        if raw:
            q.put(data)
        else:
            for chunk in q.iter_encode_chunks(data):
                q.put(chunk)

    def mpub(self, topic, messages):
        """
        Publish multiple messages to topic
        """
        q = self.get_topic_queue(topic)
        for m in messages:
            for chunk in q.iter_encode_chunks(m):
                q.put(chunk)

    def get_executor(self, name: str) -> ThreadPoolExecutor:
        """
        Return or start named executor
        """
        executor = self.executors.get(name)
        if not executor:
            xt = "%s.%s_threads" % (self.name, name)
            max_threads = config.get_parameter(xt)
            self.logger.info(
                "Starting threadpool executor %s (up to %d threads)", name, max_threads
            )
            executor = ThreadPoolExecutor(max_threads, name=name)
            self.executors[name] = executor
        return executor

    def run_in_executor(
        self, name: str, fn: Callable[[Any], T], *args: Any, **kwargs: Any
    ) -> asyncio.Future:
        executor = self.get_executor(name)
        return executor.submit(fn, *args, **kwargs)

    def register_metrics(self, table, metrics):
        """
        Register metrics

        :param table: Table name
        :param metrics: List of dicts containing metrics records
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def _iter_metrics_raw_chunks(table, metrics):
        start = 0
        while start < len(metrics):
            limit = config.nsqd.mpub_size - 8
            r = [table]
            limit -= len(table) + 1
            for m in metrics[start:]:
                jm = ujson.dumps(m)
                js = len(jm) + 1
                if limit < js:
                    break
                r += [jm]
                limit -= js
                start += 1
            yield "\n".join(r)

    def _register_unclustered_metrics(self, table, metrics):
        """
        Register metrics to send in non-clustered configuration.
        Must be used via register_metrics only

        :param fields: Table name
        :param metrics: List of dicts containing metrics records
        :return:
        """
        for chunk in self._iter_metrics_raw_chunks(table, metrics):
            self.pub("chwriter", chunk, raw=True)

    def _register_replicated_metrics(self, table, metrics):
        """
        Register metrics to send in non-sharded replicated configuration.
        Must be used via register_metrics only

        :param fields: Table name
        :param metrics: List of dicts containing metrics records
        :return:
        """
        # Change table name to raw_*
        table = "raw_%s" % table
        # Split and publish parts
        replicas = config.ch_cluster_topology[0].replicas
        for chunk in self._iter_metrics_raw_chunks(table, metrics):
            for nr in range(replicas):
                self.pub("chwriter-1-%s" % (nr + 1), chunk, raw=True)

    def _register_sharded_metrics(self, table, metrics):
        """
        Register metrics to send in sharded replicated configuration
        Must be used via register_metrics only

        :param table: Table name
        :param metrics: List of dicts containing metrics records
        :return:
        """
        # Distribute data to shards
        data = defaultdict(list)
        for m in metrics:
            for ch in self.get_shards(table, m):
                data[ch] += [m]
        # Change table name to raw_*
        table = "raw_%s" % table
        # Publish metrics
        for ch in data:
            for chunk in self._iter_metrics_raw_chunks(table, data[ch]):
                self.pub(ch, chunk, raw=True)

    def start_telemetry_callback(self) -> None:
        """
        Run telemetry callback
        :return:
        """
        self.telemetry_callback = PeriodicCallback(self.send_telemetry, 250)
        self.telemetry_callback.start()

    async def send_telemetry(self):
        """
        Publish telemetry data

        :return:
        """
        spans = get_spans()
        if spans:
            self.register_metrics("span", [span_to_dict(s) for s in spans])

    def log_request(self, handler):
        """
        Custom HTTP Log request handler
        :param handler:
        :return:
        """
        status = handler.get_status()
        method = handler.request.method
        uri = handler.request.uri
        remote_ip = handler.request.remote_ip
        if status == 200 and uri == "/mon/" and method == "GET":
            self.logger.debug("Monitoring request (%s)", remote_ip)
            metrics["mon_requests"] += 1
        elif (status == 200 or status == 429) and uri.startswith("/health/") and method == "GET":
            pass
        elif status == 200 and uri == ("/metrics") and method == "GET":
            pass
        else:
            self.logger.info(
                "%s %s (%s) %.2fms", method, uri, remote_ip, 1000.0 * handler.request.request_time()
            )
            metrics["http_requests", ("method", method.lower())] += 1
            metrics["http_response", ("status", status)] += 1

    def get_leader_lock_name(self):
        if self.leader_lock_name:
            return self.leader_lock_name % {"pool": config.pool}
        else:
            return None

    def add_close_callback(self, cb, *args, **kwargs):
        self.close_callbacks += [(cb, args, kwargs)]

    def get_backend_weight(self):
        """
        Return backend weight for weighted load balancers
        (i.e. traefik).
        Return None for default weight
        :return:
        """
        return None

    def get_backend_limit(self):
        """
        Return backend connection limit for load balancers
        (i.e. traefik)
        Return None for no limits
        :return:
        """
        return None

    def is_valid_health_check(self, service_id):
        """
        Check received service id matches own service id
        :param service_id:
        :return:
        """
        if (
            self.dcs
            and self.dcs.health_check_service_id
            and self.dcs.health_check_service_id != service_id
        ):
            return False
        else:
            return True

    def get_health_status(self):
        """
        Check service health to be reported to service registry
        :return: (http code, message)
        """
        if self.dcs and self.require_dcs_health:
            # DCS is initialized
            return self.dcs.get_status()
        else:
            return 200, "OK"

    def uptime(self):
        if not self.startup_ts:
            return 0
        return time.time() - self.startup_ts
