# ---------------------------------------------------------------------
# Initialize tags
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.core.migration.base import BaseMigration


class Migration(BaseMigration):
    depends_on = [
        ("dns", "0034_finish_tag_migration"),
        ("ip", "0024_finish_tag_migration"),
        ("peer", "0037_finish_tag_migration"),
        ("sa", "0063_finish_tag_migration"),
        ("vc", "0022_finish_tag_migration"),
    ]

    def migrate(self):
        c = self.mongo_db.noc.tags
        for m in [
            "sa_activator",
            "sa_managedobject",
            "sa_commandsnippet",
            "ip_vrfgroup",
            "ip_vrf",
            "ip_prefix",
            "ip_address",
            "ip_addressrange",
            "dns_dnszone",
            "dns_dnszonerecord",
            "vc_vc",
            "peer_as",
            "peer_asset",
            "peer_peer",
        ]:
            for tag, count in self.db.execute(
                """
                    SELECT unnest(tags), COUNT(*)
                    FROM %s
                    GROUP BY 1
                    """
                % m
            ):
                c.update_many(
                    {"tag": tag},
                    {"$addToSet": {"models": m}, "$inc": {"count": int(count)}},
                    upsert=True,
                )
