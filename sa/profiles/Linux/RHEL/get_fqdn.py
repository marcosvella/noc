# ---------------------------------------------------------------------
# Linux.RHEL.get_fqdn
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_fqdn import Script as BaseScript
from noc.sa.interfaces.igetfqdn import IGetFQDN


class Script(BaseScript):
    name = "Linux.RHEL.get_fqdn"
    interface = IGetFQDN
    always_prefer = "S"

    def execute_cli(self, **kwargs):
        v = self.cli("uname -n").strip()
        fqdn = v

        return fqdn
