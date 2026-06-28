"""FastAPI 依赖：数据库会话、当前登录用户。"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models.user import User
from .security import decode_token

# auto_error=False：未带 token 时由 get_current_user 统一返回 401
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise cred_exc
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
    except Exception:
        raise cred_exc
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise cred_exc
    return user
