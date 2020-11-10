# ----------------------------------------------------------------------
# Test ML functions
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG


@pytest.mark.parametrize(
    "op,config,measures,expected",
    [
        # gauss
        (
            "gauss",
            {"min_window": 3},
            [1.0, 1.0, 1.0, 1.0, 0.2, 1.0],
            [1.0, 1.0, 1.0, 1.0, 0.0, 1.0],
        ),
        (
            "gauss",
            {"min_window": 3, "true_level": 0.0, "false_level": 1.0},
            [1.0, 1.0, 1.0, 1.0, 0.2, 1.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ),
        (
            "gauss",
            {"min_window": 3},
            [1.0, 1.1, 0.9, 1.1, 0.2, 1.0],
            [1.0, 1.0, 1.0, 1.0, 0.0, 1.0],
        ),
    ],
)
def test_ml_node(op, config, measures, expected):
    def cb(x):
        nonlocal _value
        _value = x

    state = {}
    for ms, exp in zip(measures, expected):
        _value = None
        with CDAG("test", state) as cdag:
            node = cdag.add_node("n01", op, config=config)
            node.subscribe(cb)
            node.activate_input("x", ms)
        # Pass the state back
        state = cdag.get_state()
        if exp is None:
            assert _value is None
        else:
            assert _value == pytest.approx(exp)
