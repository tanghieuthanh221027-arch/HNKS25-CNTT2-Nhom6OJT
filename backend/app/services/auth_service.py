from sqlalchemy.orm import Session

from app.models.user import User
from app.models.enums import UserRole
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exception import ConflictException, UnauthorizedException, ForbiddenException


def register_user(db: Session, user_in: RegisterRequest) -> User:
    if db.query(User).filter(User.email == user_in.email).first():
        raise ConflictException(message="Email đã tồn tại trong hệ thống.")

    if db.query(User).filter(User.phone == user_in.phone).first():
        raise ConflictException(message="Số điện thoại đã tồn tại trong hệ thống.")

    base_username = user_in.email.split("@")[0]
    username = base_username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}{counter}"
        counter += 1

    new_user = User(
        username=username,
        email=user_in.email,
        phone=user_in.phone,
        full_name=user_in.name,
        password_hash=hash_password(user_in.password),
        role=UserRole.MEMBER,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, login_data: LoginRequest) -> dict:
    user = db.query(User).filter(
        (User.email == login_data.username) | (User.username == login_data.username)
    ).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise UnauthorizedException(message="Email/Tên đăng nhập hoặc mật khẩu không chính xác.")

    if not user.can_login:
        raise ForbiddenException(message="Tài khoản đã bị khóa hoặc không thể đăng nhập.")

    # Đã thêm tham số role=user.role vào hàm dưới đây
    access_token = create_access_token(user_id=user.user_id, role=user.role)
    
    return {
        "token": {
            "access_token": access_token,
            "token_type": "bearer"
        },
        "user": user 
    }