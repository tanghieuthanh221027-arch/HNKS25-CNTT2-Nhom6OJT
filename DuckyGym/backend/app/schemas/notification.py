from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import NotificationType
from app.schemas.common import ORMModel


class NotificationCreate(BaseModel):
    user_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    type: NotificationType = NotificationType.SYSTEM


class NotificationMarkRead(BaseModel):
    notification_ids: list[int] = Field(min_length=1)


class NotificationResponse(ORMModel):
    notification_id: int
    user_id: int
    title: str
    content: str
    type: NotificationType
    is_read: bool
    created_at: datetime


class NotificationFilter(BaseModel):
    type: Optional[NotificationType] = None
    is_read: Optional[bool] = None


class UnreadCountResponse(BaseModel):
    unread: int = Field(ge=0)
