"""Shared dependencies — carrier admin sessions."""
from fastapi import HTTPException, Request

from .config import ADMIN_PASSWORD_HASH, COOKIE_SECURE, TOKEN_SECRET, TOKEN_TTL_HOURS
from .security import create_token, verify_password, verify_token

SESSION_COOKIE = "salaq_session"


def check_admin_password(password: str) -> bool:
    if not password or not ADMIN_PASSWORD_HASH:
        return False
    return verify_password(password, ADMIN_PASSWORD_HASH)


def new_admin_token() -> str:
    return create_token(TOKEN_SECRET, TOKEN_TTL_HOURS)


def require_admin(request: Request) -> dict:
    """تحقّق من جلسة الإدارة (cookie أو Authorization: Bearer <token>)."""
    token = request.cookies.get(SESSION_COOKIE) or ""
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
    payload = verify_token(TOKEN_SECRET, token) if token else None
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="غير مصرح — سجّل الدخول أولاً")
    return payload