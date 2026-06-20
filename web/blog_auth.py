import os
import secrets
import bcrypt
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

ADMIN_PASSWORD_HASH = os.environ.get(
    "BLOG_ADMIN_HASH",
    bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
)
ADMIN_USERNAME = os.environ.get("BLOG_ADMIN_USER", "admin")

_sessions: dict[str, float] = {}


def verify_password(password: str) -> bool:
    return bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH.encode())


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    import time
    _sessions[token] = time.time()
    return token


def validate_session(token: str | None) -> bool:
    if not token or token not in _sessions:
        return False
    import time
    if time.time() - _sessions[token] > 86400 * 7:
        del _sessions[token]
        return False
    return True


def delete_session(token: str):
    _sessions.pop(token, None)


def require_admin(request: Request):
    token = request.cookies.get("blog_session")
    if not validate_session(token):
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


def require_admin_redirect(request: Request) -> RedirectResponse | None:
    token = request.cookies.get("blog_session")
    if not validate_session(token):
        return RedirectResponse(url="/admin/login", status_code=303)
    return None
