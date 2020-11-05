# ----------------------------------------------------------------------
# TanNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional
from math import tan

# NOC modules
from .base import BaseCDAGNode, ValueType


class TanNode(BaseCDAGNode):
    """
    Get tangens of 'x'
    """

    name = "tan"
    static_inputs = ["x"]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None:
            return None
        return tan(x)
