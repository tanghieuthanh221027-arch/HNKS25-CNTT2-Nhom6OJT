from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Optional

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


def _check_role_fields(role: UserRole, values: dict[str, Any]) -> None:
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
    address: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]

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
        age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )
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
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    height_cm: Optional[Decimal] = Field(default=None, gt=0, le=300)
    weight_kg: Optional[Decimal] = Field(default=None, gt=0, le=500)
    target_weight_kg: Optional[Decimal] = Field(default=None, gt=0, le=500)
    weekly_workouts: Optional[int] = Field(default=None, ge=1, le=14)
    current_password: Optional[str] = None
    new_password: Optional[str] = None


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


class BodyMetricCreate(BaseModel):
    recorded_date: Optional[date] = None
    height_cm: Decimal = Field(gt=0, le=300)
    weight_kg: Decimal = Field(gt=0, le=500)
    body_fat_pct: Optional[Decimal] = Field(default=None, ge=1, le=75)
    muscle_mass_kg: Optional[Decimal] = Field(default=None, gt=0, le=200)
    waist_cm: Optional[Decimal] = Field(default=None, gt=0, le=250)
    notes: Optional[str] = Field(default=None, max_length=255)


class BodyMetricResponse(ORMModel):
    metric_id: int
    user_id: int
    recorded_date: date
    height_cm: Decimal
    weight_kg: Decimal
    bmi: Decimal
    body_fat_pct: Optional[Decimal] = None
    muscle_mass_kg: Optional[Decimal] = None
    waist_cm: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime


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
    # Extended profile fields (Task T067D56 & T3CD518)
    member_id: Optional[int] = None
    member_code: Optional[str] = None
    qr_base64: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    bmi: Optional[Decimal] = None
    target_weight_kg: Optional[Decimal] = None
    weekly_workouts: Optional[int] = None
    streak_days: int = 0
    total_checkins: int = 0
    badges: list[dict[str, Any]] = []


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
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    status: UserStatus


class UserFilter(BaseModel):
    keyword: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
