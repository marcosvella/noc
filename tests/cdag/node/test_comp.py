# ----------------------------------------------------------------------
# Comparison operations test
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG


@pytest.mark.parametrize(
    "op,conf,x,y,expected",
    [
        # ==
        ("eq", {}, 0, 0, 1),
        ("eq", {}, 0, 1, 0),
        ("eq", {"true_level": 3}, 1, 1, 3),
        ("eq", {"false_level": -3}, 1, 0, -3),
        ("eq", {"epsilon": 0.01}, 1.0, 1.0, 1),
        ("eq", {"epsilon": 0.01}, 1.0, 1.001, 1),
        ("eq", {"epsilon": 0.01}, 1.0, 1.1, 0),
        #
        ("ne", {}, 0, 0, 0),
        ("ne", {}, 0, 1, 1),
        ("ne", {"false_level": -3}, 1, 1, -3),
        ("ne", {"true_level": 3}, 1, 0, 3),
        ("ne", {"epsilon": 0.01}, 1.0, 1.0, 0),
        ("ne", {"epsilon": 0.01}, 1.0, 1.001, 0),
        ("ne", {"epsilon": 0.01}, 1.0, 1.1, 1),
    ],
)
def test_comp_node(op, conf, x, y, expected):
    def cb(x):
        nonlocal _value
        _value = x

    _value = None
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", op, config=conf)
        node.subscribe(cb)
        assert node
        assert node.is_activated() is False
        assert _value is None
        node.activate_input("x", x)
        assert node.is_activated() is False
        assert _value is None
        node.activate_input("y", y)
        assert node.is_activated() is True
    if expected is None:
        assert _value is None
    else:
        assert _value == pytest.approx(expected)
