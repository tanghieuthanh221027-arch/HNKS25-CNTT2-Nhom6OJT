from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Date, Index, Integer, Numeric, String, false, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import TimestampMixin


class Discount(Base, TimestampMixin):
    __tablename__ = "discounts"
    __table_args__ = (
        CheckConstraint("discount_value > 0", name="ck_discounts_value_positive"),
        CheckConstraint("usage_limit >= 0", name="ck_discounts_usage_limit_non_neg"),
        CheckConstraint("used_count >= 0", name="ck_discounts_used_count_non_neg"),
        Index("ix_discounts_code_active", "code", "is_active"),
    )

    discount_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PERCENT"
    )  # PERCENT or FIXED
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    max_discount_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    usage_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    def __repr__(self) -> str:
        return f"<Discount id={self.discount_id} code={self.code!r}>"
