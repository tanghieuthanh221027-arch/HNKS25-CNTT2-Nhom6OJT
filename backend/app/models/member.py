from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timezone_utils import today_vn
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
    """
    Bảng hồ sơ mở rộng của Hội viên (Profile 1-1 với bảng users).
    Đã chuẩn hoá 3NF (Mục 3.2.1 & 3.2.2): xoá bỏ dư thừa full_name, email, phone tại bảng members,
    dùng chung định danh duy nhất từ bảng users qua khoá ngoại user_id (NOT NULL, UNIQUE, ON DELETE RESTRICT).
    """

    __tablename__ = "members"
    __table_args__ = (Index("ix_members_status", "status"),)

    member_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    gender: Mapped[Gender] = mapped_column(enum_column(Gender, 10), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    join_date: Mapped[date] = mapped_column(Date, nullable=False, default=today_vn)
    status: Mapped[MemberStatus] = mapped_column(
        enum_column(MemberStatus, 20), nullable=False, default=MemberStatus.ACTIVE
    )

    user: Mapped["User"] = relationship(back_populates="member", lazy="joined")
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
    def full_name(self) -> str:
        return self.user.full_name if self.user else f"Hội viên #{self.member_id}"

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    @property
    def phone(self) -> str:
        return self.user.phone if self.user else ""

    @property
    def is_active(self) -> bool:
        return self.status == MemberStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<Member id={self.member_id} user_id={self.user_id}>"
