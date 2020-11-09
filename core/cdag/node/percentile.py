# ----------------------------------------------------------------------
# PercentileNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List

# Third-party modules
from pydantic import BaseModel

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class PercentileNodeState(BaseModel):
    values: List[ValueType] = []


class PercentileNodeConfig(BaseModel):
    percentile: int
    min_window: int = 1
    max_window: int = 100


class PercentileNode(BaseCDAGNode):
    """
    Calculate percentile (in percents). Do not activate values until `min_window` is filled
    """

    name = "percentile"
    static_inputs = "x"
    config_cls = PercentileNodeConfig
    state_cls = PercentileNodeState
    categories = [Category.WINDOW]

    def get_value(self, x: ValueType) -> Optional[ValueType]:
        self.state.values.insert(0, x)
        # Trim
        if len(self.state.values) >= self.config.max_window:
            self.state.values = self.state.values[: self.config.max_window]
        # Check window is filled
        if len(self.state.values) < self.config.min_window:
            return None
        wl = list(sorted(self.state.values))
        i = len(wl) * self.config.percentile // 100
        return wl[i]
