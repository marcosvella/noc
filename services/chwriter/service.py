#!./bin/python
# ----------------------------------------------------------------------
# chwriter service
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from time import perf_counter
import asyncio
from typing import AsyncIterable

# Third-party modules
from typing import Dict

# NOC modules
from noc.core.service.fastapi import FastAPIService
from noc.core.http.client import fetch
from noc.config import config
from noc.core.perf import metrics
from noc.services.chwriter.channel import Channel
from noc.core.ioloop.timers import PeriodicCallback
from noc.core.liftbridge.base import LiftBridgeClient, StartPosition


class CHWriterService(FastAPIService):
    name = "chwriter"

    CH_SUSPEND_ERRORS = {598, 599}

    def __init__(self):
        super().__init__()
        self.channels: Dict[str, Channel] = {}
        self.last_ts = None
        self.last_metrics = 0
        self.table_fields = {}  # table name -> fields
        self.last_columns = 0
        self.is_sharded = False
        self.stopping = False
        self.restore_timeout = None
        # Queue of channels to flush
        self.flush_queue = asyncio.Queue()

    async def on_activate(self):
        report_callback = PeriodicCallback(self.report, 10000)
        report_callback.start()
        check_callback = PeriodicCallback(self.check_channels, config.chwriter.batch_delay_ms)
        check_callback.start()
        asyncio.create_task(self.subscribe_ch_streams())
        asyncio.create_task(self.flush_data())
        self.logger.info("Sending records to %s" % self.ch_address)

    async def iter_ch_streams(self) -> AsyncIterable[str]:
        """
        Yields CH stream names
        :return:
        """
        async with LiftBridgeClient() as client:
            while True:
                meta = await client.fetch_metadata()
                if meta.metadata:
                    for stream_meta in meta.metadata:
                        if stream_meta.name.startswith("ch."):
                            yield stream_meta.name
                    break
                else:
                    # Cluster election in progress or cluster is misconfigured
                    self.logger.info("Cluster has no active partitions. Waiting")
                    await asyncio.sleep(1)

    async def subscribe_ch_streams(self) -> None:
        """
        Subscribe to all CH streams
        :return:
        """
        async for stream in self.iter_ch_streams():
            asyncio.create_task(self.process_stream(stream))
            await asyncio.sleep(0.25)  # Shift subscriptions in time

    async def process_stream(self, stream: str) -> None:
        self.logger.info("[%s] Subscribing", stream)
        table = stream[3:]
        channel = Channel(self, table)
        self.channels[table] = channel
        cursor_id = f"chwriter-{config.chwriter.replica_id}"
        async with LiftBridgeClient() as client:
            async for msg in client.subscribe(
                stream=stream,
                partition=config.chwriter.shard_id,
                start_position=StartPosition.RESUME,
                cursor_id=cursor_id,
            ):
                offset = await channel.feed(msg)
                if offset:
                    # Data has been flushed, save cursor
                    await client.set_cursor(
                        stream,
                        partition=config.chwriter.shard_id,
                        cursor_id=cursor_id,
                        offset=offset,
                    )

    async def flush_data(self):
        """
        Flush data
        :return:
        """
        if config.clickhouse.cluster and config.chwriter.write_to:
            # Distributed configuration
            address = config.chwriter.write_to
        else:
            # Standalone configuration
            address = config.clickhouse.rw_addresses[0]
        while not self.stopping:
            ch = await self.flush_queue.get()
            n_records = ch.records
            while True:
                try:
                    self.logger.info("[%s] Sending %d records", ch.table, n_records)
                    t0 = perf_counter()
                    url = (
                        f"http://{address}/?"
                        f"user={config.clickhouse.rw_user}&"
                        f"password={config.clickhouse.rw_password or ''}&"
                        "database={config.clDickhouse.db}&"
                        "query={ch.q_sql}"
                    )
                    code, headers, body = await fetch(
                        url,
                        method="POST",
                        body=ch.get_data(),
                        user=config.clickhouse.rw_user,
                        password=config.clickhouse.rw_password or "",
                        content_encoding=config.clickhouse.encoding,
                    )
                    if code == 200:
                        self.logger.info(
                            "[%s] %d records sent in %.2fms",
                            ch.table,
                            n_records,
                            (perf_counter() - t0) * 1000,
                        )
                        metrics["records_written"] += n_records
                        break
                    elif code in self.CH_SUSPEND_ERRORS:
                        self.logger.info("[%s] Timed out: %s", ch.table, body)
                        metrics["error", ("type", "records_spool_timeouts")] += 1
                        await asyncio.sleep(1)
                        continue
                    else:
                        self.logger.info(
                            "[%s] Failed to write records: %s %s", ch.table, code, body
                        )
                        metrics["error", ("type", "records_spool_failed")] += 1
                        break
                except Exception as e:
                    self.logger.error(
                        "[%s] Failed to spool %d records due to unknown error: %s",
                        ch.table,
                        n_records,
                        e,
                    )
                    await asyncio.sleep(1)
                    continue
            ch.flush_complete()

    async def report(self):
        nm = metrics["records_written"].value
        t = perf_counter()
        if self.last_ts:
            speed = float(nm - self.last_metrics) / (t - self.last_ts)
            self.logger.info(
                "Feeding speed: %.2frecords/sec, active channels: %s, buffered records: %d",
                speed,
                metrics["channels_active"].value,
                metrics["records_buffered"].value,
            )
        self.last_metrics = nm
        self.last_ts = t

    async def check_channels(self):
        ts = perf_counter()
        expired = [c for c in self.channels.values() if c.is_expired(ts)]
        for ch in expired:
            self.logger.debug("[%s] Flushing due to timeout", ch.table)
            await ch.schedule_flush()

    def stop(self):
        # Stop consuming new messages
        self.stopping = True
        # .stop() will wait until queued data will be really published
        super().stop()


if __name__ == "__main__":
    CHWriterService().start()
