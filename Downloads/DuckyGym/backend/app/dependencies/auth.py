from typing import Optional
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.exception import ForbiddenException, UnauthorizedException
from core.security import decode_access_token
from db.database import get_db
from models.enums import UserRole
from models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedException("Vui lòng đăng nhập để tiếp tục (Thiếu token xác thực)")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise UnauthorizedException("Token không hợp lệ hoặc đã hết hạn")

    user_id = payload.get("user_id")
    if user_id is None:
        raise UnauthorizedException("Payload của token không hợp lệ")

    user = db.get(User, int(user_id))
    if user is None:
        raise UnauthorizedException("Không tìm thấy tài khoản người dùng")

    if not user.can_login:
        raise ForbiddenException("Tài khoản đã bị khóa hoặc ngừng hoạt động")

    return user


def require_roles(*roles: UserRole | str):
    normalized_roles: list[UserRole] = []
    for role in roles:
        if isinstance(role, UserRole):
            normalized_roles.append(role)
        elif role.upper() == "PT":
            normalized_roles.append(UserRole.TRAINER)
        else:
            normalized_roles.append(UserRole(role.upper()))

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_role(*normalized_roles):
            raise ForbiddenException("Bạn không có quyền truy cập chức năng này")
        return current_user

    return checker


require_admin = require_roles(UserRole.ADMIN)