from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.services import auth_service
from app.services.user import build_user_profile_dict

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Đăng ký tài khoản hội viên mới")
def register(user_in: RegisterRequest, db: Session = Depends(get_db)):
    new_user = auth_service.register_user(db=db, user_in=user_in)
    return {
        "message": "Đăng ký thành công",
        "user_id": new_user.user_id,
    }


@router.post("/login", response_model=LoginResponse, summary="Đăng nhập nhận JWT Access Token")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    auth_result = auth_service.authenticate_user(db=db, login_data=login_data)
    user_obj = auth_result["user"]
    return {
        "token": auth_result["token"],
        "user": build_user_profile_dict(db, user_obj),
    }
