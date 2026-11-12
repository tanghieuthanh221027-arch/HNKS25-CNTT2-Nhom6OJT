from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from dependencies.auth import require_roles
from models.enums import UserRole
from models.user import User
from schemas.user import UserResponse, UserUpdateSelf
from service.user import update_my_profile

router = APIRouter(prefix="/users", tags=["Users"])

# Áp dụng require_roles cho các vai trò theo yêu cầu TV2
allow_authenticated_roles = require_roles(
    UserRole.ADMIN,
    UserRole.STAFF,
    UserRole.MEMBER,
    UserRole.TRAINER,
)


@router.get("/me", response_model=UserResponse, summary="Xem hồ sơ cá nhân")
def get_me(
    current_user: User = Depends(allow_authenticated_roles),
) -> User:
    return current_user


@router.put("/me", response_model=UserResponse, summary="Cập nhật hồ sơ cá nhân")
def update_me(
    payload: UserUpdateSelf,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_authenticated_roles),
) -> User:
    return update_my_profile(db=db, current_user=current_user, data=payload)