# ----------------------------------------------------------------------
# Activation functions test
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import pytest

# NOC modules
from noc.core.cdag.graph import CDAG


@pytest.mark.parametrize(
    "fn,config,x,expected",
    [
        # Indicator
        ("indicator", {}, -1, 0),
        ("indicator", {}, 0, 1),
        ("indicator", {}, 1, 1),
        ("indicator", {"false_level": -3}, -1, -3),
        ("indicator", {"true_level": 3}, 1, 3),
        # Logistic
        ("logistic", {}, -1, 0.2689414213699951),
        ("logistic", {}, -1.0, 0.2689414213699951),
        ("logistic", {}, 0, 0.5),
        ("logistic", {}, 0.0, 0.5),
        ("logistic", {}, 1, 0.7310585786300049),
        ("logistic", {}, 1.0, 0.7310585786300049),
        # ReLU
        ("relu", {}, -1, 0),
        ("relu", {}, -1.0, 0.0),
        ("relu", {}, 0, 0),
        ("relu", {}, 1, 1),
        ("relu", {}, 1.0, 1.0),
        ("relu", {}, 2.0, 2.0),
        # Softplus
        ("softplus", {}, -1.0, 0.31326168751822286),
        ("softplus", {}, 0.0, 0.6931471805599453),
        ("softplus", {}, 1.0, 1.3132616875182228),
        ("softplus", {}, 2.0, 2.1269280110429727),
        ("softplus", {"k": 2}, -1.0, 0.0634640055214863),
        ("softplus", {"k": 2}, 0.0, 0.34657359027997264),
        ("softplus", {"k": 2}, 1.0, 1.0634640055214863),
        ("softplus", {"k": 2}, 2.0, 2.0090749639589047),
        ("softplus", {"k": 0}, -1.0, None),
    ],
)
def test_activation_node(fn, config, x, expected):
    def cb(x):
        nonlocal _value
        _value = x

    _value = None
    with CDAG("test", {}) as cdag:
        node = cdag.add_node("n01", fn, config=config)
        node.subscribe(cb)
        assert node
        assert node.is_activated() is False
        assert _value is None
        node.activate_input("x", x)
        assert node.is_activated() is True
    if expected is None:
        assert _value is None
    else:
        assert _value == pytest.approx(expected, rel=1e-4)
