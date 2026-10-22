from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scholar_no: Mapped[Optional[str]] = mapped_column(String(40), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(30), default="Student", index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    hostel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("hostels.id"))
    room_no: Mapped[Optional[str]] = mapped_column(String(30))
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    hostel: Mapped[Optional["Hostel"]] = relationship(back_populates="residents")
    department: Mapped[Optional["Department"]] = relationship(back_populates="members")
