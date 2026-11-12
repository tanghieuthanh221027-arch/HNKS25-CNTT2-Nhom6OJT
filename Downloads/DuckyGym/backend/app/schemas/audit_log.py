from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from schemas.common import ORMModel


class AuditLogCreate(BaseModel):
    user_id: Optional[int] = Field(default=None, gt=0)
    action: str = Field(min_length=1, max_length=50)
    entity_name: str = Field(min_length=1, max_length=50)
    entity_id: Optional[int] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = Field(default=None, max_length=45)


class AuditLogResponse(ORMModel):
    log_id: int
    user_id: Optional[int] = None
    action: str
    entity_name: str
    entity_id: Optional[int] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = Field(default=None, max_length=50)
    entity_name: Optional[str] = Field(default=None, max_length=50)
    entity_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    @model_validator(mode="after")
    def check_date_range(self) -> "AuditLogFilter":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from không được lớn hơn date_to")
        return self
