# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# IGetInterfaceStatusEx
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------
# NOC modules
from noc.core.interface.base import BaseInterface
from .base import DictListParameter, InterfaceNameParameter, BooleanParameter, IntParameter


class IGetInterfaceStatusEx(BaseInterface):
    """
    Returns extended interface status for all available interfaces
    including port channels and SVI
    """

    interfaces = DictListParameter(
        attrs={"interface": InterfaceNameParameter(), "ifindex": IntParameter()}, required=False
    )
    returns = DictListParameter(
        attrs={
            "interface": InterfaceNameParameter(),
            "admin_status": BooleanParameter(required=False),
            "oper_status": BooleanParameter(required=False),
            "full_duplex": BooleanParameter(required=False),
            "last_change": IntParameter(required=False),
            # Input speed, kbit/s
            "in_speed": IntParameter(required=False),
            # Output speed, kbit/s
            "out_speed": IntParameter(required=False),
            # Configured bandwidth, kbit/s
            "bandwidth": IntParameter(required=False),
        }
    )
    preview = "NOC.sa.managedobject.scripts.ShowInterfaceStatusEx"
