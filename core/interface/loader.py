# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Interface loader
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import sys
import glob
import logging
import inspect
import threading
import os
import re
import importlib

# NOC modules
from .base import BaseInterface
from noc.config import config

logger = logging.getLogger(__name__)


class InterfaceLoader(object):
    rx_class = re.compile(r"^class\s+(?P<name>\S+)\(", re.MULTILINE)

    def __init__(self):
        self.interfaces = {}  # Load interfaces
        self.lock = threading.Lock()
        self.all_interfaces = set()

    def get_interface(self, name):
        """
        Load script and return BaseScript instance.
        Returns None when no script found or loading error occured
        """
        with self.lock:
            interface = self.interfaces.get(name)
            if interface:
                return interface
            logger.info("Loading interface %s", name)
            if not self.is_valid_name(name):
                logger.error("Invalid interface name")
                return None
            imname = name.lower()
            for p in config.get_customized_paths("", prefer_custom=True):
                if os.path.exists(os.path.join(p, "sa", "interfaces", "%s.py" % imname)):
                    if p:
                        # Custom script
                        base_name = os.path.basename(os.path.dirname(config.path.custom_path))
                    else:
                        # Common script
                        base_name = "noc"
                    module_name = "%s.sa.interfaces.%s" % (base_name, imname)
                    break
            else:
                logger.error("Interface not found: %s", name)
                self.interfaces[name] = None
                return None
            try:
                sm = __import__(module_name, {}, {}, "*")
                for n in dir(sm):
                    o = getattr(sm, n)
                    if (
                        inspect.isclass(o)
                        and issubclass(o, BaseInterface)
                        and o.__module__ == sm.__name__
                    ):
                        self.interfaces[name] = o
                        return o
            except Exception as e:
                logger.error("Failed to load interface %s: %s", name, e)
            self.interfaces[name] = None
            return None

    def reload(self):
        """
        Reset script cache and release all modules
        """
        with self.lock:
            logger.info("Reloading interfaces")
            for s in self.interfaces:
                logger.debug("Reload interface %s", s)
                importlib.reload(sys.modules[s.__module__])
            self.interfaces = {}
            self.all_interfaces = set()

    def is_valid_name(self, name):
        return ".." not in name

    def find_interfaces(self):
        """
        Scan all available scripts
        """
        ns = set()
        for gx in config.get_customized_paths(os.path.join("sa", "interfaces", "*.py")):
            for path in glob.glob(gx):
                if path in ("base.py", "__init__.py"):
                    continue
                with open(path) as f:
                    data = f.read()
                for match in self.rx_class.finditer(data):
                    iname = match.group("name")
                    fname = os.path.split(path)[1]
                    if iname.lower() == fname[:-3]:
                        ns.add(iname)
        with self.lock:
            self.all_interfaces = ns

    def iter_interfaces(self):
        """
        Returns all available script names
        """
        if not self.all_interfaces:
            self.find_interfaces()
        for s in sorted(self.all_interfaces):
            yield s

    def has_interface(self, name):
        """
        Check script is exists
        """
        if not self.all_interfaces:
            self.find_interfaces()
        return name in self.all_interfaces


# Create singleton object
loader = InterfaceLoader()
