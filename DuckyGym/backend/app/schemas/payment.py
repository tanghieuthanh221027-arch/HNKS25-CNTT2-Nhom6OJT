from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PaymentMethod, PaymentStatus
from app.schemas.common import ORMModel, PositiveMoney


class PaymentCreate(BaseModel):
    invoice_id: int = Field(gt=0)
    amount: PositiveMoney
    payment_method: PaymentMethod
    transaction_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    payment_date: Optional[datetime] = None

    @model_validator(mode="after")
    def check_transfer_code(self) -> "PaymentCreate":
        if self.payment_method == PaymentMethod.CASH and self.transaction_code:
            raise ValueError("Thanh toán tiền mặt không có mã giao dịch")
        return self


class PaymentConfirm(BaseModel):
    transaction_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    confirmed: bool = True


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
    reason: Optional[str] = Field(default=None, max_length=255)


class RefundRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=255)


class PaymentResponse(ORMModel):
    payment_id: int
    invoice_id: int
    received_by: Optional[int] = None
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: datetime
    status: PaymentStatus
    transaction_code: Optional[str] = None


class PaymentFilter(BaseModel):
    invoice_id: Optional[int] = None
    status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    @model_validator(mode="after")
    def check_date_range(self) -> "PaymentFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from không được lớn hơn date_to")
        return self
