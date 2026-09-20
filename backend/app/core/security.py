"""密码哈希和登录令牌工具。

密码使用 Python 标准库 PBKDF2 加盐保存，数据库中永远不会出现明文密码。
"""

import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt

from backend.app.core.config import settings


def hash_password(password: str) -> str:
    """将明文密码转换为不可逆的 PBKDF2 哈希。"""

    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 390_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """安全比较登录密码与数据库中的哈希。"""

    try:
        salt_hex, digest_hex = stored_hash.split(":", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 390_000)
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    """创建包含用户编号和过期时间的 JWT 登录令牌。"""

    expires_at = datetime.now(UTC) + timedelta(minutes=settings.token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> int | None:
    """校验 JWT，并返回用户编号；令牌无效时返回 None。"""

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None

