# ----------------------------------------------------------------------
# StateNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------


# Python modules
from typing import Optional

# Third-party modules
from pydantic import BaseModel

# NOC modules
from .base import BaseCDAGNode, ValueType


class StateNodeState(BaseModel):
    value: Optional[ValueType]


class StateNode(BaseCDAGNode):
    """
    Save input value to a state value 'value' and proxies input to output
    """

    name = "state"
    static_inputs = "x"
    state_cls = StateNodeState
    dot_shape = "doubleoctagon"

    def get_value(self) -> Optional[ValueType]:
        value = self.get_input("x")
        self.state.value = value
        return value
