# ----------------------------------------------------------------------
# KeyNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class KeyNode(BaseCDAGNode):
    """
    Pass `in` to output only when `key` is activated with non-zero
    """

    name = "key"
    static_inputs = ["key", "in"]
    categories = [Category.UTIL]

    def get_value(self) -> Optional[ValueType]:
        key, inp = self.get_all_inputs()
        if key is None or inp is None or not key:
            return None
        return inp
