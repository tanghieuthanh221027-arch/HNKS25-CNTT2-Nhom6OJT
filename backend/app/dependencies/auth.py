from typing import Optional

from fastapi import Depends, Request

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from app.core.exception import ForbiddenException, UnauthorizedException

from app.core.security import decode_access_token

from app.db.database import get_db

from app.models.enums import UserRole

from app.models.user import User

bearer_scheme = HTTPBearer()

def get_client_ip(request: Request) -> Optional[str]:

    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:

        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else None

def get_current_user(

    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),

    db: Session = Depends(get_db),

) -> User:

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

def require_roles(*roles: UserRole):

    def checker(current_user: User = Depends(get_current_user)) -> User:

        if not current_user.has_role(*roles):

            raise ForbiddenException("Bạn không có quyền truy cập chức năng này")

        return current_user

    return checker

require_admin = require_roles(UserRole.ADMIN)
