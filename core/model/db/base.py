# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Autocommit pg database wrapper
# ----------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import psycopg2
from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper as PGDatabaseWrapper

# NOC modules
from .monitor import SpanCursor


class DatabaseWrapper(PGDatabaseWrapper):
    def _savepoint_allowed(self):
        return False

    def get_new_connection(self, conn_params):
        """
        Return raw psycopg connection. Do not mess with django setup phase
        :param conn_params:
        :return:
        """
        return psycopg2.connect(cursor_factory=SpanCursor, **conn_params)

    def init_connection_state(self):
        """
        :return:
        """
        self.connection.autocommit = True
        self.connection.set_client_encoding("UTF8")

    def _set_isolation_level(self, level):
        pass

    def _set_autocommit(self, state):
        pass
