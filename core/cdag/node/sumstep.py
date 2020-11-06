# ----------------------------------------------------------------------
# SumStepNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List
from enum import Enum

# Third-party modules
from pydantic import BaseModel

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class SumStepNodeState(BaseModel):
    values: List[ValueType] = []


class StepDirection(str, Enum):
    INC = "inc"
    DEC = "dec"
    ABS = "abs"


class SumStepNodeConfig(BaseModel):
    direction: StepDirection = StepDirection.ABS
    min_window: int = 1
    max_window: int = 100


class SumStepNode(BaseCDAGNode):
    """
    Calculate sum of increments in the window.
    """

    name = "sumstep"
    static_inputs = "x"
    config_cls = SumStepNodeConfig
    state_cls = SumStepNodeState
    categories = [Category.WINDOW]

    def get_value(self) -> Optional[ValueType]:
        x = self.get_input("x")
        if x is None:
            return None
        self.state.values.append(x)
        # Trim
        if len(self.state.values) >= self.config.max_window:
            self.state.values = self.state.values[-self.config.max_window :]
        # Check window is filled
        lv = len(self.state.values)
        if lv < self.config.min_window or lv < 2:
            return None
        # Process directions
        window = self.state.values
        if self.config.direction == StepDirection.INC:
            return sum(x1 - x0 for x0, x1 in zip(window, window[1:]) if x1 > x0)
        if self.config.direction == StepDirection.DEC:
            return sum(x0 - x1 for x0, x1 in zip(window, window[1:]) if x1 < x0)
        return sum(abs(x1 - x0) for x0, x1 in zip(window, window[1:]))
