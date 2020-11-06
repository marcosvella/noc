# ----------------------------------------------------------------------
# ACosNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional
from math import acos

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class ACosNode(BaseCDAGNode):
    """
    Get arccosinus of 'x'
    """

    name = "acos"
    static_inputs = ["x"]
    categories = [Category.MATH]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None:
            return None
        return acos(x)
