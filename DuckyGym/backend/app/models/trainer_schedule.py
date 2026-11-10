from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import ScheduleStatus, enum_column

if TYPE_CHECKING:
    from app.models.training_booking import TrainingBooking
    from app.models.user import User


class TrainerSchedule(Base):
    __tablename__ = "trainer_schedules"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="time_range_valid"),
        UniqueConstraint(
            "trainer_id", "work_date", "start_time", name="uq_trainer_schedules_slot"
        ),
        Index("ix_trainer_schedules_trainer_date", "trainer_id", "work_date"),
    )

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[ScheduleStatus] = mapped_column(
        enum_column(ScheduleStatus, 20), nullable=False, default=ScheduleStatus.ACTIVE
    )

    trainer: Mapped["User"] = relationship(
        back_populates="trainer_schedules", foreign_keys=[trainer_id]
    )
    bookings: Mapped[list["TrainingBooking"]] = relationship(back_populates="schedule")

    def __repr__(self) -> str:
        return (
            f"<TrainerSchedule id={self.schedule_id} trainer={self.trainer_id} "
            f"{self.work_date} {self.start_time}-{self.end_time}>"
        )
