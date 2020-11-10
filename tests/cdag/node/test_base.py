# ----------------------------------------------------------------------
# BaseNode tests
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG


def test_missed_activate():
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", "none")
        with pytest.raises(KeyError):
            node.activate_input("xxx", 1)


def test_get_input():
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", "add")
        assert node.get_input("x") is None
        with pytest.raises(KeyError):
            node.get_input("xxx")
        node.activate_input("x", 1)
        assert node.get_input("x") == 1


def test_get_inputs():
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", "add")
        assert node.get_inputs(["x", "y"]) == (None, None)
        node.activate_input("x", 1)
        assert node.get_inputs(["x", "y"]) == (None, None)
        node.activate_input("y", 2)
        assert node.get_inputs(["x", "y"]) == (1, 2)
