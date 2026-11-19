from datetime import date
from typing import Optional

from sqlalchemy import CheckConstraint, Date, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import TimestampMixin


class Equipment(Base, TimestampMixin):
    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint(
            "maintenance_interval_days > 0",
            name="ck_equipment_interval_positive",
        ),
        Index("ix_equipment_zone_status", "zone", "status"),
        Index("ix_equipment_next_maintenance", "next_maintenance_date"),
    )

    equipment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    zone: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="HOAT_DONG"
    )  # HOAT_DONG, BAO_TRI, HONG
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_maintained_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    maintenance_interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Equipment id={self.equipment_id} name={self.name!r} status={self.status}>"
