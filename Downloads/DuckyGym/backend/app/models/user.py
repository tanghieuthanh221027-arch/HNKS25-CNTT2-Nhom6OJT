import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from db.database import Base
from models.enums import UserRole, UserStatus, enum_column
from models.mixins import TimestampMixin

if TYPE_CHECKING:
    from models.attendance_record import AttendanceRecord
    from models.audit_log import AuditLog
    from models.feedback import Feedback
    from models.invoice import Invoice
    from models.member import Member
    from models.notification import Notification
    from models.payment import Payment
    from models.trainer_member import TrainerMember
    from models.trainer_schedule import TrainerSchedule
    from models.training_booking import TrainingBooking


EMPLOYEE_ROLES = frozenset(
    {UserRole.ADMIN, UserRole.STAFF, UserRole.CASHIER, UserRole.TRAINER}
)

_TRAINER = UserRole.TRAINER.value
_MEMBER = UserRole.MEMBER.value

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role_status", "role", "status"),
        CheckConstraint(
            "salary IS NULL OR salary >= 0", name="ck_users_salary_non_negative"
        ),
        CheckConstraint(
            "experience_years IS NULL OR experience_years >= 0",
            name="ck_users_experience_non_negative",
        ),
        CheckConstraint(
            f"role = '{_TRAINER}' OR "
            "(specialization IS NULL AND experience_years IS NULL AND bio IS NULL)",
            name="ck_users_trainer_only_fields",
        ),
        CheckConstraint(
            f"role <> '{_MEMBER}' OR "
            "(position IS NULL AND hire_date IS NULL AND salary IS NULL)",
            name="ck_users_member_no_staff_fields",
        ),
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole, 20), nullable=False, default=UserRole.MEMBER
    )
    status: Mapped[UserStatus] = mapped_column(
        enum_column(UserStatus, 20), nullable=False, default=UserStatus.ACTIVE
    )

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    member: Mapped[Optional["Member"]] = relationship(
        back_populates="user", uselist=False
    )

    trainer_schedules: Mapped[list["TrainerSchedule"]] = relationship(
        back_populates="trainer", foreign_keys="TrainerSchedule.trainer_id"
    )
    trainer_assignments: Mapped[list["TrainerMember"]] = relationship(
        back_populates="trainer", foreign_keys="TrainerMember.trainer_id"
    )
    training_bookings: Mapped[list["TrainingBooking"]] = relationship(
        back_populates="trainer", foreign_keys="TrainingBooking.trainer_id"
    )

    made_assignments: Mapped[list["TrainerMember"]] = relationship(
        back_populates="assigner", foreign_keys="TrainerMember.assigned_by"
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

    @validates("username")
    def _normalize_username(self, _key: str, value: str) -> str:
        return value.strip()

    @validates("email")
    def _normalize_email(self, _key: str, value: str) -> str:
        return value.strip().lower()

    @validates("phone")
    def _normalize_phone(self, _key: str, value: str) -> str:
        return re.sub(r"[^\d+]", "", value)

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    @property
    def is_locked(self) -> bool:
        return self.status == UserStatus.LOCKED

    @property
    def can_login(self) -> bool:
        """BR02: tài khoản bị khóa không thể đăng nhập (INACTIVE cũng bị chặn)."""
        return self.status == UserStatus.ACTIVE

    def has_role(self, *roles: UserRole) -> bool:
        return self.role in roles

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_trainer(self) -> bool:
        return self.role == UserRole.TRAINER

    @property
    def is_employee(self) -> bool:
        return self.role in EMPLOYEE_ROLES

    @property
    def can_be_assigned_to_members(self) -> bool:
        """BR12 / UC05: chỉ PT đang hoạt động mới được phân công hoặc đặt lịch."""
        return self.is_trainer and self.is_active

    def __repr__(self) -> str:
        return f"<User id={self.user_id} username={self.username!r} role={self.role.value}>"
