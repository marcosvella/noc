# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Alcatel.7302.get_metrics
# ---------------------------------------------------------------------
# Copyright (C) 2007-2016 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_metrics import Script as GetMetricsScript
from .oidrules.slot import SlotRule


class Script(GetMetricsScript):
    name = "Alcatel.7302.get_metrics"

    OID_RULES = [SlotRule]
