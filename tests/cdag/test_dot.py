# ----------------------------------------------------------------------
# CDAG.to_dot() tests
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from noc.core.cdag.graph import CDAG
from noc.core.cdag.factory.yaml import YAMLCDAGFactory


CONFIG = """
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
- name: n03
  type: add
  description: Add values
  inputs:
  - name: x
    node: n01
  - name: y
    node: n02
- name: n04
  type: state
  inputs:
  - name: x
    node: n03
"""

DOT = r"""digraph {
  rankdir="LR";
  n00000 [label="n01\ntype: value\nvalue: 1", shape="cds"];
  n00001 [label="n02\ntype: value\nvalue: 2", shape="cds"];
  n00002 [label="n03\ntype: add", shape="box"];
  n00003 [label="n04\ntype: state", shape="doubleoctagon"];
  n00000 -> n00002 [label="x"];
  n00001 -> n00002 [label="y"];
  n00002 -> n00003 [label="x"];
}"""


def test_to_dot():
    with CDAG("test", {}) as cdag:
        # Apply config
        factory = YAMLCDAGFactory(cdag, CONFIG)
        factory.construct()
    assert cdag.get_dot() == DOT
