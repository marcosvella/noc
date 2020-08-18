# ----------------------------------------------------------------------
# Run tests over tests/confdb/profiles
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import os

# Third-party modules
import pytest
import yaml

# NOC modules
from noc.core.handler import get_handler
from noc.core.profile.loader import loader as profile_loader
from noc.core.confdb.tokenizer.loader import loader as tokenizer_loader


PREFIX = ("tests", "confdb", "profiles")


def iter_test_paths():
    for root, dirs, files in os.walk(os.path.join(*PREFIX)):
        prefix = tuple(root.split(os.sep)[3:])
        for f in files:
            if f.startswith(".") or not f.endswith(".yml"):
                continue
            path = prefix + (f,)
            yield os.path.join(*path)


@pytest.mark.parametrize("path", list(iter_test_paths()))
def test_profile(path):
    # Open YAML
    full_path = PREFIX + (path,)
    with open(os.path.join(*full_path)) as f:
        test = yaml.safe_load(f.read())
    # Check test format
    assert "config" in test, "Test must have 'config' section"
    assert test["config"], "Config section must be non-empty"
    assert "result" in test, "Test must have 'result' section"
    assert test["result"], "Result section must be non-empty"
    assert isinstance(test["result"], list), "Result section must be list"
    # Load profile
    profile_name = ".".join(path.split(os.sep)[:2])
    profile = profile_loader.get_profile(profile_name)
    assert profile, "Invalid profile '%s'" % profile_name
    # @todo: Create mock ManagedObject
    # Setup tokenizer
    tokenizer_name, tokenizer_conf = profile.get_config_tokenizer(None)
    tokenizer_cls = tokenizer_loader.get_class(tokenizer_name)
    assert tokenizer_cls, "Tokenizer not found"
    tokenizer = tokenizer_cls(test["config"], **tokenizer_conf)
    # Setup normalizer
    normalizer_name, normalizer_conf = profile.get_config_normalizer(None)
    if not normalizer_name.startswith("noc."):
        normalizer_name = "noc.sa.profiles.%s.confdb.normalizer.%s" % (
            profile.name,
            normalizer_name,
        )
    normalizer_cls = get_handler(normalizer_name)
    assert normalizer_cls, "Normalizer not found"
    normalizer = normalizer_cls(None, tokenizer, **normalizer_conf)
    # Check result
    result = list(normalizer)
    expected = [tuple(x) for x in test["result"]]
    assert result == expected
