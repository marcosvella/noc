# ----------------------------------------------------------------------
# Profile loader
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import sys
import glob
import os
import threading
import importlib
from typing import Optional, Type

# NOC modules
from noc.core.loader.base import BaseLoader
from noc.config import config
from .base import BaseProfile

GENERIC_PROFILE = "Generic.Host"


class ProfileLoader(BaseLoader):
    name = "profile"

    def __init__(self):
        super().__init__()
        self.profiles = {}  # Load profiles
        self.lock = threading.Lock()
        self.all_profiles = set()

    def get_profile(self, name) -> Optional[Type[BaseProfile]]:
        """
        Load profile and return BaseProfile instance.
        Returns None when no profile found or loading error occured
        """
        if name == GENERIC_PROFILE:
            name = "Generic"
        with self.lock:
            profile = self.profiles.get(name)
            if not profile:
                self.logger.info("Loading profile %s", name)
                if not self.is_valid_name(name):
                    self.logger.error("Invalid profile name")
                    return None
                for p in config.get_customized_paths("", prefer_custom=True):
                    path = os.path.join(p, "sa", "profiles", *name.split("."))
                    if not os.path.exists(os.path.join(path, "profile.py")):
                        continue
                    if p:
                        # Custom script
                        base_name = os.path.basename(os.path.dirname(p))
                        module_name = "%s.sa.profiles.%s" % (base_name, name)
                    else:
                        # Common script
                        module_name = "noc.sa.profiles.%s" % name
                    profile = self.find_class("%s.profile" % module_name, BaseProfile, name)
                    if profile:
                        profile.initialize()
                        break
                self.profiles[name] = profile
            return profile

    def reload(self):
        """
        Reset profile cache and release all modules
        """
        with self.lock:
            self.logger.info("Reloading profiles")
            for s in self.profiles:
                self.logger.debug("Reload profile %s", s.name)
                importlib.reload(sys.modules[s.__module__])
            self.profiles = {}
            self.all_profiles = set()

    def is_valid_name(self, name):
        return ".." not in name

    def find_profiles(self):
        """
        Scan all available profiles
        """
        ns = {GENERIC_PROFILE}
        for px in config.get_customized_paths(os.path.join("sa", "profiles"), prefer_custom=True):
            px = os.path.join(px, "*", "*", "__init__.py")
            for path in glob.glob(px):
                vendor, system = path.split(os.sep)[-3:-1]
                ns.add("%s.%s" % (vendor, system))
        with self.lock:
            self.all_profiles = ns

    def iter_profiles(self):
        """
        Returns all available profile names
        """
        if not self.all_profiles:
            self.find_profiles()
        yield from sorted(self.all_profiles)

    def has_profile(self, name):
        """
        Check profile is exists
        """
        if not self.all_profiles:
            self.find_profiles()
        return name in self.all_profiles

    def choices(self):
        return [(p, p) for p in self.iter_profiles()]


# Create singleton object
loader = ProfileLoader()
