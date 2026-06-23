from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.utils.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, stored_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, stored_password)
    except (UnknownHashError, ValueError):
        return plain_password == stored_password


def password_needs_rehash(stored_password: str) -> bool:
    try:
        return pwd_context.needs_update(stored_password)
    except (UnknownHashError, ValueError):
        return True


def create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    secret_key = (
        settings.jwt_refresh_secret_key
        if token_type == "refresh"
        else settings.jwt_secret_key
    )
    expires_at = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    return create_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
    )


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    return create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh",
    )


def create_oauth_state(nha_cung_cap: str) -> str:
    return create_token(
        subject=nha_cung_cap,
        expires_delta=timedelta(minutes=10),
        token_type="oauth_state",
    )


def decode_token(token: str, token_type: str) -> dict[str, Any]:
    settings = get_settings()
    secret_key = (
        settings.jwt_refresh_secret_key
        if token_type == "refresh"
        else settings.jwt_secret_key
    )
    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

    if payload.get("type") != token_type:
        raise ValueError("Invalid token type")
    return payload
