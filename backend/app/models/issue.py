from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    token: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[str] = mapped_column(String(255), index=True)
    hostel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("hostels.id"))
    floor: Mapped[Optional[str]] = mapped_column(String(30))
    room: Mapped[Optional[str]] = mapped_column(String(30))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="Submitted", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="Medium", index=True)
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    safety: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[int] = mapped_column(Integer, default=0)
    impact: Mapped[int] = mapped_column(Integer, default=0)
    waiting: Mapped[int] = mapped_column(Integer, default=0)
    related: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    priority_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    assigned_to: Mapped[str] = mapped_column(String(160), default="Unassigned")
    assigned_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    department: Mapped[str] = mapped_column(String(100), default="Other")
    duplicate_of: Mapped[Optional[str]] = mapped_column(ForeignKey("issues.id"))
    evidence: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    sla_hours: Mapped[int] = mapped_column(Integer, default=48)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    updates: Mapped[list["IssueUpdate"]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan",
        order_by="IssueUpdate.created_at",
    )
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    duplicate_parent: Mapped[Optional["Issue"]] = relationship(
        remote_side="Issue.id",
        foreign_keys=[duplicate_of],
    )
