from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import Gender, MemberStatus, enum_column
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance_record import AttendanceRecord
    from app.models.feedback import Feedback
    from app.models.invoice import Invoice
    from app.models.subscription import Subscription
    from app.models.trainer_member import TrainerMember
    from app.models.training_booking import TrainingBooking
    from app.models.user import User


class Member(Base, TimestampMixin):
    __tablename__ = "members"
    __table_args__ = (
        Index("ix_members_full_name", "full_name"),
        Index("ix_members_status", "status"),
    )

    member_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[Gender] = mapped_column(enum_column(Gender, 10), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    join_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    status: Mapped[MemberStatus] = mapped_column(
        enum_column(MemberStatus, 20), nullable=False, default=MemberStatus.ACTIVE
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="member")
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="member", order_by="Subscription.start_date.desc()"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="member", order_by="Invoice.created_at.desc()"
    )
    trainer_assignments: Mapped[list["TrainerMember"]] = relationship(
        back_populates="member"
    )
    training_bookings: Mapped[list["TrainingBooking"]] = relationship(
        back_populates="member"
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="member", order_by="AttendanceRecord.check_in.desc()"
    )
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="member")

    @property
    def is_active(self) -> bool:
        return self.status == MemberStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<Member id={self.member_id} name={self.full_name!r}>"
