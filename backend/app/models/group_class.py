from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import CreatedAtMixin, TimestampMixin


class GroupClass(Base, TimestampMixin):
    __tablename__ = "group_classes"
    __table_args__ = (
        Index("ix_group_classes_date_status", "schedule_date", "status"),
    )

    class_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    class_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="YOGA"
    )  # YOGA, ZUMBA, HIIT, BOXING, CYCLING
    trainer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    room: Mapped[str] = mapped_column(String(100), nullable=False)
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )  # ACTIVE, CANCELLED, COMPLETED
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class GroupClassEnrollment(Base, CreatedAtMixin):
    __tablename__ = "group_class_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "class_id", "user_id", name="uq_group_class_enrollment_user"
        ),
        Index("ix_group_class_enrollments_class", "class_id", "status"),
    )

    enrollment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("group_classes.class_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="REGISTERED"
    )  # REGISTERED, CANCELLED, ATTENDED, ABSENT
    attended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
