# ----------------------------------------------------------------------
# mx service
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import orjson

# NOC modules
from noc.core.service.tornado import TornadoService
from noc.core.mx import MX_STREAM
from noc.config import config
from noc.core.liftbridge.message import Message
from noc.core.mx import MX_SHARDING_KEY
from noc.services.mx.router.router import Router
from noc.services.mx.router.action import DROP
from noc.core.perf import metrics


class MXService(TornadoService):
    name = "mx"
    use_mongo = True

    if config.features.traefik:
        traefik_backend = "mx"
        traefik_frontend_rule = "PathPrefix:/api/mx"

    def __init__(self):
        super().__init__()
        self.slot_number = 0
        self.total_slots = 0
        self.router = Router()

    async def on_activate(self):
        self.router.load()
        self.slot_number, self.total_slots = await self.acquire_slot()
        await self.subscribe_stream(MX_STREAM, self.slot_number, self.on_message)

    async def on_message(self, msg: Message) -> None:
        metrics["messages"] += 1
        # Apply routes
        self.logger.debug("[%d] Receiving message %s", msg.offset, msg.headers)
        for route in self.router.iter_route(msg):
            metrics["route_hits"] += 1
            self.logger.debug("[%d] Applying route %s", msg.offset, route.name)
            # Apply actions
            routed: bool = False
            for stream, action_headers in route.iter_action(msg):
                metrics["action_hits"] += 1
                # Fameless drop
                if stream == DROP:
                    metrics["action_drops"] += 1
                    self.logger.debug("[%s] Dropped. Stopping processing", msg.offset)
                    return
                # Build resulting headers
                headers = {}
                headers.update(msg.headers)
                if action_headers:
                    headers.update(action_headers)
                # Determine sharding channel
                sharding_key = int(headers.get(MX_SHARDING_KEY, b"0"))
                partitions = await self.get_stream_partitions(stream)
                partition = sharding_key % partitions
                # Single message may be transmuted in zero or more messages
                for body in route.iter_transmute(headers, msg.value):
                    if not isinstance(body, bytes):
                        # Transmute converts message to an arbitrary structure,
                        # so convert back to the json
                        body = orjson.dumps(body)
                    metrics[("forwards", "%s:%s" % (stream, partition))] += 1
                    self.logger.debug("[%s] Routing to %s:%s", msg.offset, stream, partition)
                    self.publish(value=body, stream=stream, partition=partition, headers=headers)
                routed = True
            if not routed:
                self.logger.debug("[%d] Not routed", msg.offset)
                metrics["route_misses"] += 1
        self.logger.debug("[%s] Finish processing", msg.offset)


if __name__ == "__main__":
    MXService().start()
