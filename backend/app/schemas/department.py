from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sla_hours: int


class HostelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    block: Optional[str]
    hostel_type: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
