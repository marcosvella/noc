# ----------------------------------------------------------------------
# HTTP Client
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import socket
import threading
import ssl
import logging
import zlib
import time
import struct
import codecs
from urllib.parse import urlparse
import asyncio

# Third-party modules
import tornado.ioloop
from tornado.ioloop import IOLoop
import tornado.iostream
import cachetools
import ujson

# NOC modules
from noc.core.perf import metrics
from noc.core.validators import is_ipv4
from .proxy import SYSTEM_PROXIES
from noc.config import config
from noc.core.comp import smart_bytes, smart_text

from http_parser.parser import HttpParser

logger = logging.getLogger(__name__)

DEFAULT_CONNECT_TIMEOUT = config.http_client.connect_timeout
DEFAULT_REQUEST_TIMEOUT = config.http_client.request_timeout
DEFAULT_USER_AGENT = config.http_client.user_agent
DEFAULT_BUFFER_SIZE = config.http_client.buffer_size
DEFAULT_MAX_REDIRECTS = config.http_client.max_redirects

ERR_TIMEOUT = 599
ERR_READ_TIMEOUT = 598
ERR_PARSE_ERROR = 597

NS_CACHE_SIZE = config.http_client.ns_cache_size
RESOLVER_TTL = config.http_client.resolver_ttl

DEFAULT_PORTS = {"http": config.http_client.http_port, "https": config.http_client.https_port}

# Methods require Content-Length header
REQUIRE_LENGTH_METHODS = {"POST", "PUT"}

ns_lock = threading.Lock()
ns_cache = cachetools.TTLCache(NS_CACHE_SIZE, ttl=RESOLVER_TTL)

CE_DEFLATE = "deflate"
CE_GZIP = "gzip"


async def resolve(host):
    """
    Resolve host and return address
    :param host:
    :return:
    """
    with ns_lock:
        addr = ns_cache.get(host)
    if addr:
        return addr
    try:
        addr = socket.gethostbyname(host)
        with ns_lock:
            ns_cache[host] = addr
        return addr
    except socket.gaierror:
        return None


async def fetch(
    url,
    method="GET",
    headers=None,
    body=None,
    connect_timeout=DEFAULT_CONNECT_TIMEOUT,
    request_timeout=DEFAULT_REQUEST_TIMEOUT,
    resolver=resolve,
    max_buffer_size=DEFAULT_BUFFER_SIZE,
    follow_redirects=False,
    max_redirects=DEFAULT_MAX_REDIRECTS,
    validate_cert=config.http_client.validate_certs,
    allow_proxy=False,
    proxies=None,
    user=None,
    password=None,
    content_encoding=None,
    eof_mark=None,
):
    """

    :param url: Fetch URL
    :param method: request method "GET", "POST", "PUT" etc
    :param headers: Dict of additional headers
    :param body: Request body for POST and PUT request
    :param connect_timeout:
    :param request_timeout:
    :param resolver:
    :param follow_redirects:
    :param max_redirects:
    :param validate_cert:
    :param allow_proxy:
    :param proxies:
    :param user:
    :param password:
    :param max_buffer_size:
    :param content_encoding:
    :param eof_mark: Do not consider connection reset as error if
      eof_mark received (string or list)
    :return: code, headers, body
    """

    def get_ssl_options():
        ssl_options = {}
        if validate_cert:
            ssl_options["cert_reqs"] = ssl.CERT_REQUIRED
        return ssl_options

    logger.debug("HTTP %s %s", method, url)
    metrics["httpclient_requests", ("method", method.lower())] += 1
    #
    if eof_mark:
        eof_mark = smart_bytes(eof_mark)
    # Detect proxy when necessary
    u = urlparse(str(url))
    use_tls = u.scheme == "https"
    if ":" in u.netloc:
        host, port = u.netloc.rsplit(":")
        port = int(port)
    else:
        host = u.netloc
        port = DEFAULT_PORTS.get(u.scheme)
        if not port:
            return ERR_TIMEOUT, {}, "Cannot resolve port for scheme: %s" % u.scheme
    if is_ipv4(host):
        addr = host
    else:
        addr = await resolver(host)
    if not addr:
        return ERR_TIMEOUT, {}, "Cannot resolve host: %s" % host
    # Detect proxy server
    if allow_proxy:
        proxy = (proxies or SYSTEM_PROXIES).get(u.scheme)
    else:
        proxy = None
    # Connect
    stream = None
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if use_tls and not proxy:
            stream = tornado.iostream.SSLIOStream(s, ssl_options=get_ssl_options())
        else:
            stream = tornado.iostream.IOStream(s)
        try:
            if proxy:
                connect_address = proxy
            elif isinstance(addr, tuple):
                connect_address = addr
            else:
                connect_address = (addr, port)

            if proxy:
                logger.debug("Connecting to proxy %s:%s", connect_address[0], connect_address[1])
            await asyncio.wait_for(
                stream.connect(connect_address, server_hostname=u.netloc), connect_timeout
            )
        except tornado.iostream.StreamClosedError:
            # May be not relevant on Tornado6 anymore
            metrics["httpclient_timeouts"] += 1
            return ERR_TIMEOUT, {}, "Connection refused"
        except ConnectionRefusedError:
            metrics["httpclient_timeouts"] += 1
            return ERR_TIMEOUT, {}, "Connection refused"
        except asyncio.TimeoutError:
            metrics["httpclient_timeouts"] += 1
            return ERR_TIMEOUT, {}, "Connection timed out"
        # Proxy CONNECT
        if proxy:
            logger.debug("Sending CONNECT %s:%s", addr, port)
            # Send CONNECT request
            req = b"CONNECT %s:%s HTTP/1.1\r\nUser-Agent: %s\r\n\r\n" % (
                smart_bytes(addr),
                smart_bytes(port),
                smart_bytes(DEFAULT_USER_AGENT),
            )
            try:
                await asyncio.wait_for(stream.write(smart_bytes(req)), request_timeout)
            except tornado.iostream.StreamClosedError:
                metrics["httpclient_proxy_timeouts"] += 1
                return ERR_TIMEOUT, {}, "Connection reset while connecting to proxy"
            except asyncio.TimeoutError:
                metrics["httpclient_proxy_timeouts"] += 1
                return ERR_TIMEOUT, {}, "Timed out while sending request to proxy"
            # Wait for proxy response
            parser = HttpParser()
            while not parser.is_headers_complete():
                try:
                    data = await asyncio.wait_for(
                        stream.read_bytes(max_buffer_size, partial=True), request_timeout
                    )
                except tornado.iostream.StreamClosedError:
                    metrics["httpclient_proxy_timeouts"] += 1
                    return ERR_TIMEOUT, {}, "Connection reset while connecting to proxy"
                except asyncio.TimeoutError:
                    metrics["httpclient_proxy_timeouts"] += 1
                    return ERR_TIMEOUT, {}, "Timed out while sending request to proxy"
                received = len(data)
                parsed = parser.execute(data, received)
                if parsed != received:
                    return ERR_PARSE_ERROR, {}, "Parse error"
            code = parser.get_status_code()
            logger.debug("Proxy response: %s", code)
            if not 200 <= code <= 299:
                return code, parser.get_headers(), "Proxy error: %s" % code
            # Switch to TLS when necessary
            if use_tls:
                logger.debug("Starting TLS negotiation")
                try:
                    stream = await asyncio.wait_for(
                        stream.start_tls(
                            server_side=False,
                            ssl_options=get_ssl_options(),
                            server_hostname=u.netloc,
                        ),
                        request_timeout,
                    )
                except tornado.iostream.StreamClosedError:
                    metrics["httpclient_proxy_timeouts"] += 1
                    return ERR_TIMEOUT, {}, "Connection reset while connecting to proxy"
                except asyncio.TimeoutError:
                    metrics["httpclient_proxy_timeouts"] += 1
                    return ERR_TIMEOUT, {}, "Timed out while sending request to proxy"
        # Process request
        body = body or ""
        content_type = "application/binary"
        if not isinstance(body, (str, bytes)):
            body = ujson.dumps(body)
            content_type = "text/json"
        body = smart_bytes(body)  # Here and below body is binary
        h = {"Host": str(u.netloc), "Connection": "close", "User-Agent": DEFAULT_USER_AGENT}
        if body and content_encoding:
            if content_encoding == CE_DEFLATE:
                # Deflate compression
                h["Content-Encoding"] = CE_DEFLATE
                compress = zlib.compressobj(
                    zlib.Z_DEFAULT_COMPRESSION,
                    zlib.DEFLATED,
                    -zlib.MAX_WBITS,
                    zlib.DEF_MEM_LEVEL,
                    zlib.Z_DEFAULT_STRATEGY,
                )
                body = compress.compress(body) + compress.flush()
            elif content_encoding == CE_GZIP:
                # gzip compression
                h["Content-Encoding"] = CE_GZIP
                compress = zlib.compressobj(
                    6, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0
                )
                crc = zlib.crc32(body, 0) & 0xFFFFFFFF
                body = "\x1f\x8b\x08\x00%s\x02\xff%s%s%s%s" % (
                    to32u(int(time.time())),
                    compress.compress(body),
                    compress.flush(),
                    to32u(crc),
                    to32u(len(body)),
                )
        if method in REQUIRE_LENGTH_METHODS:
            h["Content-Length"] = str(len(body))
            h["Content-Type"] = content_type
        if user and password:
            # Include basic auth header
            uh = smart_text("%s:%s" % (user, password))
            h["Authorization"] = b"Basic %s" % codecs.encode(uh.encode("utf-8"), "base64").strip()
        if headers:
            h.update(headers)
        path = u.path
        if u.query:
            path += "?%s" % u.query
        req = b"%s %s HTTP/1.1\r\n%s\r\n\r\n%s" % (
            smart_bytes(method),
            smart_bytes(path),
            b"\r\n".join(b"%s: %s" % (smart_bytes(k), smart_bytes(h[k])) for k in h),
            body,
        )
        try:
            await asyncio.wait_for(stream.write(req), request_timeout)
        except tornado.iostream.StreamClosedError:
            metrics["httpclient_timeouts"] += 1
            return ERR_TIMEOUT, {}, "Connection reset while sending request"
        except asyncio.TimeoutError:
            metrics["httpclient_timeouts"] += 1
            return ERR_TIMEOUT, {}, "Timed out while sending request"
        parser = HttpParser()
        response_body = []
        while not parser.is_message_complete():
            try:
                data = await asyncio.wait_for(
                    stream.read_bytes(max_buffer_size, partial=True), request_timeout
                )
            except tornado.iostream.StreamClosedError:
                if eof_mark and response_body:
                    # Check if EOF mark is in received data
                    response_body = [b"".join(response_body)]
                    if isinstance(eof_mark, str):
                        if eof_mark in response_body[0]:
                            break
                    else:
                        found = False
                        for m in eof_mark:
                            if m in response_body[0]:
                                found = True
                                break
                        if found:
                            break
                metrics["httpclient_timeouts"] += 1
                return ERR_READ_TIMEOUT, {}, "Connection reset"
            except asyncio.TimeoutError:
                metrics["httpclient_timeouts"] += 1
                return ERR_READ_TIMEOUT, {}, "Request timed out"
            received = len(data)
            parsed = parser.execute(data, received)
            if parsed != received:
                return ERR_PARSE_ERROR, {}, "Parse error"
            if parser.is_partial_body():
                response_body += [parser.recv_body()]
        code = parser.get_status_code()
        parsed_headers = parser.get_headers()
        logger.debug("HTTP Response %s", code)
        if 300 <= code <= 399 and follow_redirects:
            # Process redirects
            if max_redirects > 0:
                new_url = parsed_headers.get("Location")
                if not new_url:
                    return ERR_PARSE_ERROR, {}, "No Location header"
                logger.debug("HTTP redirect %s %s", code, new_url)
                code, parsed_headers, response_body = await fetch(
                    new_url,
                    method="GET",
                    headers=headers,
                    connect_timeout=connect_timeout,
                    request_timeout=request_timeout,
                    resolver=resolver,
                    max_buffer_size=max_buffer_size,
                    follow_redirects=follow_redirects,
                    max_redirects=max_redirects - 1,
                    validate_cert=validate_cert,
                    allow_proxy=allow_proxy,
                    proxies=proxies,
                )
                return code, parsed_headers, response_body
            else:
                return 404, {}, "Redirect limit exceeded"
        # @todo: Process gzip and deflate Content-Encoding
        return code, parsed_headers, b"".join(response_body)
    finally:
        if stream:
            stream.close()
        else:
            s.close()


def fetch_sync(
    url,
    method="GET",
    headers=None,
    body=None,
    connect_timeout=DEFAULT_CONNECT_TIMEOUT,
    request_timeout=DEFAULT_REQUEST_TIMEOUT,
    resolver=resolve,
    max_buffer_size=DEFAULT_BUFFER_SIZE,
    follow_redirects=False,
    max_redirects=DEFAULT_MAX_REDIRECTS,
    validate_cert=config.http_client.validate_certs,
    allow_proxy=False,
    proxies=None,
    user=None,
    password=None,
    content_encoding=None,
    eof_mark=None,
):
    async def _fetch():
        result = await fetch(
            url,
            method=method,
            headers=headers,
            body=body,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            resolver=resolver,
            max_buffer_size=max_buffer_size,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
            validate_cert=validate_cert,
            allow_proxy=allow_proxy,
            proxies=proxies,
            user=user,
            password=password,
            content_encoding=content_encoding,
            eof_mark=eof_mark,
        )
        r.append(result)

    r = []
    # Should be another IOLoop instance instance
    IOLoop().run_sync(_fetch)
    return r[0]


def to32u(n):
    return struct.pack("<L", n)
