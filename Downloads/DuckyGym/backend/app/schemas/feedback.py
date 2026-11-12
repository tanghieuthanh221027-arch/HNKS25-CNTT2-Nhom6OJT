from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from models.enums import FeedbackStatus, FeedbackType
from schemas.common import ORMModel
from schemas.summary import MemberSummary


class FeedbackCreate(BaseModel):
    type: FeedbackType
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_rating_by_type(self) -> "FeedbackCreate":
        if self.type == FeedbackType.RATING and self.rating is None:
            raise ValueError("Đánh giá phải có số sao từ 1 đến 5")
        if self.type == FeedbackType.COMPLAINT and self.rating is not None:
            raise ValueError("Khiếu nại không có số sao đánh giá")
        return self


class FeedbackRespond(BaseModel):
    status: FeedbackStatus
    response: Optional[str] = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def check_response(self) -> "FeedbackRespond":
        if self.status == FeedbackStatus.PENDING:
            raise ValueError("Không thể chuyển phản hồi về trạng thái PENDING")
        if self.status in (FeedbackStatus.RESOLVED, FeedbackStatus.REJECTED) and not self.response:
            raise ValueError("Cần nhập nội dung phản hồi khi giải quyết hoặc từ chối")
        return self


class FeedbackStatusUpdate(BaseModel):
    status: FeedbackStatus


class FeedbackResponse(ORMModel):
    feedback_id: int
    member_id: int
    handled_by: Optional[int] = None
    type: FeedbackType
    rating: Optional[int] = None
    title: str
    content: str
    status: FeedbackStatus
    response: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None


class FeedbackDetailResponse(FeedbackResponse):
    member: MemberSummary


class FeedbackFilter(BaseModel):
    member_id: Optional[int] = None
    type: Optional[FeedbackType] = None
    status: Optional[FeedbackStatus] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class RatingSummary(BaseModel):
    total_ratings: int = 0
    average_rating: Optional[float] = None
    distribution: dict[int, int] = {}
