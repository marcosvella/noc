# ----------------------------------------------------------------------
# BI Extractor
# ----------------------------------------------------------------------
# Copyright (C) 2007-2016 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import datetime
from noc.config import config


class BaseExtractor(object):
    """
    Extract data between timestamps
    """

    name = None
    # Time in seconds to delay extraction
    extract_delay = 0
    # Time in seconds to delay cleaning
    # counting from last extraction
    clean_delay = 0
    # Does extractor apply time-based restriction
    # or just a snapshot of existing data
    is_snapshot = False

    def __init__(self, prefix, start, stop):
        self.prefix = prefix
        self.start = start
        self.stop = stop
        self.clean_ts = stop - datetime.timedelta(seconds=self.clean_delay)
        self.last_ts = None

    @classmethod
    def is_enabled(cls):
        return getattr(config.bi, "enable_%s" % cls.name, False)

    def extract(self, *args, **options):
        pass

    def clean(self, force=False):
        """

        :param force: Really remove data
        :return:
        """

    @classmethod
    def get_start(cls):
        """
        Returns timestamp of first record
        or None when no data found
        :return:
        """
        if cls.is_snapshot:
            return datetime.datetime.now() - datetime.timedelta(seconds=cls.extract_delay + 1)
        # Should be overriden
        return None
