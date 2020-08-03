# ----------------------------------------------------------------------
# Data Extractor
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import logging
import gzip
import os
import csv
import itertools
import io
from time import perf_counter
import contextlib
from typing import Any, List
import dataclass

# NOC modules
from noc.core.log import PrefixLoggerAdapter
from noc.config import config
from noc.core.comp import smart_text

logger = logging.getLogger(__name__)


@dataclass.dataclass
class Problem(object):
    line: int
    is_rej = bool
    p_class: str
    message: str
    row: List[Any]


class BaseExtractor(object):
    """
    Data extractor interface. Subclasses must provide
    *iter_data* method
    """

    name = None
    PREFIX = config.path.etl_import
    REPORT_INTERVAL = 1000
    # List of rows to be used as constant data
    data = []
    # Suppress deduplication message
    suppress_deduplication_log = False

    def __init__(self, system):
        self.system = system
        self.config = system.config
        self.logger = PrefixLoggerAdapter(logger, "%s][%s" % (system.name, self.name))
        self.import_dir = os.path.join(self.PREFIX, system.name, self.name)
        self.fatal_problems: List[Problem] = []
        self.quality_problems: List[Problem] = []

    def register_quality_problem(self, line: int, p_class: str, message: str, row: List[Any]):
        self.quality_problems += [
            Problem(line=line + 1, is_rej=False, p_class=p_class, message=message, row=row)
        ]

    def register_fatal_problem(self, line: int, p_class: str, message: str, row: List[Any]):
        self.fatal_problems += [
            Problem(line=line + 1, is_rej=True, p_class=p_class, message=message, row=row)
        ]

    def open_compressed_file(self, path: str, mode: str) -> io.TextIOWrapper:
        path = path + ".gz"
        return io.TextIOWrapper(gzip.GzipFile(path, mode))

    def ensure_import_dir(self):
        """
        Ensure import directory is exists
        :return:
        """
        if os.path.isdir(self.import_dir):
            return
        self.logger.info("Creating directory %s", self.import_dir)
        os.makedirs(self.import_dir)

    def get_new_state(self) -> io.TextIOWrapper:
        self.ensure_import_dir()
        path = os.path.join(self.import_dir, "import.csv")
        self.logger.info("Writing to %s", path)
        return self.open_compressed_file(path, "w")

    @contextlib.contextmanager
    def with_new_state(self):
        """
        New state context manager. Usage::

        with e.with_new_state() as f:
            ...

        :return:
        """
        f = self.get_new_state()
        try:
            yield f
        finally:
            f.close()

    def get_problem_file(self) -> io.TextIOWrapper:
        self.ensure_import_dir()
        path = os.path.join(self.import_dir, "import.csv.rej")
        self.logger.info("Writing to %s", path)
        return self.open_compressed_file(path, "w")

    @contextlib.contextmanager
    def with_problem_file(self):
        """
        New state context manager. Usage::

        with e.with_problem_file() as f:
            ...

        :return:
        """
        f = self.get_problem_file()
        try:
            yield f
        finally:
            f.close()

    def iter_data(self):
        yield from self.data

    def filter(self, row):
        return True

    def clean(self, row):
        return row

    def extract(self):
        def q(s):
            if s == "" or s is None:
                return ""
            elif isinstance(s, str):
                return smart_text(s)
            else:
                return str(s)

        # Fetch data
        self.logger.info("Extracting %s from %s", self.name, self.system.name)
        t0 = perf_counter()
        data = []
        n = 0
        seen = set()
        for row in self.iter_data():
            if not self.filter(row):
                continue
            row = self.clean(row)
            if row[0] in seen:
                if not self.suppress_deduplication_log:
                    self.logger.error("Duplicated row truncated: %r", row)
                continue
            else:
                seen.add(row[0])
            data += [[q(x) for x in row]]
            n += 1
            if n % self.REPORT_INTERVAL == 0:
                self.logger.info("   ... %d records", n)
        dt = perf_counter() - t0
        speed = n / dt
        self.logger.info("%d records extracted in %.2fs (%d records/s)", n, dt, speed)
        # Sort
        data.sort()
        # Write
        with self.with_new_state() as f:
            writer = csv.writer(f)
            writer.writerows(data)
        if self.fatal_problems or self.quality_problems:
            self.logger.warning(
                "Detect problems on extracting, fatal: %d, quality: %d",
                len(self.fatal_problems),
                len(self.quality_problems),
            )
            self.logger.warning("Line num\tType\tProblem string")
            for p in self.fatal_problems:
                self.logger.warning(
                    "Fatal problem, line was rejected: %s\t%s\t%s" % (p.line, p.p_class, p.message)
                )
            for p in self.quality_problems:
                self.logger.warning(
                    "Data quality problem in line:  %s\t%s\t%s" % (p.line, p.p_class, p.message)
                )
            # Dump problem to file
            try:
                with self.with_problem_file() as f:
                    writer = csv.writer(f, delimiter=";")
                    for p in itertools.chain(self.quality_problems, self.fatal_problems):
                        writer.writerow(
                            [smart_text(c) for c in p.row]
                            + [
                                "Fatal problem, line was rejected"
                                if p.is_rej
                                else "Data quality problem"
                            ]
                            + [p.message.encode("utf-8")]
                        )
            except IOError as e:
                self.logger.error("Error when saved problems %s", e)
        else:
            self.logger.info("No problems detected")
