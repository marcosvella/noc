# ----------------------------------------------------------------------
# ASinNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional
from math import asin

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class ASinNode(BaseCDAGNode):
    """
    Get arcsinus of 'x'
    """

    name = "asin"
    static_inputs = ["x"]
    categories = [Category.MATH]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None:
            return None
        return asin(x)
