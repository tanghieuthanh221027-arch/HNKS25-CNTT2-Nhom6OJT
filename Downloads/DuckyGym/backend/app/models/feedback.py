from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.enums import (
    FEEDBACK_TRANSITIONS,
    FeedbackStatus,
    FeedbackType,
    enum_column,
)
from models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from models.member import Member
    from models.user import User


class Feedback(Base, CreatedAtMixin):
    __tablename__ = "feedbacks"
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)", name="rating_range"
        ),
        Index("ix_feedbacks_member_type", "member_id", "type"),
        Index("ix_feedbacks_status_created_at", "status", "created_at"),
    )

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    handled_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    type: Mapped[FeedbackType] = mapped_column(
        "type", enum_column(FeedbackType, 20), nullable=False
    )
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeedbackStatus] = mapped_column(
        enum_column(FeedbackStatus, 20), nullable=False, default=FeedbackStatus.PENDING
    )
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    member: Mapped["Member"] = relationship(back_populates="feedbacks")
    handler: Mapped[Optional["User"]] = relationship(
        back_populates="handled_feedbacks", foreign_keys=[handled_by]
    )

    def can_transition_to(self, new_status: FeedbackStatus) -> bool:
        return new_status in FEEDBACK_TRANSITIONS[self.status]

    def __repr__(self) -> str:
        return (
            f"<Feedback id={self.feedback_id} type={self.type.value} "
            f"status={self.status.value}>"
        )
