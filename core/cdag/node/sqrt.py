# ----------------------------------------------------------------------
# SqrtNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional
from math import sqrt

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class SqrtNode(BaseCDAGNode):
    """
    Get square root of 'x'
    """

    name = "sqrt"
    static_inputs = ["x"]
    categories = [Category.MATH]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None or x < 0:
            return None
        return sqrt(x)
