# ---------------------------------------------------------------------
# IBM.NOS.get_fqdn
# ---------------------------------------------------------------------
# Copyright (C) 2007-2013 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.sa.profiles.Generic.get_fqdn import Script as BaseScript
from noc.sa.interfaces.igetfqdn import IGetFQDN


class Script(BaseScript):
    name = "IBM.NOS.get_fqdn"
    interface = IGetFQDN

    rx_hostname = re.compile(r"^hostname\s+\"(?P<hostname>\S+)\"", re.MULTILINE)
    rx_domain_name = re.compile(r"^ip dns domain\-name\s+(?P<domain>\S+)", re.MULTILINE)

    def execute_cli(self):
        h = self.cli("show running-config | include hostname")
        d = self.cli("show running-config | include domain-name")
        fqdn = []
        match = self.rx_hostname.search(h)
        if match:
            fqdn += [match.group("hostname")]
        match = self.rx_domain_name.search(d)
        if match:
            fqdn += [match.group("domain")]
        return ".".join(fqdn)
