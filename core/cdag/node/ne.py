# ----------------------------------------------------------------------
# NENode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional


# NOC modules
from .base import BaseCDAGNode, ValueType, Category
from .eq import CompConfig


class NeNode(BaseCDAGNode):
    """
    Compare `x` and `y`. Activate with `true_level` if difference is greater than `epsilon`,
    activate with `false_level` otherwise
    """

    name = "eq"
    static_inputs = ["x", "y"]
    config_cls = CompConfig
    categories = [Category.COMPARE]

    def get_value(self) -> Optional[ValueType]:
        x, y = self.get_all_inputs()
        if x is None or y is None:
            return None
        if abs(x - y) > self.config.epsilon:
            return self.config.true_level
        return self.config.false_level
