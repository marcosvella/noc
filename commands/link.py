# ---------------------------------------------------------------------
# Link management CLI interface
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import argparse
import time
import datetime
from collections import defaultdict

# NOC modules
from noc.core.management.base import BaseCommand, CommandError
from noc.core.mongo.connection import connect
from noc.inv.models.interface import Interface
from noc.inv.models.link import Link


class Command(BaseCommand):
    help = "Show Links"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="cmd")
        # show command
        show_parser = subparsers.add_parser("show", help="Show link")
        show_parser.add_argument(
            "-m",
            "--show-method",
            dest="show_method",
            action="store_true",
            help="Show discovery method",
        )
        show_parser.add_argument("args", nargs=argparse.REMAINDER, help="Show discovery method")
        # add command
        add_parser = subparsers.add_parser("add", help="Add link")
        add_parser.add_argument("args", nargs=argparse.REMAINDER, help="Show discovery method")
        # remove command
        remove_parser = subparsers.add_parser("remove", help="Remove link")
        remove_parser.add_argument("args", nargs=argparse.REMAINDER, help="Show discovery method")
        # Clean TTL Link
        ttl_policy = subparsers.add_parser("ttl-policy", help="Remove links by TTL")
        ttl_policy.add_argument("--ttl", type=int, help="TTL by days", default=10)
        ttl_policy.add_argument(
            "--approve", dest="dry_run", action="store_false", help="Apply changes"
        )

    def handle(self, *args, **options):
        action = options["cmd"]
        if not action:
            action = "show"
        connect()
        getattr(self, "handle_%s" % action.replace("-", "_"))(*args, **options)

    def show_link(self, link, show_method=False):
        def format_interface(i):
            return "%s@%s" % (i.managed_object.name, i.name)

        i = defaultdict(list)
        for li in link.interfaces:
            i[li.managed_object] += [li]
        r = []
        for mo in i:
            r += [", ".join(format_interface(li) for li in i[mo])]
        link = " --- ".join(r)
        if show_method:
            link += " [%s]" % link.discovery_method
        self.stdout.write(link)

    def handle_show(self, *args, **options):
        show_method = options.get("show_method")
        if args:
            # Show single link
            for i in args:
                iface = Interface.get_interface(i)
                if iface:
                    link = Link.objects.filter(interfaces=iface.id).first()
                    if link:
                        self.show_link(link, show_method)
        else:
            # Show all links
            for l in Link.objects.all():
                self.show_link(l, show_method)

    def handle_add(self, *args, **options):
        """
        Add link
        :param args:
        :param options:
        :return:
        """
        if len(args) != 2:
            raise CommandError("Usage: ./noc link --add <iface1> <iface2>")
        i1 = Interface.get_interface(args[0])
        if not i1:
            raise CommandError("Invalid interface: %s" % args[0])
        i2 = Interface.get_interface(args[1])
        if not i2:
            raise CommandError("Invalid interface: %s" % args[1])
        try:
            i1.link_ptp(i2)
        except ValueError as why:
            raise CommandError(str(why))

    def handle_remove(self, *args, **options):
        """
        Remove link
        :param args:
        :param options:
        :return:
        """
        for i in args:
            iface = Interface.get_interface(i)
            if iface:
                iface.unlink()

    def handle_ttl_policy(self, ttl=10, dry_run=True, *args, **options):
        from noc.fm.models.activealarm import ActiveAlarm

        today = datetime.datetime.now()
        deadline = today - datetime.timedelta(days=ttl)

        alarm_mos = [
            d["managed_object"]
            for d in ActiveAlarm._get_collection().find(
                {"managed_object": {"$exists": True}}, {"managed_object": 1}
            )
        ]
        # Filter object with Active alarm, and manual links
        deadline_links = Link.objects.filter(
            last_seen__lt=deadline, linked_objects__nin=alarm_mos, discovery_method__ne=""
        )
        self.print(
            "# Links: %d, Deadline links: %d, Manual links: %d, On alarmed objects: %d"
            % (
                Link.objects.count(),
                Link.objects.filter(last_seen__lt=deadline).count(),
                Link.objects.filter(discovery_method="").count(),
                Link.objects.filter(linked_objects__in=alarm_mos).count(),
            )
        )
        self.print(
            "# %d/%d Links over on deadline: %s"
            % (deadline_links.count(), Link.objects.count(), deadline)
        )

        if not dry_run:
            self.print("Claimed data will be Loss..\n")
            for i in reversed(range(1, 10)):
                self.print("%d\n" % i)
                time.sleep(1)
            for link in list(deadline_links):
                self.print("Clean %s" % link)
                iface = link.interfaces[0]
                iface.unlink()
            self.print("# Done.")


if __name__ == "__main__":
    Command().run()
