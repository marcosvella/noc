# ----------------------------------------------------------------------
# DefaultResourceGroupItem
# ----------------------------------------------------------------------
# Copyright (C) 2007-2021 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import Optional, List

# Third-party modules
from pydantic import BaseModel

# NOC modules
from .utils import Reference
from ..models.label import LabelItem


class DefaultResourceGroupItem(BaseModel):
    id: str
    name: str
    technology: Reference
    parent: Optional[Reference]
    description: Optional[str]
    dynamic_service_labels: Optional[List[str]]
    dynamic_client_labels: Optional[List[str]]
    remote_system: Optional[Reference]
    remote_id: Optional[str]
    bi_id: str
    # Labels
    labels: Optional[List[LabelItem]]
    effective_labels: Optional[List[LabelItem]]


class FormResourceGroupItem(BaseModel):
    name: str
    technology: Reference
    parent: Optional[Reference]
    description: Optional[str]
    dynamic_service_labels: Optional[List[str]]
    dynamic_client_labels: Optional[List[str]]
    labels: Optional[List[str]]
