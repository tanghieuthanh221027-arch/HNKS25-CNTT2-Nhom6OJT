from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import CreatedAtMixin


class BodyMetric(Base, CreatedAtMixin):
    __tablename__ = "body_metrics"
    __table_args__ = (
        Index("ix_body_metrics_user_date", "user_id", "recorded_date"),
    )

    metric_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    recorded_date: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today
    )
    height_cm: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    bmi: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    body_fat_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    muscle_mass_kg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 1), nullable=True
    )
    waist_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<BodyMetric id={self.metric_id} user={self.user_id} date={self.recorded_date}>"
