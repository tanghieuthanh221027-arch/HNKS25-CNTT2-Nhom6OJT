from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.enums import Gender, SubscriptionStatus, SubscriptionType
from app.models.member import Member
from app.models.membership_plan import MembershipPlan
from app.models.subscription import Subscription
from app.services.member_lookup import (
    find_member_by_phone_or_qr,
    get_valid_subscription_id_for_checkin,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def create_member(db: Session) -> Member:
    member = Member(
        full_name="Nguyen Van A",
        gender=Gender.OTHER,
        date_of_birth=date(2000, 1, 1),
        phone="0901234567",
        card_code="DG-0123456789ABCDEF",
        email="member@example.test",
        address="Ha Noi",
        join_date=date.today(),
    )
    db.add(member)
    db.commit()
    return member


def test_find_member_by_phone_or_qr_exact_match(db: Session) -> None:
    member = create_member(db)

    assert find_member_by_phone_or_qr(db, member.phone) == member
    assert find_member_by_phone_or_qr(db, member.card_code) == member
    assert find_member_by_phone_or_qr(db, "090123") is None
    assert find_member_by_phone_or_qr(db, " ") is None


def test_get_valid_subscription_for_checkin_checks_dates_and_status(
    db: Session,
) -> None:
    member = create_member(db)
    plan = MembershipPlan(
        plan_name="Basic",
        category="Basic",
        duration_days=30,
        price=100,
    )
    db.add(plan)
    db.flush()
    subscription = Subscription(
        member_id=member.member_id,
        plan_id=plan.plan_id,
        subscription_type=SubscriptionType.NEW,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today(),
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(subscription)
    db.commit()

    assert (
        get_valid_subscription_id_for_checkin(db, member.member_id)
        == subscription.subscription_id
    )

    subscription.end_date = date.today() - timedelta(days=1)
    db.commit()
    assert get_valid_subscription_id_for_checkin(db, member.member_id) is None
