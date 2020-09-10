# ----------------------------------------------------------------------
# OSM Nominatim Geocoder
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from urllib.parse import quote as urllib_quote

# Third-party modules
import orjson

# NOC modules
from .base import BaseGeocoder, GeoCoderResult
from .errors import GeoCoderError


class OSMNominatimGeocoder(BaseGeocoder):
    name = "osm"

    def forward(self, query, bounds=None, region=None):
        url = (
            "http://nominatim.openstreetmap.org/search?q=%s&format=json&addressdetails=1"
            % urllib_quote(query)
        )
        if bounds:
            url += "viewbox=%s,%s" % bounds
        code, response = self.get("".join(url))
        if code != 200:
            raise GeoCoderError("%s: %s" % (code, response))
        try:
            r = orjson.loads(response)
        except ValueError:
            raise GeoCoderError("Cannot decode result")
        return GeoCoderResult(exact=False, query=query, path=[], lon=r[0]["lon"], lat=r[0]["lat"])
