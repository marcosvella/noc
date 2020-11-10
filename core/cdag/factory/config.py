# ----------------------------------------------------------------------
# ConfigCDAGFactory
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List, Dict, Any
from functools import partial

# Third-party modules
from pydantic import BaseModel

# NOC modules
from .base import BaseCDAGFactory
from ..graph import CDAG


class InputItem(BaseModel):
    name: str
    node: str


class NodeItem(BaseModel):
    name: str
    type: str
    description: Optional[str]
    config: Optional[Dict[str, Any]]
    inputs: Optional[List[InputItem]]


class ConfigCDAGFactory(BaseCDAGFactory):
    """
    Build CDAG from abstract config
    """

    def __init__(self, graph: CDAG, config: List[NodeItem]):
        super().__init__(graph)
        self.config = config

    def requirements_met(self, inputs: Optional[List[InputItem]]):
        if not inputs:
            return True
        for input in inputs:
            if input.node not in self.graph:
                return False
        return True

    def construct(self) -> None:
        for item in self.config:
            # Check for prerequisites
            if not self.requirements_met(item.inputs):
                continue
            # Create node
            node = self.graph.add_node(
                item.name, node_type=item.type, description=item.description, config=item.config
            )
            # Connect node
            if item.inputs:
                for input in item.inputs:
                    r_node = self.graph[input.node]
                    r_node.subscribe(partial(node.activate_input, input.name))
                    node.mark_as_bound(input.name)
