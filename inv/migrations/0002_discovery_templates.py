# ---------------------------------------------------------------------
# Initialize discovery templates
# ---------------------------------------------------------------------
# Copyright (C) 2007-2012 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.core.migration.base import BaseMigration


NEW_PREFIXES_REPORT_SUBJECT = "{{ count }} new prefixes discovered"
NEW_PREFIXES_REPORT_BODY = """{{ count }} new prefixes discovered

{% for p in prefixes %}{{p.vrf.name}}: {{p.prefix}}{% if p.description %}
 ({{p.description}}){% endif %} at {{p.object.name}}:{{p.interface}}
{% endfor %}
"""

NEW_ADDRESSES_REPORT_SUBJECT = "{{ count }} new addresses discovered"
NEW_ADDRESSES_REPORT_BODY = """{{ count }} new prefixes discovered

{% for a in addresses %}{{a.vrf.name}}: {{a.address}}{% if a.description %}
 ({{a.description}}){% endif %} at {{a.object.name}}:{{a.interface}}
{% endfor %}
"""

ADDRESS_COLLISION_REPORT_SUBJECT = "{{ count }} address collisions found"
ADDRESS_COLLISION_REPORT_BODY = """{{ count }} address collisions found

{% for c in collisions %}{{ c.address }}: {{ c.vrf_old.name }}{% if c.object_old %} at {{ c.object_old.name }}
 {% endif %} vs {{ c.vrf_new.name }} at {{ c.object_new.name }}:{{ c.interface_new }}
{% endfor %}
"""


class Migration(BaseMigration):
    depends_on = [("main", "0037_template")]

    def migrate(self):
        for tn, description, subject, body in [
            (
                "inv.discovery.new_prefixes_report",
                "Discovery's New Prefixes Report",
                NEW_PREFIXES_REPORT_SUBJECT,
                NEW_PREFIXES_REPORT_BODY,
            ),
            (
                "inv.discovery.new_addresses_report",
                "Discovery's New Addresses Report",
                NEW_ADDRESSES_REPORT_SUBJECT,
                NEW_ADDRESSES_REPORT_BODY,
            ),
            (
                "inv.discovery.address_collision_report",
                "Discovery's Address Collision Report",
                ADDRESS_COLLISION_REPORT_SUBJECT,
                ADDRESS_COLLISION_REPORT_BODY,
            ),
        ]:
            self.db.execute(
                "INSERT INTO main_template(name, subject, body) VALUES(%s, %s, %s)",
                [tn, subject, body],
            )
            self.db.execute(
                """
                INSERT INTO main_systemtemplate(name, description, template_id)
                SELECT %s, %s, id
                FROM main_template
                WHERE name=%s
            """,
                [tn, description, tn],
            )
