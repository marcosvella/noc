# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Crypto-related snippets
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import random
import hashlib

# Third-party modules
from typing import Optional

# NOC modules
from noc.core.comp import smart_bytes, bord, bchr, make_bytes

# Symbols used in salt
ITOA64 = b"./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
SALT_SYMBOLS = list(ITOA64)
REARRANGED_BITS = ((0, 6, 12), (1, 7, 13), (2, 8, 14), (3, 9, 15), (4, 10, 5))


def gen_salt(salt_len):
    """
    Generate random salt of given length
    >>> len(gen_salt(10)) == 10
    True
    """
    return make_bytes([random.choice(SALT_SYMBOLS) for _ in range(salt_len)])


def md5crypt(password: bytes, salt: Optional[bytes] = None, magic: bytes = b"$1$") -> bytes:
    """
    MD5 password hash
    (Used for RIPE authentication)
    >>> md5crypt("test", salt="1234")
    '$1$1234$InX9CGnHSFgHD3OZHTyt3.'
    >>> md5crypt("test", salt="1234")
    '$1$1234$InX9CGnHSFgHD3OZHTyt3.'
    >>> md5crypt("test", salt="1234", magic="$5$")
    '$5$1234$x29w4cwzSDnesjss/m2O1.'
    """
    password = smart_bytes(password)
    magic = smart_bytes(magic)
    salt = smart_bytes(salt) if salt else gen_salt(8)
    # /* The password first, since that is what is most unknown */ /* Then our magic string */ /* Then the raw salt */
    m = hashlib.md5(smart_bytes(password + magic + salt))
    # /* Then just as many characters of the MD5(pw,salt,pw) */
    mixin = hashlib.md5(smart_bytes(password + salt + password)).digest()
    for i in range(len(password)):
        m.update(bchr(mixin[i % 16]))
    # /* Then something really weird... */
    # Also really broken, as far as I can tell.  -m
    i = len(password)
    while i:
        if i & 1:
            m.update(b"\x00")
        else:
            m.update(bchr(password[0]))
        i >>= 1
    final = m.digest()
    # /* and now, just to make sure things don't run too fast */
    for i in range(1000):
        m2 = hashlib.md5()
        if i & 1:
            m2.update(smart_bytes(password))
        else:
            m2.update(smart_bytes(final))
        if i % 3:
            m2.update(smart_bytes(salt))
        if i % 7:
            m2.update(smart_bytes(password))
        if i & 1:
            m2.update(smart_bytes(final))
        else:
            m2.update(smart_bytes(password))
        final = m2.digest()
    # This is the bit that uses to64() in the original code.
    rearranged = []
    for a, b, c in REARRANGED_BITS:
        v = bord(final[a]) << 16 | bord(final[b]) << 8 | bord(final[c])
        for i in range(4):
            rearranged += [ITOA64[v & 0x3F]]
            v >>= 6
    v = bord(final[11])
    for i in range(2):
        rearranged += [ITOA64[v & 0x3F]]
        v >>= 6
    return magic + salt + b"$" + make_bytes(rearranged)
