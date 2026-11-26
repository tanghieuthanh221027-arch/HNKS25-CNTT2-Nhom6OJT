from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import SubscriptionStatus, SubscriptionType, enum_column
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance_record import AttendanceRecord
    from app.models.invoice import Invoice
    from app.models.member import Member
    from app.models.membership_plan import MembershipPlan
    from app.models.training_booking import TrainingBooking


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_subscriptions_date_range"),
        CheckConstraint("total_sessions >= 0", name="ck_subscriptions_total_sessions"),
        CheckConstraint("sessions_remaining >= 0", name="ck_subscriptions_sessions_remaining"),
        Index("ix_subscriptions_member_status", "member_id", "status"),
        Index("ix_subscriptions_status_end_date", "status", "end_date"),
    )

    subscription_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("membership_plans.plan_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        enum_column(SubscriptionType, 20),
        nullable=False,
        default=SubscriptionType.NEW,
    )
    previous_subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(
            "subscriptions.subscription_id", ondelete="SET NULL", onupdate="CASCADE"
        ),
        nullable=True,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[SubscriptionStatus] = mapped_column(
        enum_column(SubscriptionStatus, 20),
        nullable=False,
        default=SubscriptionStatus.PENDING,
    )

    member: Mapped["Member"] = relationship(back_populates="subscriptions")
    plan: Mapped["MembershipPlan"] = relationship(back_populates="subscriptions")
    previous_subscription: Mapped[Optional["Subscription"]] = relationship(
        remote_side="Subscription.subscription_id",
        back_populates="next_subscriptions",
    )
    next_subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="previous_subscription"
    )
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="subscription")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="subscription"
    )
    training_bookings: Mapped[list["TrainingBooking"]] = relationship(
        back_populates="subscription"
    )

    def is_valid_on(self, day: date) -> bool:
        return (
            self.status == SubscriptionStatus.ACTIVE
            and self.start_date <= day <= self.end_date
        )

    def __repr__(self) -> str:
        return (
            f"<Subscription id={self.subscription_id} member={self.member_id} "
            f"sessions={self.sessions_remaining}/{self.total_sessions} status={self.status.value}>"
        )
