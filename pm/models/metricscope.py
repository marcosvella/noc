# ---------------------------------------------------------------------
# MetricScope model
# ---------------------------------------------------------------------
# Copyright (C) 2007-2021 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import operator
from threading import Lock
from typing import Optional

# Third-party modules
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import (
    StringField,
    ListField,
    EmbeddedDocumentField,
    UUIDField,
    BooleanField,
)
import cachetools

# NOC Modules
from noc.config import config
from noc.core.model.decorator import on_save
from noc.core.prettyjson import to_json
from noc.core.model.decorator import on_delete_check
from noc.main.models.label import Label

id_lock = Lock()


class KeyField(EmbeddedDocument):
    # Table field name
    field_name = StringField()
    # Model reference, i.e. sa.ManagedObject
    model = StringField()

    def __str__(self):
        return self.field_name

    def to_json(self):
        return {"field_name": self.field_name, "model": self.model}

    @property
    def field_type(self):
        return "UInt64"


class LabelItem(EmbeddedDocument):
    # Wildcard label, noc::<scope>::* is preferable
    label = StringField()
    is_required = BooleanField(default=False)
    # Store data in separate table column `store_field`, if not empty
    # store in `labels` field otherwise
    store_column = StringField()
    # Create separate view column `view_column`, if not empty.
    # Otherwise, create separate view column `store_column` if set.
    # Do not create view column otherwise.
    view_column = StringField()
    # Part of primary key, implies `store_column` if set
    is_primary_key = BooleanField(default=False)
    # Part of order key
    is_order_key = BooleanField(default=False)
    # Legacy path component, for transition period
    # Path position is determined by item position.
    # Do not set for newly created scopes
    is_path = BooleanField(default=False)

    def __str__(self):
        return self.label

    @property
    def field_name(self):
        name = self.label[:-3]  # Strip ::*
        if name.startswith("noc::"):
            return name[5:]
        return name

    @property
    def label_prefix(self):
        return self.label[:-1]  # skip trailing *

    def to_json(self):
        r = {
            "label": self.label,
            "is_required": self.is_required,
            "is_primary_key": self.is_primary_key,
            "is_order_key": self.is_order_key,
            "is_path": self.is_path,
        }
        if self.store_column:
            r["store_column"] = self.store_column
        if self.view_column:
            r["view_column"] = self.view_column
        return r


@on_delete_check(check=[("pm.MetricType", "scope")])
@on_save
class MetricScope(Document):
    meta = {
        "collection": "noc.metricscopes",
        "strict": False,
        "auto_create_index": False,
        "json_collection": "pm.metricscopes",
        "json_unique_fields": ["name"],
    }

    name = StringField(unique=True)
    uuid = UUIDField(binary=True)
    # Database table name
    table_name = StringField()
    description = StringField(required=False)
    key_fields = ListField(EmbeddedDocumentField(KeyField))
    labels = ListField(EmbeddedDocumentField(LabelItem))
    enable_timedelta = BooleanField(default=False)

    _id_cache = cachetools.TTLCache(maxsize=100, ttl=60)

    def __str__(self):
        return self.name

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_id_cache"), lock=lambda _: id_lock)
    def get_by_id(cls, id) -> Optional["MetricScope"]:
        return MetricScope.objects.filter(id=id).first()

    def on_save(self):
        for label in self.labels:
            Label.ensure_label(
                label.label, description="Auto-created for PM scope", is_protected=True
            )

    @property
    def json_data(self):
        r = {
            "name": self.name,
            "$collection": self._meta["json_collection"],
            "uuid": self.uuid,
            "table_name": self.table_name,
            "description": self.description,
            "key_fields": [kf.to_json() for kf in self.key_fields],
            "labels": [p.to_json() for p in self.labels],
            "enable_timedelta": self.enable_timedelta,
        }
        return r

    def to_json(self):
        return to_json(
            self.json_data,
            order=[
                "name",
                "$collection",
                "uuid",
                "table_name",
                "description",
                "key_fields",
                "path",
            ],
        )

    def get_json_path(self):
        return f"{self.name}.json"

    def iter_fields(self):
        """
        Yield (field_name, field_type) tuples
        :return:
        """
        from .metrictype import MetricType

        yield "date", "Date"
        yield "ts", "DateTime"
        yield "metric_type", "String"
        for f in self.key_fields:
            yield f.field_name, f.field_type
        yield "labels", "Array(String)"
        if self.enable_timedelta:
            yield "time_delta", "UInt16"
        for t in MetricType.objects.filter(scope=self.id).order_by("id"):
            yield t.field_name, t.field_type

    def get_create_sql(self):
        """
        Get CREATE TABLE SQL statement
        :return:
        """
        # Key Fields
        kf = [f.field_name for f in self.key_fields]
        kf += ["date"]
        pk, ok = kf[:], kf[:]
        for label in self.labels:
            if label.is_order_key or label.is_primary_key:
                # Primary Key must be a prefix of the sorting key
                ok += [f"arrayFirst(x -> startsWith(x, '{label.label_prefix}'), labels)"]
            if label.is_primary_key:
                pk += [f"arrayFirst(x -> startsWith(x, '{label.label_prefix}'), labels)"]
        r = [
            "CREATE TABLE IF NOT EXISTS %s (" % self._get_raw_db_table(),
            ",\n".join("  %s %s" % (n, t) for n, t in self.iter_fields()),
            f") ENGINE = MergeTree() ORDER BY ({', '.join(ok)})\n",
            f"PARTITION BY toYYYYMM(date) PRIMARY KEY ({', '.join(pk)})",
        ]
        return "\n".join(r)

    def get_create_distributed_sql(self):
        """
        Get CREATE TABLE for Distributed engine
        :return:
        """
        return (
            "CREATE TABLE IF NOT EXISTS %s "
            "AS %s "
            "ENGINE = Distributed(%s, %s, %s)"
            % (
                self.table_name,
                self._get_raw_db_table(),
                config.clickhouse.cluster,
                config.clickhouse.db,
                self._get_raw_db_table(),
            )
        )

    def get_create_view_sql(self):
        view = self._get_db_table()
        if config.clickhouse.cluster:
            src = self._get_distributed_db_table()
        else:
            src = self._get_raw_db_table()
        # path emulation
        v_path = ""
        path = [label.label_prefix for label in self.labels if label.is_path]
        if path:
            l_exp = ", ".join(f"arrayFirst(x -> startsWith(x, '{pn}'), labels)" for pn in path)
            v_path = f"[{l_exp}] AS path, "
        # view columns
        vc_expr = ""
        view_columns = [
            label for label in self.labels if label.view_column and not label.store_column
        ]
        if view_columns:
            vc_expr = ", ".join(
                f"arrayFirst(x -> startsWith(x, '{x.field_name}'), labels) AS {x.view_column}, "
                for x in view_columns
            )
        return f"CREATE OR REPLACE VIEW {view} AS SELECT {v_path}{vc_expr}* FROM {src}"

    def _get_db_table(self):
        return self.table_name

    def _get_raw_db_table(self):
        return f"raw_{self.table_name}"

    def _get_distributed_db_table(self):
        return f"d_{self.table_name}"

    def ensure_table(self, connect=None):
        """
        Ensure table is exists
        :return: True, if table has been changed
        """
        from noc.core.clickhouse.connect import connection

        def ensure_column(table_name, column):
            """
            If path not exists on column - new schema
            :param table_name:
            :return:
            """
            return bool(
                ch.execute(
                    """
                SELECT 1
                FROM system.columns
                WHERE
                  database=%s
                  AND table=%s
                  AND name=%s
                """,
                    [config.clickhouse.db, table_name, column],
                )
            )

        def ensure_columns(table_name):
            c = False
            # Alter when necessary
            existing = {}
            for name, type in ch.execute(
                """
                SELECT name, type
                FROM system.columns
                WHERE
                  database=%s
                  AND table=%s
                """,
                [config.clickhouse.db, table_name],
            ):
                existing[name] = type
            after = None
            for f, t in self.iter_fields():
                if f not in existing:
                    ch.execute(post=f"ALTER TABLE {table_name} ADD COLUMN {f} {t} AFTER {after}")
                    c = True
                after = f
                if f in existing and existing[f] != t:
                    print(f"Warning! Type mismatch for column {f}: {existing[f]} <> {t}")
                    print(f"Set command manually: ALTER TABLE {table_name} MODIFY COLUMN {f} {t}")
            return c

        changed = False
        ch = connect or connection(read_only=False)
        is_cluster = bool(config.clickhouse.cluster)
        table = self._get_db_table()
        raw_table = self._get_raw_db_table()
        dist_table = self._get_distributed_db_table()
        # Legacy migration
        if ch.has_table(table) and not ch.has_table(raw_table):
            # Legacy scheme, data for non-clustered installations has been written
            # to table itself. Move to raw_*
            ch.rename_table(table, raw_table)
            changed = True
        # Old schema
        if ensure_column(raw_table, "path"):
            # Old schema, data table will be rename to old_ for save data.
            ch.rename_table(raw_table, f"old_{self.table_name}")
            pass
        # Ensure raw_* table
        if ch.has_table(raw_table):
            # raw_* table exists, check columns
            changed |= ensure_columns(raw_table)
        else:
            # Create new table
            ch.execute(post=self.get_create_sql())
            changed = True
        # For cluster mode check d_* distributed table
        if is_cluster:
            if ch.has_table(dist_table):
                changed |= ensure_columns(dist_table)
            else:
                ch.execute(post=self.get_create_distributed_sql())
                changed = True
        # Synchronize view
        if changed or not ch.has_table(table):
            ch.execute(post=self.get_create_view_sql())
            changed = True
        return changed
