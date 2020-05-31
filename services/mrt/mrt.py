#!./bin/python
# ---------------------------------------------------------------------
# MRTHandler
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import logging
import asyncio

# Third-party modules
import ujson

# Python modules
from noc.core.service.authhandler import AuthRequestHandler
from noc.core.service.error import RPCRemoteError, RPCError
from noc.core.perf import metrics
from noc.core.span import Span
from noc.sa.models.managedobject import ManagedObject
from noc.sa.models.useraccess import UserAccess
from noc.core.debug import error_report
from noc.core.error import ERR_UNKNOWN
from noc.config import config


logger = logging.getLogger(__name__)


class MRTRequestHandler(AuthRequestHandler):
    async def write_chunk(self, obj):
        data = ujson.dumps(obj)
        self.write("%s|%s" % (len(data), data))
        logger.debug("%s|%s" % (len(data), data))
        await self.flush()

    async def run_script(self, oid, script, args, span_id=0, bi_id=None):
        with Span(
            server="MRT",
            service="run_script",
            sample=int(config.mrt.enable_command_logging),
            in_label=bi_id or oid,
            parent=span_id,
            client=self.current_user,
        ) as span:
            try:
                await self.write_chunk({"id": str(oid), "running": True})
                logger.debug("[%s] Run script %s %s %s", span.context, oid, script, args)
                r = await self.service.sae.script(oid, script, args)
                metrics["mrt_success"] += 1
            except RPCRemoteError as e:
                span.set_error_from_exc(e, getattr(e, "remote_code", 1))
                return {"id": str(oid), "error": str(e)}
            except RPCError as e:
                logger.error("RPC Error: %s" % str(e))
                span.set_error_from_exc(e, getattr(e, "code", 1))
                return {"id": str(oid), "error": str(e)}
            except Exception as e:
                error_report()
                metrics["mrt_failed"] += 1
                span.set_error_from_exc(e)
                return {"id": str(oid), "error": str(e)}
            if r["errors"]:
                span.set_error(ERR_UNKNOWN, r["output"])
                return {"id": str(oid), "error": r["output"]}
            span.out_label = r["output"]
            return {"id": str(oid), "result": r["output"]}

    async def post(self, *args, **kwargs):
        """
        Request is the list of
        {
            id: <managed object id>,
            script: <script name>,
            args: <arguments>
        }
        :param args:
        :param kwargs:
        :return:
        """
        metrics["mrt_requests"] += 1
        # Parse request
        req = ujson.loads(self.request.body)
        # Disable nginx proxy buffering
        self.set_header("X-Accel-Buffering", "no")
        # Object ids
        ids = set(int(d["id"]) for d in req if "id" in d and "script" in d)
        logger.info(
            "Run task on parralels: %d (Max concurrent %d), for User: %s",
            len(req),
            config.mrt.max_concurrency,
            self.current_user,
        )
        # Check access
        qs = ManagedObject.objects.filter(id__in=list(ids))
        if not self.current_user.is_superuser:
            adm_domains = UserAccess.get_domains(self.current_user)
            qs = qs.filter(administrative_domain__in=adm_domains)
        ids = dict(qs.values_list("id", "bi_id"))
        with Span(
            sample=int(config.mrt.enable_command_logging),
            server="MRT",
            service="post",
            client=self.current_user,
            in_label=req,
        ) as span:
            if self.service.use_telemetry:
                logger.info(
                    "[%s] Enable telemetry for task, user: %s", span.span_id, self.current_user
                )
            futures = set()
            for d in req:
                if "id" not in d or "script" not in d:
                    continue
                oid = int(d["id"])
                if oid not in ids:
                    await self.write_chunk({"id": str(d["id"]), "error": "Access denied"})
                    metrics["mrt_access_denied"] += 1
                    continue
                while len(futures) >= config.mrt.max_concurrency:
                    done, futures = asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)
                    for f in done:
                        r = await f
                        await self.write_chunk(r)
                futures += [
                    self.run_script(
                        oid, d["script"], d.get("args"), span_id=span.span_id, bi_id=ids.get(oid)
                    )
                ]
            # Wait for rest
            while futures:
                done, futures = asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)
                for f in done:
                    r = await f
                    await self.write_chunk(r)
        logger.info("Done")
