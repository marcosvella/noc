# ----------------------------------------------------------------------
# Task Collector
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import functools

# NOC modules
from .base import BaseCollector
from noc.core.ioloop.util import run_sync
from noc.core.liftbridge.base import LiftBridgeClient, Metadata, PartitionMetadata


class LiftbridgeStreamCollector(BaseCollector):
    name = "liftbridge"

    CURSOR_STREAM = {
        "events": "classifier",
        "dispose": "correlator",
        "mx": "mx",
        "kafkasender": "kafkasender",
    }

    async def get_meta(self) -> Metadata:
        async with LiftBridgeClient() as client:
            return await client.fetch_metadata()

    async def get_partition_meta(self, stream, partition) -> PartitionMetadata:
        async with LiftBridgeClient() as client:
            return await client.fetch_partition_metadata(stream, partition)

    async def fetch_cursor(self, stream, partition, name):
        async with LiftBridgeClient() as client:
            return await client.fetch_cursor(stream=stream, partition=partition, cursor_id=name)

    def iter_metrics(self):
        meta: Metadata = run_sync(self.get_meta)

        for stream in meta.metadata:
            for p in sorted(stream.partitions):
                if stream.name.startswith("_"):
                    continue
                name, pool, cursor = stream.name, None, -1
                if "." in name:
                    name, pool = name.split(".", 1)
                if name in self.CURSOR_STREAM:
                    cursor = run_sync(
                        functools.partial(
                            self.fetch_cursor, stream.name, p, self.CURSOR_STREAM[name]
                        )
                    )
                    if pool:
                        yield (
                            "stream_cursor_offset",
                            ("name", stream.name),
                            ("partition", p),
                            ("cursor_id", self.CURSOR_STREAM[name]),
                            ("pool", pool),
                        ), cursor
                    else:
                        yield (
                            "stream_cursor_offset",
                            ("name", stream.name),
                            ("partition", p),
                            ("cursor_id", self.CURSOR_STREAM[name]),
                        ), cursor

                try:
                    p_meta: PartitionMetadata = run_sync(
                        functools.partial(
                            self.get_partition_meta,
                            stream.name,
                            p,
                        )
                    )
                except Exception as e:
                    print("[%s|%s] Failed getting data for partition: %s" % (stream.name, p, e))
                    continue
                if pool:
                    yield (
                        "stream_newest_offset",
                        ("name", stream.name),
                        ("partition", p),
                        ("pool", pool),
                    ), p_meta.newest_offset
                    yield (
                        "stream_high_watermark",
                        ("name", stream.name),
                        ("partition", p),
                        ("pool", pool),
                    ), p_meta.high_watermark
                else:
                    yield (
                        "stream_newest_offset",
                        ("name", stream.name),
                        ("partition", p),
                    ), p_meta.newest_offset
                    yield (
                        "stream_high_watermark",
                        ("name", stream.name),
                        ("partition", p),
                    ), p_meta.high_watermark
