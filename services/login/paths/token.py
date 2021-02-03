# ----------------------------------------------------------------------
# /api/login/token handler
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from http import HTTPStatus
from typing import Optional, Dict
import codecs

# Third-party modules
from fastapi import APIRouter, Request, Header

# NOC modules
from noc.config import config
from noc.core.comp import smart_text, smart_bytes
from ..models.token import TokenRequest, TokenResponse
from ..auth import authenticate, get_jwt_token, get_user_from_jwt, revoke_token, is_revoked
from ..exceptions import HTTPException

router = APIRouter()


@router.post("/api/login/token", response_model=TokenResponse, tags=["login"])
async def token(
    request: Request,
    req: TokenRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    auth_req: Optional[Dict[str, str]]
    if req.grant_type == "refresh_token":
        # Refresh token
        if is_revoked(req.refresh_token):
            raise HTTPException(error="invalid_grant", status_code=HTTPStatus.FORBIDDEN)
        try:
            user = get_user_from_jwt(req.refresh_token, audience="refresh")
        except ValueError as e:
            raise HTTPException(
                error="unauthorized_client (%s)" % e, status_code=HTTPStatus.FORBIDDEN
            )
        revoke_token(req.refresh_token)
        return get_token_response(user)
    elif req.grant_type == "password":
        # ROPCGrantRequest
        auth_req = {"user": req.username, "password": req.password, "ip": request.client.host}
    elif req.grant_type == "client_credentials" and authorization:
        # CCGrantRequest + Basic auth header
        schema, data = authorization.split(" ", 1)
        if schema != "Basic":
            raise HTTPException(error="unsupported_grant_type", status_code=HTTPStatus.BAD_REQUEST)
        auth_data = smart_text(codecs.decode(smart_bytes(data), "base64"))
        if ":" not in auth_data:
            raise HTTPException(error="invalid_request", status_code=HTTPStatus.BAD_REQUEST)
        user, password = auth_data.split(":", 1)
        auth_req = {"user": user, "password": password, "ip": request.client.host}
    else:
        raise HTTPException(error="unsupported_grant_type", status_code=HTTPStatus.BAD_REQUEST)
    # Authenticate
    if auth_req:
        user = authenticate(auth_req)
        if user:
            return get_token_response(user)
    raise HTTPException(error="invalid_scope", status_code=HTTPStatus.BAD_REQUEST)


def get_token_response(user: str) -> TokenResponse:
    expire = config.login.session_ttl
    return TokenResponse(
        access_token=get_jwt_token(user, expire=expire, audience="auth"),
        token_type="bearer",
        expires_in=expire,
        refresh_token=get_jwt_token(user, expire=expire, audience="refresh"),
    )
