from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import BookingStatus
from app.schemas.common import ORMModel
from app.schemas.summary import MemberSummary, UserSummary


class BookingCreate(BaseModel):
    member_id: Optional[int] = Field(default=None, gt=0)
    trainer_id: int = Field(gt=0)
    schedule_id: int = Field(gt=0)
    booking_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_booking(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        if self.booking_date < date.today():
            raise ValueError("Ngày tập không được ở quá khứ")
        return self


class BookingReschedule(BaseModel):
    schedule_id: int = Field(gt=0)
    booking_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_booking(self) -> "BookingReschedule":
        if self.end_time <= self.start_time:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        if self.booking_date < date.today():
            raise ValueError("Ngày tập không được ở quá khứ")
        return self


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class BookingCancel(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)


class BookingResponse(ORMModel):
    booking_id: int
    member_id: int
    trainer_id: int
    schedule_id: int
    booking_date: date
    start_time: time
    end_time: time
    status: BookingStatus
    created_at: datetime


class BookingDetailResponse(BookingResponse):
    member: MemberSummary
    trainer: UserSummary


class BookingFilter(BaseModel):
    member_id: Optional[int] = None
    trainer_id: Optional[int] = None
    status: Optional[BookingStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    @model_validator(mode="after")
    def check_date_range(self) -> "BookingFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from không được lớn hơn date_to")
        return self
