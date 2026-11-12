from fastapi import APIRouter, Depends

from app.models.user import User
# Import trực tiếp hàm get_current_user từ file auth.py trong thư mục dependencies của nhóm
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "name": current_user.full_name,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
    }