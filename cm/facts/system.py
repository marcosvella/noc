# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Common system settings
# ---------------------------------------------------------------------
# Copyright (C) 2007-2015 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from __future__ import absolute_import
from .base import BaseFact


class System(BaseFact):
    ATTRS = [
        "hostname",
        "domain_name",
        "profile",
        "vendor",
        "platform",
        "version",
        "timezone",
        "[nameservers]",
        "managed_object_name",
        "object_profile",
        "level",
        "location",
    ]

    def __init__(
        self,
        hostname=None,
        domain_name=False,
        profile=None,
        vendor=None,
        platform=None,
        version=None,
        timezone=None,
        nameservers=None,
        object_profile=None,
        level=None,
        location=None,
        **kwargs,
    ):
        super(System, self).__init__()
        self.hostname = hostname
        self.domain_name = domain_name
        self.profile = profile
        self.vendor = vendor
        self.platform = platform
        self.version = version
        self.timezone = timezone
        self.nameservers = nameservers
        self.managed_object_name = None
        self.object_profile = object_profile
        self.level = level
        self.location = location

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        self._hostname = value or None

    @property
    def domain_name(self):
        return self._domain_name

    @domain_name.setter
    def domain_name(self, value):
        self._domain_name = value or None

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, value):
        self._profile = value or None

    @property
    def vendor(self):
        return self._vendor

    @vendor.setter
    def vendor(self, value):
        self._vendor = value or None

    @property
    def platform(self):
        return self._platform

    @platform.setter
    def platform(self, value):
        self._platform = value or None

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value or None

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, value):
        self._timezone = value or None

    @property
    def nameservers(self):
        return self._nameservers

    @nameservers.setter
    def nameservers(self, value):
        self._nameservers = value or []

    @property
    def managed_object_name(self):
        return self._managed_object_name

    @managed_object_name.setter
    def managed_object_name(self, value):
        self._managed_object_name = value

    @property
    def object_profile(self):
        return self._object_profile

    @object_profile.setter
    def object_profile(self, value):
        self._object_profile = value

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value

    def bind(self):
        self.managed_object_name = self.managed_object.name
        if self.managed_object.object_profile:
            self.object_profile = self.managed_object.object_profile.name
            self.level = self.managed_object.object_profile.level
