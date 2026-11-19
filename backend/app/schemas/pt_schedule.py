from datetime import date, datetime, time
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from app.models.enums import BookingStatus
from app.schemas.common import ORMModel


class PTScheduleCreate(BaseModel):
    trainer_id: int = Field(gt=0, description="ID của huấn luyện viên (PT)")
    member_id: Optional[int] = Field(default=None, gt=0, description="ID hội viên (tự động lấy nếu hội viên đang đăng nhập)")
    booking_date: date = Field(description="Ngày tập")
    start_time: time = Field(description="Giờ bắt đầu")
    end_time: time = Field(description="Giờ kết thúc")
    schedule_id: Optional[int] = Field(default=None, gt=0, description="ID ca làm việc của PT (tùy chọn)")

    @model_validator(mode="after")
    def validate_times(self) -> "PTScheduleCreate":
        if self.end_time <= self.start_time:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu.")
        if self.booking_date < date.today():
            raise ValueError("Ngày tập không được ở trong quá khứ.")
        return self


class PTScheduleUpdate(BaseModel):
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    @model_validator(mode="after")
    def validate_update(self) -> "PTScheduleUpdate":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật.")
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("Giờ kết thúc phải sau giờ bắt đầu.")
        if self.booking_date is not None and self.booking_date < date.today():
            raise ValueError("Ngày tập không được ở trong quá khứ.")
        return self


class PTScheduleCancelRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255, description="Lý do huỷ ca tập")


class PTScheduleResponse(ORMModel):
    booking_id: int
    schedule_id: int
    trainer_id: int
    trainer_name: Optional[str] = None
    member_id: int
    member_name: Optional[str] = None
    booking_date: date
    start_time: time
    end_time: time
    status: BookingStatus
    created_at: Optional[datetime] = None

