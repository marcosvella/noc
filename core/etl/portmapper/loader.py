# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# NRI Port mapper loader
# ----------------------------------------------------------------------
# Copyright (C) 2007-2016 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import inspect
import logging
import os

# NOC modules
from .base import BasePortMapper
from noc.config import config

logger = logging.getLogger(__name__)


class PortMapperLoader(object):
    def __init__(self):
        self.loaders = {}

    def get_loader(self, name):
        loader = self.loaders.get(name)
        custom_name = os.path.basename(
            os.path.dirname(config.get_customized_paths("", prefer_custom=True)[0])
        )
        if not loader and custom_name:
            logging.info("Loading %s", name)
            mn = "%s.etl.portmappers.%s" % (custom_name, name)
            try:
                sm = __import__(mn, {}, {}, "*")
                for n in dir(sm):
                    o = getattr(sm, n)
                    if (
                        inspect.isclass(o)
                        and issubclass(o, BasePortMapper)
                        and o.__module__ == sm.__name__
                    ):
                        loader = o
                        break
                    logger.error("Loader not found: %s", name)
            except ImportError as e:
                logger.error("Failed to load: %s", e)
                loader = None
            self.loaders[name] = loader
        return loader


loader = PortMapperLoader()
