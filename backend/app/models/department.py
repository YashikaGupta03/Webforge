from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    sla_hours: Mapped[int] = mapped_column(Integer, default=48)

    members: Mapped[list["User"]] = relationship(back_populates="department")


class Hostel(Base):
    __tablename__ = "hostels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    block: Mapped[Optional[str]] = mapped_column(String(100))
    hostel_type: Mapped[Optional[str]] = mapped_column(String(50))
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]

    residents: Mapped[list["User"]] = relationship(back_populates="hostel")
