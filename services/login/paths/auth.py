# ----------------------------------------------------------------------
# /api/auth/auth/ handler
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import logging
from typing import Optional, Tuple
import codecs

# Third-party modules
from fastapi import APIRouter, Request, Cookie, Header
from fastapi.responses import ORJSONResponse
import cachetools

# NOC modules
from noc.config import config
from noc.aaa.models.apikey import APIKey
from noc.core.comp import smart_text, smart_bytes
from ..auth import authenticate, set_jwt_cookie, get_user_from_jwt

router = APIRouter()
logger = logging.getLogger(__name__)

PINHOLE_PATHS = {"/api/login/login", "/api/login/is_logged", "/api/login/token"}


@router.get("/api/auth/auth/", tags=["login"])
@router.get("/api/login/auth/", tags=["login"])
async def auth(
    request: Request,
    jwt_cookie: Optional[str] = Cookie(None, alias=config.login.jwt_cookie_name),
    private_token: Optional[str] = Header(None, alias="Private-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    original_uri: Optional[str] = Header(None, alias="X-Original-URI"),
):
    """
    Authenticate request. Called via nginx's auth_proxy
    """
    if original_uri and original_uri in PINHOLE_PATHS:
        # Pinholes to endpoints without authorization
        return ORJSONResponse({"status": True}, status_code=200)
    if jwt_cookie:
        return await auth_cookie(request=request, jwt_cookie=jwt_cookie)
    if private_token:
        return await auth_private_token(request=request, private_token=private_token)
    if authorization:
        return await auth_authorization(request=request, authorization=authorization)
    logger.error("[%s] Denied: Unsupported authentication method", request.client.host)
    return ORJSONResponse({"status": False}, status_code=401)


async def auth_cookie(request: Request, jwt_cookie: str) -> ORJSONResponse:
    """
    Authorize against JWT token contained in cookie
    """
    try:
        user = get_user_from_jwt(jwt_cookie)
        return ORJSONResponse({"status": True}, status_code=200, headers={"Remote-User": user})
    except ValueError as e:
        logger.error("[Cookie][%s] Denied: %s", request.client.host, str(e) or "Unspecified reason")
        return ORJSONResponse({"status": False}, status_code=401)


async def auth_private_token(request: Request, private_token: str) -> ORJSONResponse:
    """
    Authenticate against Private-Token header
    """
    reason = None
    remote_ip = request.client.host
    user, access = get_api_access(private_token, remote_ip)
    if user and access:
        return ORJSONResponse(
            {"status": True},
            status_code=200,
            headers={"Remote-User": user, "X-NOC-API-Access": access},
        )
    if not user:
        reason = "API Key not found"
    elif not access:
        reason = "API Key has no access"
    logger.error(
        "[Private-Token][%s|%s] Denied: %s",
        user or "NOT SET",
        remote_ip,
        reason or "Unspecified reason",
    )
    return ORJSONResponse({"status": False}, status_code=401)


api_key_cache = cachetools.TTLCache(100, ttl=3)


@cachetools.cached(api_key_cache)
def get_api_access(key: str, ip: str) -> Tuple[str, str]:
    """
    Cached API key data

    :param key: API Key value
    :param ip: Client IP
    :return:
    """
    return APIKey.get_name_and_access_str(key, ip)


async def auth_authorization(request: Request, authorization: str) -> ORJSONResponse:
    """
    Authenticate against Authorization header
    """
    schema, data = authorization.split(" ", 1)
    if schema == "Basic":
        return await auth_authorization_basic(request=request, data=data)
    elif schema == "Bearer":
        return await auth_authorization_bearer(request=request, data=data)
    logger.error(
        "[Authorization][%s] Denied: Unsupported authorization schema '%s'",
        request.client.host,
        schema,
    )
    return ORJSONResponse({"status": False}, status_code=401)


async def auth_authorization_basic(request: Request, data: str) -> ORJSONResponse:
    """
    HTTP Basic authorization handler
    """
    remote_ip = request.client.host
    auth_data = smart_text(codecs.decode(smart_bytes(data), "base64"))
    if ":" not in auth_data:
        logger.error("[Authorization|Basic][%s] Denied: Malformed data", remote_ip)
        return ORJSONResponse({"status": False}, status_code=401)
    user, password = auth_data.split(":", 1)
    credentials = {"user": user, "password": password, "ip": remote_ip}
    if authenticate(credentials):
        response = ORJSONResponse({"status": True}, status_code=200, headers={"Remote-User": user})
        set_jwt_cookie(response, user)
        return response
    logger.error("[Authorization|Basic][%s|%s] Denied: Authentication failed", user, remote_ip)
    return ORJSONResponse({"status": False}, status_code=401)


async def auth_authorization_bearer(request: Request, data: str) -> ORJSONResponse:
    """
    HTTP Bearer autorization handler
    :return:
    """
    try:
        user = get_user_from_jwt(data)
    except ValueError:
        logger.error(
            "[Authorization|Bearer][%s] Denied: Authentication failed", request.client.host
        )
        return ORJSONResponse({"status": False}, status_code=401)
    return ORJSONResponse({"status": True}, status_code=200, headers={"Remote-User": user})
