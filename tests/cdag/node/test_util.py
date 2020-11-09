# ----------------------------------------------------------------------
# Test util functions
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG


@pytest.mark.parametrize(
    "op,config,x,key,expected",
    [
        # key
        ("key", {}, 1.0, 0.0, None),
        ("key", {}, 2.0, 1.0, 2.0),
    ],
)
def test_key_node(op, config, x, key, expected):
    def cb(x):
        nonlocal _value
        _value = x

    _value = None
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", op, config=config)
        node.subscribe(cb)
        node.activate_input("key", key)
        node.activate_input("x", x)
    if expected is None:
        assert _value is None
    else:
        assert _value == pytest.approx(expected, rel=1e-4)
