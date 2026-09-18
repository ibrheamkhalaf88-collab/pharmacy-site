"""Auth router — تسجيل دخول الإدارة."""
from fastapi import APIRouter, Depends, HTTPException, Response

from ..config import COOKIE_SECURE
from ..deps import SESSION_COOKIE, check_admin_password, new_admin_token, require_admin
from ..models import LoginIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginIn, response: Response):
    if not check_admin_password(body.password):
        raise HTTPException(status_code=401, detail="كلمة السر غير صحيحة")
    token = new_admin_token()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=24 * 3600,
        path="/",
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(_: dict = Depends(require_admin)):
    return {"status": "ok", "role": "admin"}