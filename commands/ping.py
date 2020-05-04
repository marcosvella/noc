# ----------------------------------------------------------------------
# Pretty command
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import argparse

# Third-party modules
from tornado.ioloop import IOLoop
import tornado.gen
import tornado.queues

# NOC modules
from noc.core.management.base import BaseCommand
from noc.core.validators import is_ipv4
from noc.core.ioloop.ping import Ping
from noc.core.ioloop.util import setup_asyncio


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--in", action="append", dest="input", help="File with addresses")
        parser.add_argument(
            "--jobs", action="store", type=int, default=100, dest="jobs", help="Concurrent jobs"
        )
        parser.add_argument("addresses", nargs=argparse.REMAINDER, help="Object name")

    def handle(self, input, addresses, jobs, *args, **options):
        self.addresses = set()
        # Direct addresses
        for a in addresses:
            if is_ipv4(a):
                self.addresses.add(a)
        # Read addresses from files
        if input:
            for fn in input:
                try:
                    with open(fn) as f:
                        for line in f:
                            line = line.strip()
                            if is_ipv4(line):
                                self.addresses.add(line)
                except OSError as e:
                    self.die("Cannot read file %s: %s\n" % (fn, e))
        # Ping
        setup_asyncio()
        self.ping = Ping()
        self.jobs = jobs
        self.queue = tornado.queues.Queue(self.jobs)
        for i in range(self.jobs):
            IOLoop.current().spawn_callback(self.ping_worker)
        IOLoop.current().run_sync(self.ping_task)

    async def ping_task(self):
        for a in self.addresses:
            await self.queue.put(a)
        for i in range(self.jobs):
            await self.queue.put(None)
        await self.queue.join()

    async def ping_worker(self):
        while True:
            a = await self.queue.get()
            if a:
                rtt, attempts = await self.ping.ping_check_rtt(a, count=1, timeout=1000)
                if rtt:
                    self.stdout.write("%s %.2fms\n" % (a, rtt * 1000))
                else:
                    self.stdout.write("%s FAIL\n" % a)
            self.queue.task_done()
            if not a:
                break


if __name__ == "__main__":
    Command().run()
