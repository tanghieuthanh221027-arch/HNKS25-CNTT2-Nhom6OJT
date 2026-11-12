from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt

import enum
from typing import Any, Optional

from core.config import settings
from models.enums import UserRole


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(user_id: int, role: UserRole | str) -> str:
    # Xử lý an toàn để lấy chuỗi giá trị của role (dù truyền vào là Enum hay str)
    role_str = role.value if isinstance(role, enum.Enum) else str(role)

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role_str,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int, role: UserRole | str) -> str:
    # Xử lý an toàn để lấy chuỗi giá trị của role (dù truyền vào là Enum hay str)
    role_str = role.value if isinstance(role, enum.Enum) else str(role)

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role_str,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") not in (None, "access"):
            return None
        # Đảm bảo luôn có user_id kiểu int
        if "user_id" not in payload and "sub" in payload:
            payload["user_id"] = int(payload["sub"])
        return payload
    except jwt.PyJWTError:
        return None
