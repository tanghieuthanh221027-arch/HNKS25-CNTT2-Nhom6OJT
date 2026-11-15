import base64
import io
import secrets
from datetime import date, timedelta

import qrcode
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.exception import BusinessRuleException, NotFoundException
from models.enums import (
    Gender,
    MemberStatus,
    SubscriptionStatus,
    SubscriptionType,
)
from models.member import Member
from models.membership_plan import MembershipPlan
from models.subscription import Subscription
from models.user import User
from schemas.subscription import SubscriptionDetailResponse, SubscriptionSelfCreate


def _generate_unique_card_code(db: Session) -> str:
    """Sinh mã thẻ ngẫu nhiên khó đoán và đảm bảo duy nhất trong CSDL."""
    while True:
        code = f"DG-{secrets.token_hex(8).upper()}"
        exists = db.scalar(select(Member.member_id).where(Member.card_code == code))
        if not exists:
            return code


def generate_qr_base64(data: str) -> str:
    """Sinh ảnh QR từ chuỗi mã thẻ và trả về định dạng chuỗi base64."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _get_or_create_member_for_user(db: Session, user: User) -> Member:
    """Lấy hồ sơ hội viên của User (tự động khởi tạo nếu chưa có) và đảm bảo có card_code cố định."""
    member = db.scalar(select(Member).where(Member.user_id == user.user_id))
    if member is None:
        # Thử tìm theo email hoặc phone nếu đã tồn tại hồ sơ rời
        member = db.scalar(
            select(Member).where(
                (Member.email == user.email) | (Member.phone == user.phone)
            )
        )
        if member is not None and member.user_id is None:
            member.user_id = user.user_id
        else:
            member = Member(
                user_id=user.user_id,
                card_code=_generate_unique_card_code(db),
                full_name=user.full_name,
                gender=Gender.OTHER,
                date_of_birth=date(2000, 1, 1),
                phone=user.phone,
                email=user.email,
                address="Chưa cập nhật",
                join_date=date.today(),
                status=MemberStatus.ACTIVE,
            )
            db.add(member)
            db.flush()

    if not member.card_code:
        member.card_code = _generate_unique_card_code(db)
        db.flush()

    return member


def _build_subscription_detail_response(
    subscription: Subscription,
    member: Member,
) -> SubscriptionDetailResponse:
    """Đóng gói dữ liệu Subscription kèm card_code, qr_code base64 và days_remaining."""
    today = date.today()
    days_remaining = max(0, (subscription.end_date - today).days)
    qr_b64 = generate_qr_base64(member.card_code) if member.card_code else None

    response = SubscriptionDetailResponse.model_validate(subscription)
    response.card_code = member.card_code
    response.qr_code = qr_b64
    response.days_remaining = days_remaining
    return response


def create_my_subscription(
    db: Session,
    current_user: User,
    payload: SubscriptionSelfCreate,
) -> SubscriptionDetailResponse:
    member = _get_or_create_member_for_user(db, current_user)
    if not member.is_active:
        raise BusinessRuleException("Hồ sơ hội viên đang ngừng hoạt động, không thể đăng ký gói tập")

    plan = db.get(MembershipPlan, payload.plan_id)
    if plan is None:
        raise NotFoundException("Không tìm thấy gói tập yêu cầu")
    if not plan.is_available:
        raise BusinessRuleException("Gói tập này hiện đã ngừng kinh doanh")

    today = date.today()

    # Tìm thẻ ACTIVE còn hạn hiện tại của hội viên
    active_sub = db.scalar(
        select(Subscription)
        .where(
            Subscription.member_id == member.member_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date >= today,
        )
        .order_by(Subscription.end_date.desc(), Subscription.subscription_id.desc())
    )

    if active_sub is not None:
        # Phương án 2: Gia hạn nối tiếp, đóng gói cũ sang EXPIRED và cộng dồn hạn vào gói mới ACTIVE
        sub_type = SubscriptionType.RENEW
        prev_sub_id = active_sub.subscription_id
        start_date = active_sub.start_date
        end_date = active_sub.end_date + timedelta(days=plan.duration_days)
        active_sub.status = SubscriptionStatus.EXPIRED
    else:
        # Đăng ký mới hoặc thẻ cũ đã hết hạn
        sub_type = SubscriptionType.NEW
        prev_sub_id = None
        start_date = payload.start_date if payload.start_date and payload.start_date >= today else today
        end_date = start_date + timedelta(days=plan.duration_days)

    new_sub = Subscription(
        member_id=member.member_id,
        plan_id=plan.plan_id,
        subscription_type=sub_type,
        previous_subscription_id=prev_sub_id,
        start_date=start_date,
        end_date=end_date,
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(new_sub)
    db.commit()

    # Truy vấn lại kèm quan hệ plan và member để trả về đầy đủ chi tiết
    stmt = (
        select(Subscription)
        .options(joinedload(Subscription.plan), joinedload(Subscription.member))
        .where(Subscription.subscription_id == new_sub.subscription_id)
    )
    saved_sub = db.scalar(stmt)
    return _build_subscription_detail_response(saved_sub, member)


def get_my_current_subscription(
    db: Session,
    current_user: User,
) -> SubscriptionDetailResponse:
    member = db.scalar(select(Member).where(Member.user_id == current_user.user_id))
    if member is None:
        raise NotFoundException("Tài khoản chưa có hồ sơ hội viên hoặc chưa đăng ký gói tập")

    if not member.card_code:
        member.card_code = _generate_unique_card_code(db)
        db.commit()
        db.refresh(member)

    today = date.today()
    stmt = (
        select(Subscription)
        .options(joinedload(Subscription.plan), joinedload(Subscription.member))
        .where(
            Subscription.member_id == member.member_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date >= today,
        )
        .order_by(Subscription.end_date.desc(), Subscription.subscription_id.desc())
    )
    current_sub = db.scalar(stmt)

    if current_sub is None:
        raise NotFoundException("Hội viên hiện không có thẻ tập nào đang còn hạn")

    return _build_subscription_detail_response(current_sub, member)