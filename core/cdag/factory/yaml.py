# ----------------------------------------------------------------------
# YAMLCDAGFactory
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import yaml

# NOC modules
from .base import CDAG
from .config import ConfigCDAGFactory, NodeItem


class YAMLCDAGFactory(ConfigCDAGFactory):
    def __init__(self, graph: CDAG, config: str):
        items = [NodeItem(**i) for i in yaml.safe_load(config)]
        super().__init__(graph, items)
