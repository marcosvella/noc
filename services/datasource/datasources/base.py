# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# BaseDatasource
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import logging

# NOC modules
from noc.main.models.datasourcecache import DataSourceCache
from noc.core.perf import metrics
from noc.config import config
from noc.core.text import ch_escape


class BaseDataSource(object):
    name = None
    CACHE_COLLECTION = "datasource_caches"
    lock = None
    ttl = config.datasource.default_ttl

    logger = logging.getLogger(__name__)

    def clean(self, row):
        s = "\t".join(str(x) for x in row)
        if "\n" in s or "\\" in s or s.count("\t") >= len(row):
            metrics["error", ("type", "rogue_chars")] += 1
            self.logger.error("Rogue chars in row %s", row)
            row = [ch_escape(x) if isinstance(x, str) else x for x in list(row)]
        return row

    def get(self):
        try:
            if self.lock:
                self.lock.acquire()
            # Try to get cached data
            data = DataSourceCache.get_data(self.name)
            if not data:
                data = ["\t".join(str(x) for x in self.clean(row)) for row in self.extract()]
                data += [""]
                data = "\n".join(data)
                DataSourceCache.set_data(self.name, data, self.ttl)
            return data
        finally:
            if self.lock:
                self.lock.release()

    def extract(self):
        """
        Generate list of rows. Each row is a list of fields
        :return:
        """
        raise NotImplementedError
