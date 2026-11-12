from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from models.enums import ScheduleStatus
from schemas.common import ORMModel


class ScheduleCreate(BaseModel):
    trainer_id: Optional[int] = Field(default=None, gt=0)
    work_date: date
    start_time: time
    end_time: time
    status: ScheduleStatus = ScheduleStatus.ACTIVE

    @model_validator(mode="after")
    def check_time_range(self) -> "ScheduleCreate":
        if self.end_time <= self.start_time:
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        if self.work_date < date.today():
            raise ValueError("Ngày làm việc không được ở quá khứ")
        return self


class ScheduleUpdate(BaseModel):
    work_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: Optional[ScheduleStatus] = None

    @model_validator(mode="after")
    def check_input(self) -> "ScheduleUpdate":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật")
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")
        return self


class ScheduleResponse(ORMModel):
    schedule_id: int
    trainer_id: int
    work_date: date
    start_time: time
    end_time: time
    status: ScheduleStatus


class ScheduleDetailResponse(ScheduleResponse):
    trainer_name: Optional[str] = None
    is_booked: bool = False


class ScheduleFilter(BaseModel):
    trainer_id: Optional[int] = None
    status: Optional[ScheduleStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    only_available: bool = False

    @model_validator(mode="after")
    def check_date_range(self) -> "ScheduleFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from không được lớn hơn date_to")
        return self
