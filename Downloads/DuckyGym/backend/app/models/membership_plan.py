from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.enums import PlanStatus, enum_column
from models.mixins import TimestampMixin

if TYPE_CHECKING:
    from models.subscription import Subscription


class MembershipPlan(Base, TimestampMixin):
    __tablename__ = "membership_plans"
    __table_args__ = (
        CheckConstraint("duration_days > 0", name="duration_positive"),
        CheckConstraint("price >= 0", name="price_non_negative"),
        Index("ix_membership_plans_category_status", "category", "status"),
    )

    plan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[PlanStatus] = mapped_column(
        enum_column(PlanStatus, 20), nullable=False, default=PlanStatus.ACTIVE
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")

    @property
    def is_available(self) -> bool:
        return self.status == PlanStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<MembershipPlan id={self.plan_id} name={self.plan_name!r}>"
