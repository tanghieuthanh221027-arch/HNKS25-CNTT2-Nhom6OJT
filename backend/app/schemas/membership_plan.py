from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.models.enums import PlanStatus
from app.schemas.common import Money, ORMModel

PlanName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
PlanCategory = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class PlanBase(BaseModel):
    plan_name: PlanName
    category: PlanCategory
    duration_days: int = Field(gt=0, le=3650)
    price: Money
    description: Optional[str] = None


class PlanCreate(PlanBase):
    status: PlanStatus = PlanStatus.ACTIVE


class PlanUpdate(BaseModel):
    plan_name: Optional[PlanName] = None
    category: Optional[PlanCategory] = None
    duration_days: Optional[int] = Field(default=None, gt=0, le=3650)
    price: Optional[Money] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def require_any_field(self) -> "PlanUpdate":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật")
        return self


class PlanStatusUpdate(BaseModel):
    status: PlanStatus


class PlanResponse(ORMModel):
    plan_id: int
    plan_name: str
    category: str
    duration_days: int
    price: Decimal
    description: Optional[str] = None
    status: PlanStatus
    created_at: datetime
    updated_at: datetime


class PlanFilter(BaseModel):
    keyword: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    status: Optional[PlanStatus] = None
    min_price: Optional[Decimal] = Field(default=None, ge=0)
    max_price: Optional[Decimal] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_price_range(self) -> "PlanFilter":
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price không được lớn hơn max_price")
        return self
