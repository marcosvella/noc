# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# about
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from noc.core.management.base import BaseCommand
from noc.core.version import version


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.print(version.version)


if __name__ == "__main__":
    Command().run()
