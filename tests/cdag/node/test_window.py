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
    "op,config,measures,expected", []  # [("nth", {}, [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])]
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
        assert _value == exp
