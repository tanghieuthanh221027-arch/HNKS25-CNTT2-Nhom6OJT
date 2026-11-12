from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.enums import BOOKING_TRANSITIONS, BookingStatus, enum_column
from models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from models.member import Member
    from models.trainer_schedule import TrainerSchedule
    from models.user import User


class TrainingBooking(Base, CreatedAtMixin):
    __tablename__ = "training_bookings"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_training_bookings_time_range"),
        Index("ix_training_bookings_member_status", "member_id", "status"),
        Index(
            "ix_training_bookings_trainer_slot",
            "trainer_id",
            "booking_date",
            "start_time",
        ),
    )

    booking_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    trainer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
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
    status: Mapped[BookingStatus] = mapped_column(
        enum_column(BookingStatus, 20), nullable=False, default=BookingStatus.PENDING
    )

    member: Mapped["Member"] = relationship(back_populates="training_bookings")
    trainer: Mapped["User"] = relationship(
        back_populates="training_bookings", foreign_keys=[trainer_id]
    )
    schedule: Mapped["TrainerSchedule"] = relationship(back_populates="bookings")

    def can_transition_to(self, new_status: BookingStatus) -> bool:
        return new_status in BOOKING_TRANSITIONS[self.status]

    def __repr__(self) -> str:
        return (
            f"<TrainingBooking id={self.booking_id} member={self.member_id} "
            f"trainer={self.trainer_id} status={self.status.value}>"
        )
