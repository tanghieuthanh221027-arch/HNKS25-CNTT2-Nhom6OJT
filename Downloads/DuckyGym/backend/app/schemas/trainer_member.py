from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from models.enums import AssignmentStatus
from schemas.common import ORMModel
from schemas.summary import MemberSummary, UserSummary


class AssignmentCreate(BaseModel):
    trainer_id: int = Field(gt=0)
    member_id: int = Field(gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def check_date_range(self) -> "AssignmentCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc không được trước ngày bắt đầu")
        return self


class AssignmentUpdate(BaseModel):
    end_date: Optional[date] = None
    status: Optional[AssignmentStatus] = None

    @model_validator(mode="after")
    def require_any_field(self) -> "AssignmentUpdate":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật")
        return self


class AssignmentResponse(ORMModel):
    id: int
    trainer_id: int
    member_id: int
    assigned_by: int
    start_date: date
    end_date: Optional[date] = None
    status: AssignmentStatus


class AssignmentDetailResponse(AssignmentResponse):
    trainer: UserSummary
    member: MemberSummary


class AssignmentFilter(BaseModel):
    trainer_id: Optional[int] = None
    member_id: Optional[int] = None
    status: Optional[AssignmentStatus] = None
