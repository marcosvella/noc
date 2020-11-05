# ----------------------------------------------------------------------
# Test StateNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG


@pytest.mark.parametrize("value", [1, 1.0, 5])
def test_state_node(value):
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", "state")
        node.activate_input("x", value)
    state = node.get_state()
    assert state.value == value
