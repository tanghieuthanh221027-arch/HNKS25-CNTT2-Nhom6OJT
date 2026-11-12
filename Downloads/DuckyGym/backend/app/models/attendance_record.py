from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.enums import AttendanceStatus, enum_column

if TYPE_CHECKING:
    from models.member import Member
    from models.subscription import Subscription
    from models.user import User


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        CheckConstraint(
            "check_out IS NULL OR check_out >= check_in",
            name="ck_attendance_records_time_range",
        ),
        Index("ix_attendance_records_member_status", "member_id", "status"),
        Index("ix_attendance_records_check_in", "check_in"),
    )

    attendance_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(
            "subscriptions.subscription_id", ondelete="SET NULL", onupdate="CASCADE"
        ),
        nullable=True,
        index=True,
    )
    checked_in_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    check_in: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        enum_column(AttendanceStatus, 20),
        nullable=False,
        default=AttendanceStatus.CHECKED_IN,
    )

    member: Mapped["Member"] = relationship(back_populates="attendance_records")
    subscription: Mapped[Optional["Subscription"]] = relationship(
        back_populates="attendance_records"
    )
    checker: Mapped[Optional["User"]] = relationship(
        back_populates="checked_in_records", foreign_keys=[checked_in_by]
    )

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.check_out is None:
            return None
        return int((self.check_out - self.check_in).total_seconds() // 60)

    def __repr__(self) -> str:
        return (
            f"<AttendanceRecord id={self.attendance_id} member={self.member_id} "
            f"status={self.status.value}>"
        )
