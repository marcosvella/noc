# ----------------------------------------------------------------------
# Revoke tokens
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
from fastapi import APIRouter

# NOC modules
from ..auth import revoke_token, get_user_from_jwt
from ..models.revoke import RevokeRequest
from ..models.status import StatusResponse, StatusResponseOk

router = APIRouter()


@router.post("/api/login/revoke", response_model=StatusResponse, tags=["login"])
async def revoke(req: RevokeRequest):
    if req.access_token:
        try:
            get_user_from_jwt(req.access_token, audience="auth")
        except ValueError:
            return StatusResponse(error="unauthorized_client")
        revoke_token(req.access_token)
    if req.refresh_token:
        try:
            get_user_from_jwt(req.refresh_token, audience="auth")
        except ValueError:
            return StatusResponse(error="invalid_request")
        revoke_token(req.refresh_token)
    if not req.access_token and not req.refresh_token:
        return StatusResponse(error="invalid_request")
    return StatusResponseOk(status=True, message="Ok")
