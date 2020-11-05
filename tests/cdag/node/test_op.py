# ----------------------------------------------------------------------
# Test OpNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG


@pytest.mark.parametrize(
    "op,x,y,expected",
    [
        # +
        ("add", 0, 0, 0),
        ("add", 1, 2, 3),
        ("add", 1.0, 2.0, 3.0),
        ("add", 1.0, 2, 3.0),
        # -
        ("sub", 0, 0, 0),
        ("sub", 2, 1, 1),
        ("sub", 1.0, 2.0, -1.0),
        ("sub", 1.0, 2, -1.0),
        # *
        ("mul", 0, 1, 0),
        ("mul", 1, 2, 2),
        ("mul", 1.0, 2.0, 2.0),
        ("mul", 1.0, 2, 2.0),
        # /
        ("div", 0, 0, None),
        ("div", 1, 0, None),
        ("div", 2, 1, 2),
        ("div", 1.0, 2.0, 0.5),
        ("div", 1.0, 2, 0.5),
    ],
)
def test_op_node(op, x, y, expected):
    def cb(x):
        nonlocal _value
        _value = x

    _value = None
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", op)
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
        assert _value == expected
