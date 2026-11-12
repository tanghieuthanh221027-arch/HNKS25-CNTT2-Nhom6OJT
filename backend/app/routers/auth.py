from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.database import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# Schema khớp với dữ liệu Register.jsx gửi lên
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

# Schema khớp với dữ liệu Login gửi lên
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: RegisterRequest, db: Session = Depends(get_db)):
    # 1. Chặn trùng Email và Số điện thoại
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại trong hệ thống.")
        
    if db.query(User).filter(User.phone == user_in.phone).first():
        raise HTTPException(status_code=400, detail="Số điện thoại đã tồn tại trong hệ thống.")

    # 2. Tự động tạo username từ email (VD: abc@gmail.com -> abc) và tránh trùng lặp
    base_username = user_in.email.split("@")[0]
    username = base_username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}{counter}"
        counter += 1

    # 3. Hash mật khẩu và lưu vào DB
    hashed_pwd = hash_password(user_in.password)

    new_user = User(
        username=username,
        email=user_in.email,
        phone=user_in.phone,
        full_name=user_in.name,
        password_hash=hashed_pwd,
        role=UserRole.MEMBER
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Đăng ký thành công", "user_id": new_user.user_id}


@router.post("/login")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )
    
    if not user.can_login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa hoặc không thể đăng nhập."
        )

    access_token = create_access_token(user_id=user.user_id, role=user.role)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }