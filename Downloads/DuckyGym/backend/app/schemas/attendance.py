from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from models.enums import AttendanceStatus
from schemas.common import ORMModel
from schemas.summary import MemberSummary


class CheckInRequest(BaseModel):
    member_id: int = Field(gt=0)
    subscription_id: Optional[int] = Field(default=None, gt=0)


class CheckOutRequest(BaseModel):
    check_out: Optional[datetime] = None


class AttendanceResponse(ORMModel):
    attendance_id: int
    member_id: int
    subscription_id: Optional[int] = None
    checked_in_by: Optional[int] = None
    check_in: datetime
    check_out: Optional[datetime] = None
    status: AttendanceStatus


class AttendanceDetailResponse(AttendanceResponse):
    member: MemberSummary
    duration_minutes: Optional[int] = None


class CheckInEligibility(BaseModel):
    member_id: int
    eligible: bool
    reason: Optional[str] = None
    subscription_id: Optional[int] = None
    subscription_end_date: Optional[date] = None
    days_remaining: Optional[int] = None


class AttendanceFilter(BaseModel):
    member_id: Optional[int] = None
    status: Optional[AttendanceStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    @model_validator(mode="after")
    def check_date_range(self) -> "AttendanceFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from không được lớn hơn date_to")
        return self
