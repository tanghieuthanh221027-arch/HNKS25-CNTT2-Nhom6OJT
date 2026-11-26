from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import BOOKING_TRANSITIONS, BookingStatus, enum_column
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.subscription import Subscription
    from app.models.trainer_schedule import TrainerSchedule
    from app.models.user import User


class TrainingBooking(Base, CreatedAtMixin):
    """
    Lịch hẹn đặt ca tập cá nhân 1:1 (Mục 3.2.6, 4.5, 5.2, 6.1):
    - Khoá ngoại member_id, trainer_id, subscription_id, schedule_id đều dùng ondelete="RESTRICT" (BR04).
    - Bổ sung subscription_id liên kết trực tiếp tới gói tập bị trừ buổi (BR16).
    - Bổ sung start_at & end_at (DATETIME) hỗ trợ ca tập qua đêm (23:00 -> 01:00 sáng hôm sau).
    - Hỗ trợ đầy đủ 6 trạng thái: PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW, EXPIRED.
    """

    __tablename__ = "training_bookings"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_training_bookings_datetime_range"),
        Index("ix_training_bookings_member_status", "member_id", "status"),
        Index(
            "ix_training_bookings_trainer_slot",
            "trainer_id",
            "booking_date",
            "start_time",
        ),
        Index("ix_training_bookings_trainer_window", "trainer_id", "start_at", "end_at"),
    )

    booking_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    trainer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "subscriptions.subscription_id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    schedule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "trainer_schedules.schedule_id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        enum_column(BookingStatus, 20), nullable=False, default=BookingStatus.PENDING
    )
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    member: Mapped["Member"] = relationship(back_populates="training_bookings")
    trainer: Mapped["User"] = relationship(
        back_populates="training_bookings", foreign_keys=[trainer_id]
    )
    subscription: Mapped["Subscription"] = relationship(
        back_populates="training_bookings"
    )
    schedule: Mapped["TrainerSchedule"] = relationship(back_populates="bookings")

    def can_transition_to(self, new_status: BookingStatus) -> bool:
        return new_status in BOOKING_TRANSITIONS.get(self.status, set())

    def __repr__(self) -> str:
        return (
            f"<TrainingBooking id={self.booking_id} member={self.member_id} "
            f"trainer={self.trainer_id} sub={self.subscription_id} status={self.status.value}>"
        )
