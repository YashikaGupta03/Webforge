from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    scholar_no: Optional[str]
    name: str
    role: str
    phone: Optional[str]
    hostel_id: Optional[int]
    room_no: Optional[str]
    department_id: Optional[int]
