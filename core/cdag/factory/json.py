# ----------------------------------------------------------------------
# JSONCDAGFactory
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import orjson

# NOC modules
from .base import CDAG
from .config import ConfigCDAGFactory, NodeItem


class JSONCDAGFactory(ConfigCDAGFactory):
    def __init__(self, graph: CDAG, config: str):
        items = [NodeItem(**i) for i in orjson.loads(config)]
        super().__init__(graph, items)
