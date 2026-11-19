from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import TimestampMixin


class MemberCard(Base, TimestampMixin):
    __tablename__ = "member_cards"
    __table_args__ = (
        Index("ix_member_cards_card_code", "card_code"),
        Index("ix_member_cards_user_id", "user_id"),
    )

    card_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    member_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    card_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    qr_base64: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    bmi: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    target_weight_kg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 1), nullable=True
    )
    weekly_workouts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_checkins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<MemberCard id={self.card_id} user={self.user_id} code={self.card_code!r}>"
