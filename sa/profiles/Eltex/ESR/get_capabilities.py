# ---------------------------------------------------------------------
# Eltex.ESR.get_capabilities
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_capabilities import Script as BaseScript
from noc.sa.profiles.Generic.get_capabilities import false_on_cli_error, false_on_snmp_error
from noc.core.mib import mib


class Script(BaseScript):
    name = "Eltex.ESR.get_capabilities"

    @false_on_cli_error
    def has_ipv6_cli(self):
        """
        Check box has IPv6 ND enabled
        """
        self.cli("show ipv6 neighbors")
        return True

    @false_on_cli_error
    def has_lldp_cli(self):
        """
        Check box has LLDP enabled
        """
        return True

    @false_on_snmp_error
    def has_lldp_snmp(self):
        """
        Check box has lldp enabled on Eltex
        """
        r = self.snmp.get(mib["LLDP-MIB::lldpStatsRemTablesInserts", 0])
        if r:
            return True
