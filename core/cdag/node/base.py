# ----------------------------------------------------------------------
# BaseNode
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Any, Set, Optional, Type, Dict, Union, List, Iterable, Callable, Tuple
from enum import Enum
import inspect

# Third-party modules
from pydantic import BaseModel, StrictInt, StrictFloat

ValueType = Union[int, float]
StrictValueType = Union[StrictInt, StrictFloat]


class Category(str, Enum):
    MATH = "math"
    OPERATION = "operation"
    LOGICAL = "logical"
    ACTIVATION = "activation"
    COMPARE = "compare"
    DEBUG = "debug"
    UTIL = "util"
    STATISTICS = "statistics"
    ML = "ml"
    WINDOW = "window"


class BaseCDAGNodeMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        n = type.__new__(mcs, name, bases, attrs)
        sig = inspect.signature(n.get_value)
        n.static_inputs = [x for x in sig.parameters if x != "self"]
        return n


class BaseCDAGNode(object, metaclass=BaseCDAGNodeMetaclass):
    name: str
    state_cls: Type[BaseModel]
    config_cls: Type[BaseModel]
    static_inputs: List[str]  # Filled by metaclass
    dot_shape: str = "box"
    categories: List[Category] = []

    def __init__(
        self,
        node_id: str,
        state: Optional[Dict[str, Any]] = None,
        description: str = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.description = description
        self.state = self.clean_state(state)
        self.config = self.clean_config(config)
        self._activated: bool = False
        self._inputs: Dict[str, Optional[ValueType]] = {i: None for i in self.iter_inputs()}
        self._bound_inputs: Set[str] = set()
        self._to_activate = len(self._inputs)
        self._subscribers: List[Callable[[ValueType], None]] = []
        self._value: Optional[ValueType] = None

    def clean_state(self, state: Optional[Dict[str, Any]]) -> Optional[BaseModel]:
        if not hasattr(self, "state_cls"):
            return None
        state = state or {}
        return self.state_cls(**state)

    def clean_config(self, config: Optional[Dict[str, Any]]) -> Optional[BaseModel]:
        if not hasattr(self, "config_cls"):
            return None
        return self.config_cls(**config)

    def iter_inputs(self) -> Iterable[str]:
        """
        Enumerate all configured inputs
        :return:
        """
        yield from self.static_inputs

    def is_activated(self) -> bool:
        """
        Check if all inputs is met and outputs can be activated
        :return:
        """
        return self._to_activate == 0

    def activate_input(self, name: str, value: ValueType) -> None:
        """
        Activate named input with
        :param name:
        :param value:
        :return:
        """
        if name not in self._inputs:
            raise KeyError("Invalid input: %s" % name)
        if self._inputs[name] is None:
            self._to_activate -= 1
        self._inputs[name] = value
        if self.is_activated():
            self.on_activate()

    def on_activate(self):
        """
        Perform node activation sequence. Fired when:

        * graph.activate() is called
        * all inputs are activated

        :return:
        """
        if self._activated:
            return
        self._value = self.get_value(**self._inputs)
        # Notify all subscribers
        for cb in self._subscribers:
            cb(self._value)
        self._activated = True

    def subscribe(self, callback: Callable[[ValueType], None]) -> None:
        """
        Subscribe to activation function
        :param callback:
        :return:
        """
        self._subscribers += [callback]

    def mark_as_bound(self, name: str) -> None:
        if name in self._inputs:
            self._bound_inputs.add(name)

    def get_value(self, *args, **kwargs) -> Optional[ValueType]:  # pragma: no cover
        """
        Calculate node value. Returns None when input is malformed and should not be propagated
        :return:
        """
        raise NotImplementedError

    def get_input(self, name: str) -> Optional[ValueType]:
        """
        Get activated input value
        :param name:
        :return:
        """
        return self._inputs[name]

    def get_inputs(self, names: Iterable[str]) -> Tuple[Optional[ValueType], ...]:
        """
        Return tuple of input values only when all of them are activated,
        Return tuple of None otherwise
        :param names:
        :return:
        """
        r = tuple(self._inputs[name] for name in names)
        if any(True for v in r if v is None):
            return tuple(None for _ in range(len(r)))
        return r

    def get_state(self) -> Optional[BaseModel]:
        """
        Get current node state
        :return:
        """
        return self.state

    def iter_subscribers(self) -> Iterable[Tuple["BaseCDAGNode", str]]:
        for cb in self._subscribers:
            if (
                not hasattr(cb, "func")
                or cb.func.__name__ != "activate_input"
                or not hasattr(cb.func, "__self__")
            ):
                continue  # pragma: no cover
            r_node = cb.func.__self__
            if not isinstance(r_node, BaseCDAGNode):
                continue  # pragma: no cover
            yield r_node, cb.args[0]
