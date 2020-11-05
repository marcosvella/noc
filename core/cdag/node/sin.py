# ----------------------------------------------------------------------
# SinNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional
from math import sin

# NOC modules
from .base import BaseCDAGNode, ValueType


class SinNode(BaseCDAGNode):
    """
    Get sinus of 'x'
    """

    name = "sin"
    static_inputs = ["x"]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None:
            return None
        return sin(x)
