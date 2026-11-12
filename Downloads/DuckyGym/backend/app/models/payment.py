from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.enums import PaymentMethod, PaymentStatus, enum_column

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.user import User


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_payments_invoice_status", "invoice_id", "status"),
        Index("ix_payments_payment_date", "payment_date"),
    )

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("invoices.invoice_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    received_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        enum_column(PaymentMethod, 30), nullable=False
    )
    payment_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
    )
    status: Mapped[PaymentStatus] = mapped_column(
        enum_column(PaymentStatus, 20), nullable=False, default=PaymentStatus.PENDING
    )
    transaction_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")
    receiver: Mapped[Optional["User"]] = relationship(
        back_populates="received_payments", foreign_keys=[received_by]
    )

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.payment_id} invoice={self.invoice_id} "
            f"status={self.status.value}>"
        )
