from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: str) -> str:
    if not settings.secret_key:
        raise RuntimeError("SECRET_KEY must be configured before issuing access tokens.")
    if len(settings.secret_key.encode("utf-8")) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 bytes long.")
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": user_id, "exp": expires}, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    if not settings.secret_key:
        raise RuntimeError("SECRET_KEY must be configured before verifying access tokens.")
    if len(settings.secret_key.encode("utf-8")) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 bytes long.")
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("Token subject is missing.")
    return subject
