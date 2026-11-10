from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import AssignmentStatus, enum_column

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.user import User


class TrainerMember(Base):
    __tablename__ = "trainer_members"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="date_range_valid"
        ),
        Index("ix_trainer_members_trainer_status", "trainer_id", "status"),
        Index("ix_trainer_members_member_status", "member_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    assigned_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[AssignmentStatus] = mapped_column(
        enum_column(AssignmentStatus, 20),
        nullable=False,
        default=AssignmentStatus.ACTIVE,
    )

    trainer: Mapped["User"] = relationship(
        back_populates="trainer_assignments", foreign_keys=[trainer_id]
    )
    member: Mapped["Member"] = relationship(back_populates="trainer_assignments")
    assigner: Mapped["User"] = relationship(
        back_populates="made_assignments", foreign_keys=[assigned_by]
    )

    def __repr__(self) -> str:
        return (
            f"<TrainerMember id={self.id} trainer={self.trainer_id} "
            f"member={self.member_id} status={self.status.value}>"
        )
