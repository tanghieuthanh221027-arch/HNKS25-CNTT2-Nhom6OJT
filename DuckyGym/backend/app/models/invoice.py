from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import InvoiceStatus, enum_column
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.payment import Payment
    from app.models.subscription import Subscription
    from app.models.user import User


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="total_non_negative"),
        CheckConstraint("discount_amount >= 0", name="discount_non_negative"),
        CheckConstraint("discount_amount <= total_amount", name="discount_within_total"),
        CheckConstraint(
            "final_amount = total_amount - discount_amount", name="final_amount_formula"
        ),
        Index("ix_invoices_member_status", "member_id", "status"),
        Index("ix_invoices_status_created_at", "status", "created_at"),
    )

    invoice_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("members.member_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "subscriptions.subscription_id", ondelete="RESTRICT", onupdate="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    final_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        enum_column(InvoiceStatus, 20), nullable=False, default=InvoiceStatus.UNPAID
    )

    member: Mapped["Member"] = relationship(back_populates="invoices")
    subscription: Mapped["Subscription"] = relationship(back_populates="invoices")
    creator: Mapped["User"] = relationship(
        back_populates="created_invoices", foreign_keys=[created_by]
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice", order_by="Payment.payment_date"
    )

    @staticmethod
    def compute_final_amount(total_amount: Decimal, discount_amount: Decimal) -> Decimal:
        return total_amount - discount_amount

    def __repr__(self) -> str:
        return f"<Invoice id={self.invoice_id} status={self.status.value}>"
