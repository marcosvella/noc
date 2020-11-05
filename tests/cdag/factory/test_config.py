# ----------------------------------------------------------------------
# ConfigFactory tests
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG
from noc.core.cdag.factory.config import ConfigCDAGFactory, NodeItem, InputItem

CONFIG = [
    NodeItem(name="n01", type="value", description="Value of 1", config={"value": 1.0}),
    NodeItem(name="n02", type="value", description="Value of 2", config={"value": 2.0}),
    NodeItem(
        name="n03",
        type="add",
        description="Add values",
        inputs=[InputItem(name="x", node="n01"), InputItem(name="y", node="n02")],
    ),
    NodeItem(name="n04", type="state", inputs=[InputItem(name="x", node="n03")]),
]


@pytest.mark.parametrize("config,out_state", [(CONFIG, {"n04": {"value": 3.0}})])
def test_config_factory(config, out_state):
    # Empty graph with no state
    with CDAG("test", {}) as cdag:
        # Apply config
        factory = ConfigCDAGFactory(cdag, CONFIG)
        factory.construct()
        # Check nodes
        for item in CONFIG:
            node = cdag[item.name]
            assert node
            assert node.node_id == item.name
            if item.description:
                assert node.description == item.description
    # Compare final state with expected
    assert cdag.get_state() == out_state
