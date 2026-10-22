from __future__ import annotations

import ipaddress
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/demo-login", response_model=TokenResponse)
def demo_login(request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    client_host = request.client.host if request.client else ""
    try:
        is_local_client = ipaddress.ip_address(client_host).is_loopback
    except ValueError:
        is_local_client = False
    if settings.app_environment.casefold() != "development" or not is_local_client:
        raise HTTPException(status_code=404, detail="Not found.")

    scholar_no = "LOCAL-DEMO-STUDENT"
    account = db.scalar(select(User).where(User.scholar_no == scholar_no))
    if account is None:
        account = User(
            id=str(uuid4()),
            scholar_no=scholar_no,
            email="local-demo-student@localhost.invalid",
            name="Local Demo Student",
            role="Student",
            password_hash=hash_password(secrets.token_urlsafe(32)),
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
    if not account.is_active or account.role != "Student":
        raise HTTPException(status_code=409, detail="The local demo account is unavailable.")
    return TokenResponse(
        access_token=create_access_token(account.id),
        role=account.role,
        name=account.name,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    account = db.scalar(
        select(User).where(User.scholar_no == data.scholar_no.strip())
    )
    if account is None or not account.is_active or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid account or password.")
    return TokenResponse(access_token=create_access_token(account.id), role=account.role, name=account.name)


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
