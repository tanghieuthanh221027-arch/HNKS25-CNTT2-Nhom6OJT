from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from models.enums import RevenuePeriod


class RevenueQuery(BaseModel):
    period: RevenuePeriod = RevenuePeriod.DAY
    date_from: date
    date_to: date

    @model_validator(mode="after")
    def check_date_range(self) -> "RevenueQuery":
        if self.date_from > self.date_to:
            raise ValueError("date_from không được lớn hơn date_to")
        return self


class RevenuePoint(BaseModel):
    label: str
    revenue: Decimal = Decimal("0.00")
    invoice_count: int = Field(default=0, ge=0)


class RevenueStatsResponse(BaseModel):
    period: RevenuePeriod
    date_from: date
    date_to: date
    total_revenue: Decimal = Decimal("0.00")
    total_invoices: int = Field(default=0, ge=0)
    points: list[RevenuePoint] = []
