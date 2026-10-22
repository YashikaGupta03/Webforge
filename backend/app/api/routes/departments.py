from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.department import Department, Hostel
from app.models.user import User
from app.schemas.department import DepartmentResponse, HostelResponse
from app.schemas.user import UserResponse
from app.services.assignment_service import get_assignable_staff

router = APIRouter()


@router.get("", response_model=list[DepartmentResponse])
def departments(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.name)).all())


@router.get("/hostels", response_model=list[HostelResponse])
def hostels(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Hostel]:
    return list(db.scalars(select(Hostel).order_by(Hostel.name)).all())


@router.get("/{department_id}/staff", response_model=list[UserResponse])
def department_staff(
    department_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("Administrator", "Super Admin", "Warden")),
) -> list[User]:
    return get_assignable_staff(db, department_id)
