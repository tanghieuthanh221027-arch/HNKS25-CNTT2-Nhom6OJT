from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=72)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tên đăng nhập không được để trống")
        return value


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    exp: int
    type: str = "access"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LoginResponse(BaseModel):
    token: Token
    user: UserResponse
    redirect_to: Optional[str] = None

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_bcrypt_password_length(cls, value: str) -> str:
        # bcrypt limits passwords by encoded bytes, including UTF-8 multibyte characters.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value
