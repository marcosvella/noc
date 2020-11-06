# ----------------------------------------------------------------------
# ReLUNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class ReLUNode(BaseCDAGNode):
    """
    Get ReLU activation function of 'x'
    """

    name = "relu"
    static_inputs = ["x"]
    categories = [Category.MATH, Category.ACTIVATION]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None:
            return None
        return max(x, 0)
