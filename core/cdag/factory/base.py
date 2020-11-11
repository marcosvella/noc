# ----------------------------------------------------------------------
# BaseCDAGFactory
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Any, Optional, Dict

# NOC modules
from ..graph import CDAG

FactoryCtx = Dict[str, Any]


class BaseCDAGFactory(object):
    """
    CDAG factory is responsible for computation graph construction. Factories can be chained
    together
    """

    def __init__(self, graph: CDAG, ctx: Optional[FactoryCtx] = None):
        self.graph = graph
        self.ctx = ctx

    def construct(self) -> None:  # pragma: no cover
        raise NotImplementedError
