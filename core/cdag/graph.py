# ----------------------------------------------------------------------
# CDAG
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, Any, Dict

# NOC modules
from .node.base import BaseCDAGNode
from .node.loader import loader


class CDAG(object):
    def __init__(self, graph_id: str, state: Optional[Dict[str, Any]] = None):
        self.graph_id = graph_id
        self.state: Dict[str, Any] = state or {}
        self.nodes: Dict[str, BaseCDAGNode] = {}

    def __getitem__(self, item: str) -> BaseCDAGNode:
        return self.nodes[item]

    def add_node(
        self,
        node_id: str,
        node_type: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseCDAGNode:
        if node_id in self.state:
            raise ValueError("Node %s is already configured" % node_id)
        node_cls = loader.get_class(node_type)
        if not node_cls:
            raise ValueError("Invalid node type: %s" % node_type)
        config = config or {}
        #
        node = node_cls(
            node_id, description=description, state=self.state.get(node_id), config=config
        )
        self.nodes[node_id] = node
        return node

    def activate(self):
        """
        Activate all graph calculations
        :return:
        """
        for node in self.nodes.values():
            if node.is_activated():
                node.on_activate()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.activate()

    def get_state(self) -> Dict[str, Any]:
        """
        Construct current state
        :return:
        """
        r = {}
        for node_id, node in self.nodes.items():
            if not hasattr(node, "state_cls"):
                continue
            ns = node.get_state()
            if ns is None:
                continue
            r[node_id] = ns.dict()
        return r

    def get_dot(self) -> str:
        """
        Build graphviz dot representation for graph

        :return:
        """
        n_map: Dict[str, str] = {}
        r = ["digraph {", '  rankdir="LR";']
        # Nodes
        for n, node_id in enumerate(sorted(self.nodes)):
            dot_id = "n%05d" % n
            n_map[node_id] = dot_id
            node = self.nodes[node_id]
            n_attrs = ""
            if node.config:
                attrs = []
                for fn in node.config.__fields__:
                    v = getattr(node.config, fn)
                    if hasattr(v, "value"):
                        v = v.value
                    attrs += ["%s: %s" % (fn, v)]
                if attrs:
                    n_attrs = "\\n" + "\\n".join(attrs)
            r += [
                '  %s [label="%s\\ntype: %s%s", shape="%s"];'
                % (dot_id, node_id, node.name, n_attrs, node.dot_shape)
            ]
        # Edges
        for node in self.nodes.values():
            for r_node, in_name in node.iter_subscribers():
                r += [
                    '  %s -> %s [label="%s"];'
                    % (n_map[node.node_id], n_map[r_node.node_id], in_name)
                ]
        r += ["}"]
        return "\n".join(r)
