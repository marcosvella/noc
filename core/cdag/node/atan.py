# ----------------------------------------------------------------------
# ATanNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional
from math import atan

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class ATanNode(BaseCDAGNode):
    """
    Get arctangens of 'x'
    """

    name = "atan"
    static_inputs = ["x"]
    categories = [Category.MATH]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None:
            return None
        return atan(x)
