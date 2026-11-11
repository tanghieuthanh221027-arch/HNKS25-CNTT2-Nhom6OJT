from datetime import date, datetime
from typing import Annotated, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.enums import Gender, MemberStatus
from app.schemas.common import NameStr, ORMModel, PhoneStr
from app.schemas.invoice import InvoiceResponse
from app.schemas.subscription import SubscriptionDetailResponse
from app.schemas.trainer_member import AssignmentDetailResponse

Address = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


def _check_birth_date(value: date) -> date:
    today = date.today()
    if value >= today:
        raise ValueError("Ngày sinh phải nhỏ hơn ngày hiện tại")
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 12 or age > 100:
        raise ValueError("Tuổi hội viên phải từ 12 đến 100")
    return value


class MemberBase(BaseModel):
    full_name: NameStr
    gender: Gender
    date_of_birth: date
    phone: PhoneStr
    email: EmailStr
    address: Address

    @field_validator("date_of_birth")
    @classmethod
    def check_birth_date(cls, value: date) -> date:
        return _check_birth_date(value)


class MemberCreate(MemberBase):
    user_id: Optional[int] = Field(default=None, gt=0)
    join_date: Optional[date] = None
    status: MemberStatus = MemberStatus.ACTIVE


class MemberUpdate(BaseModel):
    full_name: Optional[NameStr] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    phone: Optional[PhoneStr] = None
    email: Optional[EmailStr] = None
    address: Optional[Address] = None

    @field_validator("date_of_birth")
    @classmethod
    def check_birth_date(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return value
        return _check_birth_date(value)

    @model_validator(mode="after")
    def require_any_field(self) -> "MemberUpdate":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật")
        return self


class MemberStatusUpdate(BaseModel):
    status: MemberStatus


class MemberLinkUser(BaseModel):
    user_id: int = Field(gt=0)


class MemberResponse(ORMModel):
    member_id: int
    user_id: Optional[int] = None
    full_name: str
    gender: Gender
    date_of_birth: date
    phone: str
    email: str
    address: str
    join_date: date
    status: MemberStatus
    created_at: datetime
    updated_at: datetime


class MemberDetailResponse(MemberResponse):
    current_subscription: Optional[SubscriptionDetailResponse] = None
    current_trainer: Optional[AssignmentDetailResponse] = None
    total_visits: int = 0
    last_check_in: Optional[datetime] = None


class MemberHistoryResponse(BaseModel):
    member_id: int
    subscriptions: list[SubscriptionDetailResponse] = []
    invoices: list[InvoiceResponse] = []


class MemberSearchParams(BaseModel):
    keyword: Optional[str] = Field(default=None, max_length=100)
    member_id: Optional[int] = None
    status: Optional[MemberStatus] = None
    gender: Optional[Gender] = None
    has_active_subscription: Optional[bool] = None
