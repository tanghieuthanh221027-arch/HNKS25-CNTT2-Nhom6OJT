from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import SubscriptionStatus, SubscriptionType
from app.schemas.common import ORMModel
from app.schemas.invoice import InvoiceResponse
from app.schemas.summary import MemberSummary, PlanSummary


class SubscriptionCreate(BaseModel):
    member_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)
    start_date: Optional[date] = None


class SubscriptionSelfCreate(BaseModel):
    plan_id: int = Field(gt=0)
    start_date: Optional[date] = None


class SubscriptionRenew(BaseModel):
    plan_id: Optional[int] = Field(default=None, gt=0)
    start_date: Optional[date] = None


class SubscriptionUpgrade(BaseModel):
    new_plan_id: int = Field(gt=0)
    start_date: Optional[date] = None


class SubscriptionStatusUpdate(BaseModel):
    status: SubscriptionStatus
    reason: Optional[str] = Field(default=None, max_length=255)


class SubscriptionResponse(ORMModel):
    subscription_id: int
    member_id: int
    plan_id: int
    subscription_type: SubscriptionType
    previous_subscription_id: Optional[int] = None
    start_date: date
    end_date: date
    status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime


class SubscriptionDetailResponse(SubscriptionResponse):
    plan: PlanSummary
    member: Optional[MemberSummary] = None
    days_remaining: Optional[int] = None


class SubscriptionRegisterResult(BaseModel):
    subscription: SubscriptionResponse
    invoice: InvoiceResponse


class SubscriptionFilter(BaseModel):
    member_id: Optional[int] = None
    plan_id: Optional[int] = None
    status: Optional[SubscriptionStatus] = None
    subscription_type: Optional[SubscriptionType] = None
    expiring_within_days: Optional[int] = Field(default=None, ge=0, le=365)
    start_from: Optional[date] = None
    start_to: Optional[date] = None

    @model_validator(mode="after")
    def check_date_range(self) -> "SubscriptionFilter":
        if self.start_from and self.start_to and self.start_from > self.start_to:
            raise ValueError("start_from không được lớn hơn start_to")
        return self
