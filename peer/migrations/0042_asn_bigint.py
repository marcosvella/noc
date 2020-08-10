# ----------------------------------------------------------------------
# Change AS.asn type to bigint
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import bson

# NOC module
from noc.core.migration.base import BaseMigration


class Migration(BaseMigration):
    def migrate(self):
        self.db.execute("ALTER TABLE peer_as ALTER asn TYPE BIGINT")
