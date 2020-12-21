# ----------------------------------------------------------------------
# BaseGeocoder class
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from dataclasses import dataclass, field
from typing import Any, Optional, List, Iterator

# NOC modules
from noc.core.http.client import fetch_sync
from .errors import GeoCoderError


@dataclass
class GeoCoderResult(object):
    exact: bool
    query: str
    path: List[str]
    lon: Optional[float] = None
    lat: Optional[float] = None
    id: Optional[str] = None
    address: Optional[str] = None
    scope: Optional[str] = None


class BaseGeocoder(object):
    name = None

    def __init__(self, *args, **kwargs):
        pass

    def forward(self, query: str, bounds=None) -> GeoCoderResult:
        """
        Forward lookup
        :param query: Address as string
        :type query: str
        :return: GeoCoderResult or None
        """
        try:
            return next(self.iter_query(query, bounds))
        except StopIteration:
            return None

    def iter_query(self, query: str, bounds) -> Iterator[GeoCoderResult]:
        """
        Get list of probable address candidates
        :param query:
        :return:
        """
        raise NotImplementedError()

    def get(self, url):
        """
        Perform get request
        :param url:
        :type url: str
        :return:
        """
        code, headers, body = fetch_sync(
            url, follow_redirects=True, validate_cert=False, allow_proxy=True
        )
        if 200 <= code <= 299:
            return code, body
        else:
            raise GeoCoderError("HTTP Error %s" % code)

    @staticmethod
    def get_path(data, path):
        """
        Returns nested object referred by dot-separated path, or None
        :param data:
        :param path:
        :return:
        """
        o = data
        for p in path.split("."):
            if p in o:
                o = o[p]
            else:
                return None
        return o

    @staticmethod
    def maybe_float(f: Any) -> Optional[float]:
        if isinstance(f, float):
            return f
        if f:
            return float(f)
        return None
