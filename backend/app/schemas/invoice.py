from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import InvoiceStatus
from app.schemas.common import Money, ORMModel
from app.schemas.payment import PaymentResponse
from app.schemas.summary import MemberSummary, PlanSummary, UserSummary


class InvoiceCreate(BaseModel):
    member_id: int = Field(gt=0)
    subscription_id: int = Field(gt=0)
    discount_amount: Money = Decimal("0.00")


class InvoiceDiscountUpdate(BaseModel):
    discount_amount: Money


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus
    reason: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def check_target_status(self) -> "InvoiceStatusUpdate":
        if self.status == InvoiceStatus.UNPAID:
            raise ValueError("Không thể chuyển hóa đơn về trạng thái UNPAID")
        return self


class InvoiceResponse(ORMModel):
    invoice_id: int
    member_id: int
    subscription_id: int
    created_by: int
    total_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    member: MemberSummary
    creator: UserSummary
    payments: list[PaymentResponse] = []
    plan: Optional[PlanSummary] = None
    paid_amount: Decimal = Decimal("0.00")
    remaining_amount: Decimal = Decimal("0.00")


class InvoiceFilter(BaseModel):
    member_id: Optional[int] = None
    subscription_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    @model_validator(mode="after")
    def check_date_range(self) -> "InvoiceFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from không được lớn hơn date_to")
        return self
