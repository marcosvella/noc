# ----------------------------------------------------------------------
# BaseCDAGFactory
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from ..graph import CDAG


class BaseCDAGFactory(object):
    """
    CDAG factory is responsible for computation graph construction. Factories can be chained
    together
    """

    def __init__(self, graph: CDAG):
        self.graph = graph

    def construct(self) -> None:  # pragma: no cover
        raise NotImplementedError
