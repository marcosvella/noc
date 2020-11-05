# ----------------------------------------------------------------------
# Test factory chain
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG
from noc.core.cdag.factory.yaml import YAMLCDAGFactory


CONFIG1 = """
- name: n01
  description: Value of 1
  type: value
  config:
    value: 1.0
- name: n02
  type: value
  description: Value of 2
  config:
    value: 2.0
"""
CONFIG2 = """
- name: n03
  type: add
  description: Add values
  inputs:
  - name: x
    node: n01
  - name: y
    node: n02
"""
CONFIG3 = """
- name: n04
  type: state
  inputs:
  - name: x
    node: n03
"""


@pytest.mark.parametrize(
    "configs,out_state", [([CONFIG1, CONFIG2, CONFIG3], {"n04": {"value": 3.0}})]
)
def test_factory_chain(configs, out_state):
    # Empty graph with no state
    with CDAG("test", {}) as cdag:
        # Apply config
        for cfg in configs:
            factory = YAMLCDAGFactory(cdag, cfg)
            factory.construct()
    # Compare final state with expected
    assert cdag.get_state() == out_state
