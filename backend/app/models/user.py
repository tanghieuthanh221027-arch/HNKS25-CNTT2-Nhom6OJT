from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import UserRole, UserStatus, enum_column
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance_record import AttendanceRecord
    from app.models.audit_log import AuditLog
    from app.models.feedback import Feedback
    from app.models.invoice import Invoice
    from app.models.member import Member
    from app.models.notification import Notification
    from app.models.payment import Payment
    from app.models.trainer_member import TrainerMember
    from app.models.trainer_schedule import TrainerSchedule
    from app.models.training_booking import TrainingBooking


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role_status", "role", "status"),
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole, 20), nullable=False, default=UserRole.MEMBER
    )
    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        enum_column(UserStatus, 20), nullable=False, default=UserStatus.ACTIVE
    )

    member: Mapped[Optional["Member"]] = relationship(
        back_populates="user", uselist=False
    )
    trainer_schedules: Mapped[list["TrainerSchedule"]] = relationship(
        back_populates="trainer", foreign_keys="TrainerSchedule.trainer_id"
    )
    trainer_assignments: Mapped[list["TrainerMember"]] = relationship(
        back_populates="trainer", foreign_keys="TrainerMember.trainer_id"
    )
    made_assignments: Mapped[list["TrainerMember"]] = relationship(
        back_populates="assigner", foreign_keys="TrainerMember.assigned_by"
    )
    training_bookings: Mapped[list["TrainingBooking"]] = relationship(
        back_populates="trainer", foreign_keys="TrainingBooking.trainer_id"
    )
    created_invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="creator", foreign_keys="Invoice.created_by"
    )
    received_payments: Mapped[list["Payment"]] = relationship(
        back_populates="receiver", foreign_keys="Payment.received_by"
    )
    checked_in_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="checker", foreign_keys="AttendanceRecord.checked_in_by"
    )
    handled_feedbacks: Mapped[list["Feedback"]] = relationship(
        back_populates="handler", foreign_keys="Feedback.handled_by"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")

    @property
    def is_trainer(self) -> bool:
        return self.role == UserRole.TRAINER

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<User id={self.user_id} username={self.username!r} role={self.role.value}>"
