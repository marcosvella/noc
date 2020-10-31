# ----------------------------------------------------------------------
# ManagedObjectModel
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List
from pydantic import IPvAnyAddress, validator

# NOC modules
from .base import BaseModel
from .typing import Reference
from .administrativedomain import AdministrativeDomain
from .authprofile import AuthProfile
from .container import Container
from .managedobjectprofile import ManagedObjectProfile
from .networksegment import NetworkSegment
from .resourcegroup import ResourceGroup
from .ttsystem import TTSystem
from .project import Project


class ManagedObject(BaseModel):
    id: str
    name: str
    is_managed: bool
    container: Optional[Reference["Container"]]
    administrative_domain: Reference["AdministrativeDomain"]
    pool: str
    fm_pool: Optional[str]
    segment: Reference["NetworkSegment"]
    profile: str
    object_profile: Reference["ManagedObjectProfile"]
    static_client_groups: List[Reference["ResourceGroup"]]
    static_service_groups: List[Reference["ResourceGroup"]]
    scheme: str
    address: str
    port: Optional[str]
    user: Optional[str]
    password: Optional[str]
    super_password: Optional[str]
    snmp_ro: Optional[str]
    description: Optional[str]
    auth_profile: Optional[Reference["AuthProfile"]]
    tags: List[str]
    tt_system: Optional[Reference["TTSystem"]]
    tt_queue: Optional[str]
    tt_system_id: Optional[str]
    project: Optional[Reference["Project"]]

    @validator('address')
    def address_must_ipaddress(cls, v):
        IPvAnyAddress().validate(v)
        return str(v)

    _csv_fields = [
        "id",
        "name",
        "is_managed",
        "container",
        "administrative_domain",
        "pool",
        "fm_pool",
        "segment",
        "profile",
        "object_profile",
        "static_client_groups",
        "static_service_groups",
        "scheme",
        "address",
        "port",
        "user",
        "password",
        "super_password",
        "snmp_ro",
        "description",
        "auth_profile",
        "tags",
        "tt_system",
        "tt_queue",
        "tt_system_id",
        "project",
    ]
