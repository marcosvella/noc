# ---------------------------------------------------------------------
# Migrate pyrules to handlers
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.core.migration.base import BaseMigration


class Migration(BaseMigration):
    PMAP = [
        ("drop_event", "IEventTrigger"),
        ("get_single_result", "IReduceTask"),
        ("matrix_report", "IReduceTask"),
        ("mrt_result", "IReduceTask"),
        ("open_event", "IEvent"),
        ("prefix_list_provisioning", "IReduceTask"),
        ("refresh_config", "IEventTrigger"),
        ("result_report", "IReduceTask"),
        ("vc_provisioning", "IReduceTask"),
        ("version_inventory", "IReduceTask"),
    ]

    def migrate(self):
        for name, iface in self.PMAP:
            handler = "noc.solutions.noc.default.pyrules.%s.%s" % (name, name)
            if self.db.execute("SELECT COUNT(*) FROM main_pyrule WHERE name = %s", [name])[0][0]:
                # Pyrule exists, change handler
                self.db.execute(
                    'UPDATE main_pyrule SET handler=%s,"text"=NULL WHERE name=%s', [handler, name]
                )
            else:
                # Create new pyrule
                self.db.execute(
                    """INSERT INTO main_pyrule(name, interface, handler, description, changed)
                    VALUES(%s, %s, %s, %s, now())""",
                    [name, iface, handler, "%s solution" % handler],
                )
