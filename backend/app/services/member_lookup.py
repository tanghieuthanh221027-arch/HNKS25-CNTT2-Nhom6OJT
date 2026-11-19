from datetime import date
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.enums import SubscriptionStatus
from app.models.member import Member
from app.models.subscription import Subscription


def find_member_by_phone_or_qr(db: Session, value: str) -> Optional[Member]:
    """Find one member by exact phone number or QR card code."""
    value = value.strip()
    if not value:
        return None

    column = Member.card_code if value.startswith("DG-") else Member.phone
    statement = select(Member).where(column == value).limit(1)
    return db.scalar(statement)


def get_valid_subscription_id_for_checkin(
    db: Session, member_id: int
) -> Optional[int]:
    """Return a valid active subscription ID, or None when the card cannot check in."""
    if db.bind is not None and db.bind.dialect.name == "mysql":
        result = db.execute(
            text("CALL sp_get_valid_subscription_for_checkin(:member_id)"),
            {"member_id": member_id},
        )
        try:
            row = result.fetchone()
            subscription_id = int(row[0]) if row is not None else None
            while result.nextset():
                result.fetchall()
            return subscription_id
        finally:
            result.close()

    today = date.today()
    statement = (
        select(Subscription.subscription_id)
        .where(
            Subscription.member_id == member_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.start_date <= today,
            Subscription.end_date >= today,
        )
        .order_by(
            Subscription.end_date.desc(),
            Subscription.subscription_id.desc(),
        )
        .limit(1)
    )
    return db.scalar(statement)
