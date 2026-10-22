from __future__ import annotations

from datetime import datetime
from typing import Dict, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


DepartmentName = Literal[
    "Electrical",
    "Civil and Roads",
    "Plumbing and Water",
    "Sanitation and Housekeeping",
    "Mess and Food",
    "Hostel and Warden",
    "IT and Network",
    "Other",
]
IssueStatus = Literal["Submitted", "Read/Verified", "Assigned", "In Progress", "Resolved", "Reopened"]


class IssueCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=5, max_length=1200)
    category: DepartmentName = "Other"
    location: str = Field(min_length=2, max_length=255)
    evidence: Optional[str] = None
    hostel_id: Optional[int] = None
    floor: Optional[str] = Field(default=None, max_length=30)
    room: Optional[str] = Field(default=None, max_length=30)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class IssueUpdateRequest(BaseModel):
    status: IssueStatus
    note: str = Field(default="", max_length=2000)


class AssignmentRequest(BaseModel):
    department: DepartmentName
    staff_name: Optional[str] = Field(default=None, max_length=160)


class DuplicateLinkRequest(BaseModel):
    duplicate_of: str


class IssueChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    draft: Dict[str, Optional[str]] = Field(default_factory=dict)


class IssueUpdateResponse(BaseModel):
    at: str
    status: str
    note: str


class IssueResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    description: str
    category: str
    location: str
    priority: str
    score: int
    safety: int
    severity: int
    impact: int
    waiting: int
    related: int
    confidence: float
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")
    assigned_to: str = Field(serialization_alias="assignedTo")
    department: str
    duplicate_of: Optional[str] = Field(serialization_alias="duplicateOf")
    updates: list[IssueUpdateResponse]
    evidence: Optional[str]
    created_by: str = Field(serialization_alias="createdBy")
    sla_hours: int = Field(serialization_alias="slaHours")


class IssueChatResponse(BaseModel):
    reply: str
    draft: Dict[str, Optional[str]]
    confidence: float
    category: str
    alternatives: list[str]
    needs_review: bool
    emergency: bool
