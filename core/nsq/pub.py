# ----------------------------------------------------------------------
# Simple HTTP client for NSQ pub/mpub
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import logging
import struct
import random

# Third-party modules
import ujson
import tornado.gen
from typing import List, Any

# NOC modules
from noc.core.http.client import fetch_sync, fetch
from noc.core.dcs.loader import get_dcs
from noc.config import config
from noc.core.perf import metrics
from noc.core.comp import smart_bytes
from .error import NSQPubError

nsqd_http_service_param = config.nsqd.__dict__["http_addresses"]
logger = logging.getLogger(__name__)


def nsq_pub(topic, message):
    """
    Publish message to NSQ topic

    :param topic: NSQ topic name
    :param message: Raw message (Converted to JSON if is not a string)
    :return:
    """
    if not isinstance(message, str):
        message = ujson.dumps(message)
    # Resolve NSQd or wait
    si = config.nsqd.http_addresses[0]
    # Post message
    code, _, body = fetch_sync(
        "http://%s:%s/pub?topic=%s" % (si.host, si.port, topic), method="POST", body=message
    )
    if code != 200:
        raise NSQPubError("NSQ Pub error: code=%s message=%s" % (code, body))


def mpub_encode(messages: List[Any]) -> bytes:
    """
    Build mpub binary message
    :param messages: List of messages
    :return: Serialized message body
    """

    def iter_msg():
        # Amount of messages in pack
        yield struct.pack("!i", len(messages))
        for msg in messages:
            if not isinstance(msg, str):
                msg = ujson.dumps(msg)
            if isinstance(msg, str):
                msg = smart_bytes(msg)
            yield struct.pack("!i", len(msg))
            yield msg

    if not messages:
        return b""
    return b"".join(iter_msg())


async def mpub(topic, messages, dcs=None, retries=None):
    """
    Asynchronously publish message to NSQ topic

    :param topic: NSQ topic
    :param messages: List of strings containing messages
    :param dcs: DSC instance
    :param retries: Error retries. config.nsqd.pub_retries by default
    :return: None
    :raises NSQPubError: On publish error
    """
    if not messages:
        return
    if not dcs:
        # No global DCS, instantiate one
        dcs = get_dcs()
    # Build body
    msg = mpub_encode(messages)
    # Setup resolver
    services = nsqd_http_service_param.services
    num_services = len(services)
    if num_services > 1:
        s_index = random.randint(0, num_services - 1)
    else:
        s_index = 0
    # Post message
    retries = retries or config.nsqd.pub_retries
    code = 200
    body = None
    metrics["nsq_mpub", ("topic", topic)] += 1
    while retries > 0:
        # Get actual nsqd service's address and port
        si = services[s_index]
        if not nsqd_http_service_param.is_static(si):
            si = await dcs.resolve(si, near=True)
        # Send message
        code, _, body = await fetch(
            "http://%s/mpub?topic=%s&binary=true" % (si, topic),
            method="POST",
            body=msg,
            connect_timeout=config.nsqd.connect_timeout,
            request_timeout=config.nsqd.request_timeout,
        )
        if code == 200:
            break
        metrics["nsq_mpub_error", ("topic", topic)] += 1
        logger.error("Failed to pub to topic '%s': %s (Code=%d)", topic, body, code)
        retries -= 1
        if retries > 0:
            await tornado.gen.sleep(config.nsqd.pub_retry_delay)
            s_index = (s_index + 1) % num_services
    if code != 200:
        logger.error("Failed to pub to topic '%s'. Giving up", topic)
        metrics["nsq_mpub_fail", ("topic", topic)] += 1
        raise NSQPubError("NSQ Pub error: code=%s message=%s" % (code, body))
