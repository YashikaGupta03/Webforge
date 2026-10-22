from __future__ import annotations

import ipaddress
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.department import Department, Hostel
from app.models.user import User
from app.schemas.auth import DemoLoginRequest, LoginRequest, SignupRequest, TokenResponse, UserCreate
from app.schemas.user import UserResponse

router = APIRouter()
DEMO_ROLES = ("Student", "Warden", "Administrator", "Department Staff", "Super Admin")


def is_loopback_request(request: Request) -> bool:
    client_host = request.client.host if request.client else ""
    try:
        return ipaddress.ip_address(client_host).is_loopback
    except ValueError:
        return False


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    scholar_no = data.scholar_no.strip()
    account = db.scalar(
        select(User).where(User.scholar_no == scholar_no)
    )
    if account is None or not account.is_active or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid account or password.")
    return TokenResponse(access_token=create_access_token(account.id), role=account.role, name=account.name)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)) -> User:
    user = User(
        id=str(uuid4()),
        email=str(data.email).strip().casefold(),
        scholar_no=data.scholar_no,
        name=data.name,
        role="Student",
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email or scholar number is already registered.") from error
    db.refresh(user)
    return user


@router.post("/demo-login", response_model=TokenResponse)
def demo_login(
    data: DemoLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    client_host = request.client.host if request.client else ""
    try:
        local_request = ipaddress.ip_address(client_host).is_loopback
    except ValueError:
        local_request = False
    if settings.app_environment.casefold() != "development" or not local_request:
        raise HTTPException(status_code=404, detail="Not found.")
    if data.role not in DEMO_ROLES:
        raise HTTPException(status_code=422, detail="Unsupported demo role.")

    role_key = data.role.upper().replace(" ", "-")
    scholar_no = f"LOCAL-DEMO-{role_key}"
    account = db.scalar(select(User).where(User.scholar_no == scholar_no))
    department = db.scalar(select(Department).order_by(Department.id))
    hostel = db.scalar(select(Hostel).order_by(Hostel.id))
    if data.role == "Warden" and hostel is None:
        raise HTTPException(
            status_code=503,
            detail="Seed hostels before using the Warden demo role.",
        )
    if data.role == "Department Staff" and department is None:
        raise HTTPException(
            status_code=503,
            detail="Seed departments before using the Department Staff demo role.",
        )
    if account is None:
        account = User(
            id=str(uuid4()),
            scholar_no=scholar_no,
            email=f"{role_key.lower()}@local-demo.invalid",
            name=f"Local Demo {data.role}",
            role=data.role,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            hostel_id=hostel.id if data.role == "Warden" and hostel else None,
            department_id=department.id if data.role == "Department Staff" and department else None,
        )
        db.add(account)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            account = db.scalar(select(User).where(User.scholar_no == scholar_no))
            if account is None:
                raise
        else:
            db.refresh(account)
    if not account.is_active or account.role != data.role:
        raise HTTPException(status_code=409, detail="The local demo account is unavailable.")
    return TokenResponse(
        access_token=create_access_token(account.id),
        role=account.role,
        name=account.name,
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("Administrator", "Super Admin")),
) -> User:
    if data.role == "Super Admin" and admin.role != "Super Admin":
        raise HTTPException(status_code=403, detail="Only a super admin may provision another super admin.")
    user = User(
        id=str(uuid4()),
        email=str(data.email).casefold(),
        scholar_no=data.scholar_no,
        name=data.name.strip(),
        role=data.role,
        password_hash=hash_password(data.password),
        phone=data.phone,
        hostel_id=data.hostel_id,
        room_no=data.room_no,
        department_id=data.department_id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email or scholar number is already registered.") from error
    db.refresh(user)
    return user
