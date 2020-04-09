# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Base classes for geocoding parsers
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import itertools

# Thirs-party modules
from six.moves import zip


class GeocodingParser(object):
    ID_ADDR = None

    def __init__(self):
        pass

    def parse(self, f):
        pass

    def feed_building(self, b_id, addr, coords):
        print("BUILDING(%s=%s)" % (self.ID_ADDR, b_id), addr, coords)

    def get_centroid(self, points):
        """
        Calculate coordinates by center of mass
        """
        A = 0.0
        Cx = 0.0
        Cy = 0.0
        a, b = itertools.tee(points)
        next(b, None)
        for (xi, yi), (xii, yii) in zip(a, b):
            d = xi * yii - xii * yi
            A += d
            Cx += (xi + xii) * d
            Cy += (yi + yii) * d
        return Cx / (3 * A), Cy / (3 * A)
