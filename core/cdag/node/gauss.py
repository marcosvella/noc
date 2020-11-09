# ----------------------------------------------------------------------
# GaussNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List

# Third-party modules
from pydantic import BaseModel
import numpy as np

# NOC modules
from .base import BaseCDAGNode, ValueType, Category


class GaussNodeState(BaseModel):
    values: List[float] = []


class GaussNodeConfig(BaseModel):
    n_sigma: float = 3.0
    min_window: int = 3
    max_window: int = 100
    true_level: ValueType = 1
    false_level: ValueType = 0
    skip_outliers: bool = True


class GaussNode(BaseCDAGNode):
    """
    Gaussian filter. Considering input values has normal distribution.
    Collect data and activate with `true_level` if |value - mean| < n_sigma * std
    """

    name = "gauss"
    static_inputs = "x"
    config_cls = GaussNodeConfig
    state_cls = GaussNodeState
    categories = [Category.ML]

    def get_value(self, x: ValueType) -> Optional[ValueType]:
        # Check window is filled
        x = float(x)
        if len(self.state.values) < self.config.min_window:
            self.state.values.insert(0, x)
            return self.config.true_level
        mean = np.mean(np.array(self.state.values))
        std = np.std(np.array(self.state.values))
        is_outlier = abs(x - mean) > self.config.n_sigma * std
        if not self.config.skip_outliers or not is_outlier:
            self.state.values.insert(0, x)
            # Trim
            if len(self.state.values) >= self.config.max_window:
                self.state.values = self.state.values[: self.config.max_window]
        return self.config.false_level if is_outlier else self.config.true_level
