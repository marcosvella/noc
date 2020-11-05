# ----------------------------------------------------------------------
# AbsNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional

# NOC modules
from .base import BaseCDAGNode, ValueType


class AbsNode(BaseCDAGNode):
    """
    Get absolute value of 'x'
    """

    name = "abs"
    static_inputs = ["x"]

    def get_value(self) -> Optional[ValueType]:
        (x,) = self.get_all_inputs()
        if x is None:
            return None
        return x if x >= 0 else -x
