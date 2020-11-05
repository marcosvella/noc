# ----------------------------------------------------------------------
# AddNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional

# NOC modules
from .base import BaseCDAGNode, ValueType


class AddNode(BaseCDAGNode):
    """
    Add `x` to `y`
    """

    name = "add"
    static_inputs = ["x", "y"]

    def get_value(self) -> Optional[ValueType]:
        x, y = self.get_all_inputs()
        if x is None or y is None:
            return None
        return x + y
