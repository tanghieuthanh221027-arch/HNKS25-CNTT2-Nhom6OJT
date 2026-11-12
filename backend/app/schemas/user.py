from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional , Any

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.enums import Gender, UserRole, UserStatus
from app.schemas.common import (
    Money,
    NameStr,
    ORMModel,
    PhoneStr,
    UsernameStr,
    validate_password_strength,
)

STAFF_ROLES = {UserRole.ADMIN, UserRole.STAFF, UserRole.CASHIER, UserRole.TRAINER}
EMPLOYMENT_FIELDS = ("position", "hire_date", "salary")
TRAINER_FIELDS = ("specialization", "experience_years", "bio")


def _check_role_fields(role: UserRole, values: dict[str , Any]) -> None:
    if role == UserRole.MEMBER:
        for field in EMPLOYMENT_FIELDS:
            if values.get(field) is not None:
                raise ValueError(f"Trường {field} không áp dụng cho vai trò MEMBER")
    if role != UserRole.TRAINER:
        for field in TRAINER_FIELDS:
            if values.get(field) is not None:
                raise ValueError(f"Trường {field} chỉ áp dụng cho vai trò TRAINER")


class UserCreate(BaseModel):
    username: UsernameStr
    password: str
    full_name: NameStr
    email: EmailStr
    phone: PhoneStr
    role: UserRole
    position: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    hire_date: Optional[date] = None
    salary: Optional[Money] = None
    specialization: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    experience_years: Optional[int] = Field(default=None, ge=0, le=60)
    bio: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def check_role_specific_fields(self) -> "UserCreate":
        _check_role_fields(self.role, self.model_dump())
        return self


class UserRegister(BaseModel):
    username: UsernameStr
    password: str
    confirm_password: str
    full_name: NameStr
    email: EmailStr
    phone: PhoneStr
    gender: Gender
    date_of_birth: date
    address: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("date_of_birth")
    @classmethod
    def check_birth_date(cls, value: date) -> date:
        today = date.today()
        if value >= today:
            raise ValueError("Ngày sinh phải nhỏ hơn ngày hiện tại")
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 12 or age > 100:
            raise ValueError("Tuổi hội viên phải từ 12 đến 100")
        return value

    @model_validator(mode="after")
    def check_password_match(self) -> "UserRegister":
        if self.password != self.confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return self


class UserUpdateSelf(BaseModel):
    full_name: Optional[NameStr] = None
    email: Optional[EmailStr] = None
    phone: Optional[PhoneStr] = None
    bio: Optional[str] = None

    @model_validator(mode="after")
    def require_any_field(self) -> "UserUpdateSelf":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật")
        return self


class UserUpdate(BaseModel):
    full_name: Optional[NameStr] = None
    email: Optional[EmailStr] = None
    phone: Optional[PhoneStr] = None
    position: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    hire_date: Optional[date] = None
    salary: Optional[Money] = None
    specialization: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    experience_years: Optional[int] = Field(default=None, ge=0, le=60)
    bio: Optional[str] = None

    @model_validator(mode="after")
    def require_any_field(self) -> "UserUpdate":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật")
        return self


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    status: UserStatus
    reason: Optional[str] = Field(default=None, max_length=255)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def check_passwords(self) -> "PasswordChange":
        if self.new_password != self.confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp")
        if self.new_password == self.current_password:
            raise ValueError("Mật khẩu mới phải khác mật khẩu hiện tại")
        return self


class PasswordReset(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserResponse(ORMModel):
    user_id: int
    username: str
    full_name: str
    email: str
    phone: str
    role: UserRole
    position: Optional[str] = None
    hire_date: Optional[date] = None
    salary: Optional[Decimal] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class UserPublicResponse(ORMModel):
    user_id: int
    username: str
    full_name: str
    email: str
    phone: str
    role: UserRole
    position: Optional[str] = None
    status: UserStatus
    created_at: datetime


class TrainerResponse(ORMModel):
    user_id: int
    full_name: str
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    status: UserStatus


class UserFilter(BaseModel):
    keyword: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
