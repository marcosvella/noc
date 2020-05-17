# ----------------------------------------------------------------------
# main.datastreamconfig application
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from noc.lib.app.extdocapplication import ExtDocApplication, view
from noc.main.models.datastreamconfig import DataStreamConfig
from noc.core.translation import ugettext as _


class DataStreamConfigApplication(ExtDocApplication):
    """
    DataStreamConfig application
    """

    title = "DataStream Config"
    menu = [_("Setup"), _("DataStream Config")]
    model = DataStreamConfig
