from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.body_metric import BodyMetric
from app.models.enums import SubscriptionStatus, UserRole, UserStatus
from app.models.member import Member
from app.models.member_card import MemberCard
from app.models.membership_plan import MembershipPlan
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.user import (
    BodyMetricCreate,
    BodyMetricResponse,
    TrainerResponse,
    UserResponse,
    UserUpdateSelf,
)
from app.services.auth_service import ensure_member_and_card
from app.services.user import build_user_profile_dict, update_my_profile

router = APIRouter(prefix="/users", tags=["Users"])

allow_authenticated_roles = require_roles(
    UserRole.ADMIN,
    UserRole.STAFF,
    UserRole.CASHIER,
    UserRole.MEMBER,
    UserRole.TRAINER,
)

allow_staff_or_admin = require_roles(
    UserRole.ADMIN,
    UserRole.STAFF,
    UserRole.CASHIER,
)


@router.get("/me", response_model=UserResponse, summary="Xem hồ sơ cá nhân & BMI")
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_authenticated_roles),
) -> dict[str, Any]:
    return build_user_profile_dict(db, current_user)


@router.put("/me", response_model=UserResponse, summary="Cập nhật hồ sơ cá nhân, tính BMI & đổi mật khẩu")
def update_me(
    payload: UserUpdateSelf,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_authenticated_roles),
) -> dict[str, Any]:
    return update_my_profile(db=db, current_user=current_user, data=payload)


@router.get(
    "/body-metrics",
    response_model=list[BodyMetricResponse],
    summary="[Bonus T3CD409] Lịch sử chỉ số cơ thể (cân nặng, BMI) theo thời gian",
)
def get_my_body_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_authenticated_roles),
) -> list[BodyMetric]:
    return (
        db.query(BodyMetric)
        .filter(BodyMetric.user_id == current_user.user_id)
        .order_by(BodyMetric.recorded_date.asc(), BodyMetric.metric_id.asc())
        .all()
    )


@router.post(
    "/body-metrics",
    response_model=BodyMetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Bonus T3CD409] Ghi nhận chỉ số cơ thể mới (tự động tính BMI)",
)
def create_body_metric(
    payload: BodyMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_authenticated_roles),
) -> BodyMetric:
    bmi = round(
        payload.weight_kg / ((payload.height_cm / Decimal("100")) ** 2), 1
    )
    rec_date = payload.recorded_date or date.today()
    bm = BodyMetric(
        user_id=current_user.user_id,
        recorded_date=rec_date,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        bmi=bmi,
        body_fat_pct=payload.body_fat_pct,
        muscle_mass_kg=payload.muscle_mass_kg,
        waist_cm=payload.waist_cm,
        notes=payload.notes,
    )
    db.add(bm)

    # Đồng bộ luôn sang thẻ hội viên hiện tại
    _, card = ensure_member_and_card(db, current_user)
    if card:
        card.height_cm = payload.height_cm
        card.weight_kg = payload.weight_kg
        card.bmi = bmi

    db.commit()
    db.refresh(bm)
    return bm


@router.get(
    "/trainers",
    response_model=list[TrainerResponse],
    summary="Danh sách Huấn luyện viên (PT) đang hoạt động",
)
def list_trainers(db: Session = Depends(get_db)) -> list[User]:
    return (
        db.query(User)
        .filter(User.role == UserRole.TRAINER, User.status == UserStatus.ACTIVE)
        .order_by(User.user_id.asc())
        .all()
    )


@router.get(
    "/members",
    summary="Tìm kiếm hội viên theo SĐT, tên, email hoặc mã thẻ (Dành cho Lễ tân / Admin)",
)
def search_members(
    keyword: Optional[str] = Query(default=None, description="SĐT, họ tên, email hoặc mã hội viên"),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(allow_staff_or_admin),
) -> list[dict[str, Any]]:
    query = (
        db.query(Member, User, MemberCard)
        .outerjoin(User, User.user_id == Member.user_id)
        .outerjoin(MemberCard, MemberCard.member_id == Member.member_id)
    )
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Member.phone.ilike(kw),
                Member.full_name.ilike(kw),
                Member.email.ilike(kw),
                MemberCard.card_code.ilike(kw),
            )
        )
    rows = query.order_by(Member.member_id.asc()).limit(limit).all()
    today = date.today()
    results = []
    for member, user, card in rows:
        latest_sub = (
            db.query(Subscription, MembershipPlan)
            .join(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
            .filter(Subscription.member_id == member.member_id)
            .order_by(
                (Subscription.status == SubscriptionStatus.ACTIVE).desc(),
                Subscription.end_date.desc(),
            )
            .first()
        )
        sub_info = None
        if latest_sub:
            sub, plan = latest_sub
            days_left = (sub.end_date - today).days
            sub_info = {
                "subscription_id": sub.subscription_id,
                "plan_id": plan.plan_id,
                "plan_name": plan.plan_name,
                "start_date": sub.start_date,
                "end_date": sub.end_date,
                "status": "EXPIRED" if (sub.status == SubscriptionStatus.ACTIVE and sub.end_date < today) else sub.status.value,
                "days_remaining": days_left,
            }
        results.append(
            {
                "member_id": member.member_id,
                "user_id": member.user_id,
                "full_name": member.full_name,
                "phone": member.phone,
                "email": member.email,
                "status": member.status.value,
                "member_code": card.card_code if card else f"DG-{(member.user_id or member.member_id):06d}",
                "streak_days": card.streak_days if card else 0,
                "total_checkins": card.total_checkins if card else 0,
                "current_subscription": sub_info,
            }
        )
    return results
