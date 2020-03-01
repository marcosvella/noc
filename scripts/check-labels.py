#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Check gitlab MR labels
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
from __future__ import print_function
import os
import sys
import argparse
import time
from xml.sax.saxutils import escape


ENV_LABELS = "CI_MERGE_REQUEST_LABELS"
ENV_CI = "CI"
ERR_OK = 0
ERR_FAIL = 1


JUNIT_CLASS_NAME = "scripts.check_labels"
JUNIT_FILE = escape(sys.argv[0])


class FatalError(Exception):
    pass


class TestCase(object):
    def __init__(self, name=None, path=None, fatal=False, ref=None):
        self.name = name
        self.path = path
        self.fatal = fatal
        self.start = None
        self.stop = None
        self.failure = None
        self.ref = ref

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop = time.time()
        if exc_type is None:
            return
        self.failure = str(exc_val)
        if exc_type is AssertionError:
            if self.ref:
                self.failure += (
                    "\nRefer to https://docs.getnoc.com/master/en/go.html#%s for details."
                    % self.ref
                )
            if self.fatal:
                raise FatalError
            return True

    @property
    def is_failed(self):
        return bool(self.failure)

    def to_junit_xml(self):
        duration = self.stop - self.start
        if self.path:
            test_name = "%s[%s]" % (self.name, self.path)
        else:
            test_name = self.name
        r = [
            '  <testcase classname="%s" file="%s" line="1" '
            'name="%s" '
            'time="%.3f">' % (JUNIT_CLASS_NAME, JUNIT_FILE, test_name, duration),
        ]
        if self.is_failed:
            r += ['    <failure message="%s"></failure>' % (escape(self.failure))]
        r += [
            "  </testcase>",
        ]
        return "\n".join(r)


class TestSuite(object):
    PRI_LABELS = ["pri::p1", "pri::p2", "pri::p3", "pri::p4"]
    COMP_LABELS = ["comp::trivial", "comp::low", "comp::medium", "comp::high"]
    KIND_LABELS = ["kind::feature", "kind::improvement", "kind::bug", "kind::cleanup"]
    BACKPORT = "backport"

    def __init__(self, files):
        self.files = files
        self.tests = []
        self.start = None
        self.stop = None
        self._is_failed = None
        self._labels = None

    def to_junit_xml(self):
        pass

    def test(self, name, path=None, fatal=False, ref=None):
        t = TestCase(name=name, path=path, fatal=fatal, ref=ref)
        self.tests += [t]
        return t

    def check(self):
        self.start = time.time()
        try:
            self.do_check()
        except FatalError:
            pass
        self.stop = time.time()

    def do_check(self):
        self.check_env_labels()
        self.check_required_scoped_labels()
        self.check_backport_label()
        self.check_affected()

    @property
    def is_failed(self):
        if self._is_failed is None:
            self._is_failed = any(t for t in self.tests if t.is_failed)
        return self._is_failed

    def report(self):
        print("\n\n".join(t.failure for t in self.tests if t.is_failed))

    def report_junit(self, path):
        duration = self.stop - self.start
        n_tests = len(self.tests)
        n_failures = sum(1 for t in self.tests if t.is_failed)
        r = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<testsuite errors="0" failures="%d" name="check-labels" skipped="0" tests="%d" time="%.3f">'
            % (n_failures, n_tests, duration),
        ]
        for t in self.tests:
            r += [t.to_junit_xml()]
        r += ["</testsuite>"]
        report = "\n".join(r)
        # Write report
        rdir = os.path.dirname(path)
        if not os.path.exists(rdir):
            os.makedirs(rdir)
        with open(path, "w") as f:
            f.write(report)
        print(os.path.dirname(path))

    @property
    def labels(self):
        if self._labels is None:
            self._labels = os.environ.get(ENV_LABELS, "").split(",")
        return self._labels

    def check_env_labels(self):
        """
        Check ENV_LABELS is exit
        :return:
        """
        with self.test("test_env_labels", fatal=True):
            assert ENV_LABELS in os.environ or ENV_CI in os.environ, (
                "%s environment variable is not defined. Must be called within Gitlab CI"
                % ENV_LABELS
            )

    def check_backport_label(self):
        with self.test("test_backport"):
            if self.BACKPORT not in self.labels:
                return
            kind = [x for x in self.labels if x.startswith("kind::")]
            for label in kind:
                assert label == "kind::bug", (
                    "'%s' cannot be used with '%s'.\n Use only with 'kind::bug'"
                    % (self.BACKPORT, label)
                )

    def check_required_scoped_labels(self):
        def test_required(label, choices):
            prefix = "%s::" % label
            seen_labels = [x for x in self.labels if x.startswith(prefix)]
            n_labels = len(seen_labels)
            # Check label is exists
            with self.test("test_%s_label_set" % label, ref="dev-mr-labels-%s" % label):
                assert n_labels > 0, "'%s::*' label is not set. Must be one of %s." % (
                    label,
                    ", ".join(choices),
                )
            # Check label is defined only once
            with self.test("test_%s_label_single" % label, ref="dev-mr-labels-%s" % label):
                assert n_labels < 2, "Multiple '%s::*' labels defined. Must be exactly one." % label
            # Check label is known one
            with self.test("test_%s_known" % label, ref="dev-mr-labels-%s" % label):
                for x in seen_labels:
                    assert x in choices, "Invalid label '%s'. Must be one of %s." % (
                        x,
                        ", ".join(choices),
                    )

        test_required("pri", self.PRI_LABELS)
        test_required("comp", self.COMP_LABELS)
        test_required("kind", self.KIND_LABELS)

    def check_affected(self):
        def test_affected(label, checker):
            with self.test("test_%s" % label, ref="dev-mr-labels-affected"):
                has_changed = any(1 for p in file_parts if checker(p))
                if has_changed:
                    assert label in self.labels, "'%s' label is not set." % label
                else:
                    assert label not in self.labels, "'%s' label must not be set." % label

        file_parts = [f.split(os.sep) for f in self.files]
        test_affected("core", lambda x: x[0] == "core")
        test_affected("confdb", lambda x: x[:3] == ["core", "confdb", "syntax"])
        test_affected("documentation", lambda x: x[0] == "docs")
        test_affected("ui", lambda x: x[0] == "ui")
        test_affected("profiles", lambda x: x[:2] == ["sa", "profiles"])
        test_affected("migration", lambda x: len(x) > 2 and x[1] == "migration")
        test_affected("tests", lambda x: x[0] == "tests")
        test_affected("nbi", lambda x: x[:3] == ["services", "nbi", "api"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit-report", help="Write JUnit XML report to file")
    parser.add_argument("files", nargs="*", help="List of affected files")
    args = parser.parse_args()
    suite = TestSuite(args.files)
    suite.check()
    if suite.is_failed:
        suite.report()
    if args.junit_report:
        suite.report_junit(args.junit_report)
    sys.exit(ERR_FAIL if suite.is_failed else ERR_OK)


if __name__ == "__main__":
    main()
