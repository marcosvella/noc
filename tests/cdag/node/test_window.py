# ----------------------------------------------------------------------
# Test WindowNode
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
        # nth
        ("nth", {}, [1, 2, 3, 4, 5], [None, 1, 2, 3, 4]),
        ("nth", {"n": 0}, [1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
        ("nth", {"n": 1}, [1, 2, 3, 4, 5], [None, 1, 2, 3, 4]),
        ("nth", {"n": 3}, [1, 2, 3, 4, 5], [None, None, None, 1, 2]),
        # percentile
        ("percentile", {"percentile": 50, "min_window": 0}, [1, 2, 3, 4, 5, 6], [1, 2, 2, 3, 3, 4]),
        (
            "percentile",
            {"percentile": 50, "min_window": 3},
            [1, 2, 3, 4, 5, 6],
            [None, None, 2, 3, 3, 4],
        ),
        # sumstep
        ("sumstep", {"direction": "inc"}, [1, 2, -1, 1, -1, 1], [None, 1, 1, 3, 3, 5]),
        (
            "sumstep",
            {"direction": "inc", "min_window": 3},
            [1, 2, -1, 1, -1, 1],
            [None, None, 1, 3, 3, 5],
        ),
        ("sumstep", {"direction": "dec"}, [1, 2, -1, 1, -1, 1], [None, 0, 3, 3, 5, 5]),
        ("sumstep", {"direction": "abs"}, [1, 2, -1, 1, -1, 1], [None, 1, 4, 6, 8, 10]),
    ],
)
def test_window_node(op, config, measures, expected):
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
            assert _value is exp
        else:
            assert _value == exp
