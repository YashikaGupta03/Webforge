from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    text: str
    at: datetime = Field(validation_alias="created_at")
    read: bool = Field(validation_alias="is_read")
    issue_id: Optional[str] = Field(validation_alias="issue_id", serialization_alias="issueId")
