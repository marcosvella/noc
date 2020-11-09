# ----------------------------------------------------------------------
# ExpDecayNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List
from math import exp
from time import perf_counter_ns

# Third-party modules
from pydantic import BaseModel

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class ExpDecayNodeState(BaseModel):
    times: List[int] = []
    values: List[ValueType] = []


class ExpDecayNodeConfig(BaseModel):
    k: float = 1.0
    min_window: int = 1
    max_window: int = 100


class ExpDecayNode(BaseCDAGNode):
    """
    Calculate exponential decay function over window. k - decay factor
    """

    name = "expdecay"
    static_inputs = "x"
    config_cls = ExpDecayNodeConfig
    state_cls = ExpDecayNodeState
    categories = [Category.WINDOW]

    def get_value(self, x: ValueType) -> Optional[ValueType]:
        t0 = perf_counter_ns()
        self.state.values.insert(0, x)
        self.state.times.insert(0, t0)
        # Trim
        if len(self.state.values) >= self.config.max_window:
            self.state.values = self.state.values[: self.config.max_window]
            self.state.times = self.state.times[: self.config.max_window]
        # Check window is filled
        if len(self.state.values) < self.config.min_window:
            return None
        nk = -self.config.k
        return sum(v * exp(nk * (t0 - ts)) for ts, v in zip(self.state.times, self.state.values))
