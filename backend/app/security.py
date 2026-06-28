"""密码哈希(标准库 pbkdf2) 与 JWT(PyJWT)。不依赖 bcrypt，保证跨平台可装。"""
import datetime as _dt
import hashlib
import hmac
import secrets

import jwt

from .config import JWT_ALGO, JWT_EXP_HOURS, JWT_SECRET

_ITER = 200_000  # 迭代次数，兼顾安全与性能


def hash_password(password: str) -> tuple[str, str]:
    """返回 (password_hash_hex, salt_hex)。"""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITER)
    return dk.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITER)
    return hmac.compare_digest(dk.hex(), expected_hash)


def create_access_token(user_id: int, username: str) -> str:
    now = _dt.datetime.now(_dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + _dt.timedelta(hours=JWT_EXP_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
