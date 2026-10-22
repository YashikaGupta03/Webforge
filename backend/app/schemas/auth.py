from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    scholar_no: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class UserCreate(BaseModel):
    email: EmailStr
    scholar_no: Optional[str] = Field(default=None, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["Student", "Warden", "Administrator", "Department Staff", "Super Admin"] = "Student"
    phone: Optional[str] = Field(default=None, max_length=30)
    hostel_id: Optional[int] = None
    room_no: Optional[str] = Field(default=None, max_length=30)
    department_id: Optional[int] = None
