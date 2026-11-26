import os
import smtplib
from datetime import date, timedelta
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exception import BusinessRuleException, NotFoundException
from app.core.qr_utils import generate_card_code, generate_qr_base64
from app.core.timezone_utils import today_vn
from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_staff_or_admin
from app.models.discount import Discount
from app.models.enums import (
    InvoiceStatus,
    NotificationType,
    PaymentMethod,
    PaymentStatus,
    PlanStatus,
    SubscriptionStatus,
    SubscriptionType,
)
from app.models.invoice import Invoice
from app.models.member import Member
from app.models.membership_plan import MembershipPlan
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.auth_service import ensure_member_and_card
from app.services.user import compute_badges

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & QR Card"])


class SubscriptionCreateRequest(BaseModel):
    plan_id: int = Field(gt=0)
    payment_method: str = Field(default="BANK_TRANSFER")
    discount_code: Optional[str] = None
    start_date: Optional[date] = None


def _send_expiry_email_task(recipient_email: str, full_name: str, plan_name: str, end_date_str: str) -> None:
    """Gửi email nhắc thẻ sắp hết hạn qua SMTP Gmail App Password (chạy ngầm với BackgroundTasks)."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    if not smtp_user or not smtp_pass:
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Ducky Gym] Thông báo gói tập {plan_name} sắp hết hạn ({end_date_str})"
        msg["From"] = f"Ducky Gym Club <{smtp_user}>"
        msg["To"] = recipient_email

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background: #0b1326; color: #e3e9f7; border-radius: 12px;">
            <h2 style="color: #f97316; margin-top: 0;">DUCKY GYM PERFORMANCE CLUB</h2>
            <p>Xin chào <b>{full_name}</b>,</p>
            <p>Thẻ hội viên của bạn với gói tập <b>{plan_name}</b> sẽ hết hạn vào ngày <b>{end_date_str}</b>.</p>
            <p>Hãy gia hạn sớm trên website hoặc tại quầy lễ tân để duy trì chuỗi ngày tập luyện và nhận ưu đãi hội viên thân thiết nhé!</p>
            <p style="margin-top: 24px; font-size: 12px; color: #9ca8bf;">Hotline hỗ trợ 24/7: 1900 6868 · 123 Hà Đông, Hà Nội</p>
        </div>
        """
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [recipient_email], msg.as_string())
    except Exception:
        pass


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="[Task T067E0D] Hội viên đăng ký gói tập (tự nối tiếp hạn thẻ & sinh mã QR)",
)
def create_subscription(
    payload: SubscriptionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    plan = (
        db.query(MembershipPlan)
        .filter(
            MembershipPlan.plan_id == payload.plan_id,
            MembershipPlan.status == PlanStatus.ACTIVE,
        )
        .first()
    )
    if not plan:
        raise NotFoundException("Gói tập không tồn tại hoặc đã ngừng kinh doanh.")

    member, card = ensure_member_and_card(db, current_user)
    if not member or not card:
        raise BusinessRuleException("Tài khoản này không phải hội viên để đăng ký gói tập.")

    today = today_vn()
    # Tự động khoá các gói đã quá hạn
    overdue_subs = (
        db.query(Subscription)
        .filter(
            Subscription.member_id == member.member_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date < today,
        )
        .all()
    )
    for ov in overdue_subs:
        ov.status = SubscriptionStatus.EXPIRED

    # Kiểm tra thẻ còn hạn hiện tại để nối tiếp ngày hết hạn (Task T067E0D)
    active_sub = (
        db.query(Subscription)
        .filter(
            Subscription.member_id == member.member_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date >= today,
        )
        .order_by(Subscription.end_date.desc())
        .first()
    )

    if active_sub:
        start_date = active_sub.end_date + timedelta(days=1)
        sub_type = SubscriptionType.RENEW
        prev_sub_id = active_sub.subscription_id
    else:
        start_date = payload.start_date if (payload.start_date and payload.start_date >= today) else today
        sub_type = SubscriptionType.NEW
        prev_sub_id = None

    end_date = start_date + timedelta(days=plan.duration_days)

    # Áp dụng mã giảm giá nếu có
    total_amount = plan.price
    discount_amount = Decimal("0.00")
    if payload.discount_code and payload.discount_code.strip():
        code_str = payload.discount_code.strip().upper()
        disc = db.query(Discount).filter(Discount.code == code_str, Discount.is_active == True).first()  # noqa: E712
        if not disc or disc.expiry_date < today or disc.used_count >= disc.usage_limit:
            raise BusinessRuleException("Mã giảm giá không hợp lệ, đã hết hạn hoặc hết lượt sử dụng.")
        if total_amount < disc.min_order_amount:
            raise BusinessRuleException(
                f"Đơn hàng tối thiểu để áp dụng mã {code_str} là {int(disc.min_order_amount):,} đ."
            )
        if disc.discount_type == "PERCENT":
            discount_amount = (total_amount * disc.discount_value) / Decimal("100")
            if disc.max_discount_amount and discount_amount > disc.max_discount_amount:
                discount_amount = disc.max_discount_amount
        else:
            discount_amount = min(total_amount, disc.discount_value)
        discount_amount = round(discount_amount, 2)
        disc.used_count += 1

    final_amount = max(Decimal("0.00"), total_amount - discount_amount)

    new_sub = Subscription(
        member_id=member.member_id,
        plan_id=plan.plan_id,
        subscription_type=sub_type,
        previous_subscription_id=prev_sub_id,
        start_date=start_date,
        end_date=end_date,
        total_sessions=plan.pt_sessions,
        sessions_remaining=plan.pt_sessions,
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(new_sub)
    db.flush()

    # Đảm bảo mã thẻ ngẫu nhiên khó đoán & ảnh QR base64 luôn mới
    if not card.card_code:
        card.card_code = generate_card_code(current_user.user_id)
    card.qr_base64 = generate_qr_base64(card.card_code)

    pay_method = (
        PaymentMethod.CASH
        if payload.payment_method.upper() in ("CASH", "TIEN_MAT")
        else PaymentMethod.BANK_TRANSFER
    )
    inv = Invoice(
        member_id=member.member_id,
        subscription_id=new_sub.subscription_id,
        created_by=current_user.user_id,
        total_amount=total_amount,
        discount_amount=discount_amount,
        final_amount=final_amount,
        status=InvoiceStatus.PAID,
    )
    db.add(inv)
    db.flush()

    payment = Payment(
        invoice_id=inv.invoice_id,
        received_by=current_user.user_id,
        amount=final_amount if final_amount > 0 else Decimal("1.00"),
        payment_method=pay_method,
        status=PaymentStatus.SUCCESS,
        transaction_code=f"SUB-{new_sub.subscription_id:06d}-{current_user.user_id}",
    )
    db.add(payment)
    db.commit()
    db.refresh(new_sub)

    effective_end_date = end_date
    days_remaining = (effective_end_date - today).days

    return {
        "message": (
            f"Gia hạn gói {plan.plan_name} thành công! Hạn thẻ mới đến {effective_end_date.strftime('%d/%m/%Y')}."
            if sub_type == SubscriptionType.RENEW
            else f"Đăng ký gói {plan.plan_name} thành công!"
        ),
        "subscription_id": new_sub.subscription_id,
        "subscription_type": sub_type.value,
        "plan_id": plan.plan_id,
        "plan_name": plan.plan_name,
        "duration_days": plan.duration_days,
        "total_sessions": new_sub.total_sessions,
        "sessions_remaining": new_sub.sessions_remaining,
        "start_date": start_date,
        "end_date": effective_end_date,
        "days_remaining": days_remaining,
        "status": new_sub.status.value,
        "total_amount": total_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "card_code": card.card_code,
        "qr_base64": card.qr_base64,
    }


@router.get(
    "/me",
    summary="[Task T067E0D & T3CD518] Xem thẻ hội viên điện tử hiện tại, chuỗi base64 QR, streak & huy hiệu",
)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    member, card = ensure_member_and_card(db, current_user)
    today = today_vn()

    if card and not card.qr_base64:
        card.qr_base64 = generate_qr_base64(card.card_code)
        db.commit()

    active_subs: list[tuple[Subscription, MembershipPlan]] = []
    latest_sub_tuple: Optional[tuple[Subscription, MembershipPlan]] = None

    if member:
        # Tự động chuyển các gói đã quá hạn sang EXPIRED
        all_subs = (
            db.query(Subscription, MembershipPlan)
            .join(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
            .filter(Subscription.member_id == member.member_id)
            .order_by(Subscription.end_date.desc())
            .all()
        )
        dirty = False
        for s, _p in all_subs:
            if s.status == SubscriptionStatus.ACTIVE and s.end_date < today:
                s.status = SubscriptionStatus.EXPIRED
                dirty = True
        if dirty:
            db.commit()

        active_subs = [
            (s, p)
            for s, p in all_subs
            if s.status == SubscriptionStatus.ACTIVE and s.end_date >= today
        ]
        if all_subs:
            latest_sub_tuple = active_subs[0] if active_subs else all_subs[0]

    card_code = card.card_code if card else f"DG-{current_user.user_id:06d}"
    qr_b64 = card.qr_base64 if (card and card.qr_base64) else generate_qr_base64(card_code)
    streak = card.streak_days if card else 0
    total_ci = card.total_checkins if card else 0

    if not latest_sub_tuple:
        return {
            "has_subscription": False,
            "card_status": "NO_SUBSCRIPTION",
            "member_name": current_user.full_name,
            "member_code": card_code,
            "qr_base64": qr_b64,
            "plan_name": "Chưa đăng ký gói tập",
            "start_date": None,
            "end_date": None,
            "days_remaining": 0,
            "total_sessions": 0,
            "sessions_remaining": 0,
            "near_expiry_warning": False,
            "warning_message": "Bạn chưa có gói tập đang hoạt động. Hãy đăng ký gói tập để kích hoạt thẻ QR.",
            "streak_days": streak,
            "total_checkins": total_ci,
            "badges": compute_badges(total_ci, streak),
            "history": [],
        }

    latest_sub, latest_plan = latest_sub_tuple
    earliest_start = min((s.start_date for s, _ in active_subs), default=latest_sub.start_date)
    furthest_end = max((s.end_date for s, _ in active_subs), default=latest_sub.end_date)
    total_pt_sessions = sum((s.total_sessions for s, _ in active_subs), 0)
    pt_sessions_remaining = sum((s.sessions_remaining for s, _ in active_subs), 0)
    days_remaining = (furthest_end - today).days
    is_active = latest_sub.status == SubscriptionStatus.ACTIVE and furthest_end >= today
    near_expiry = is_active and 0 <= days_remaining <= 7

    warning_msg = None
    if not is_active:
        warning_msg = f"Thẻ hội viên của bạn đã hết hạn vào ngày {furthest_end.strftime('%d/%m/%Y')}. Vui lòng gia hạn!"
    elif near_expiry:
        warning_msg = f"Thẻ hội viên sắp hết hạn trong {days_remaining} ngày ({furthest_end.strftime('%d/%m/%Y')}). Hãy gia hạn sớm!"

    return {
        "has_subscription": True,
        "subscription_id": latest_sub.subscription_id,
        "card_status": "ACTIVE" if is_active else "EXPIRED",
        "member_name": current_user.full_name,
        "member_code": card_code,
        "qr_base64": qr_b64,
        "plan_id": latest_plan.plan_id,
        "plan_name": latest_plan.plan_name,
        "category": latest_plan.category,
        "price": latest_plan.price,
        "start_date": earliest_start,
        "end_date": furthest_end,
        "days_remaining": max(0, days_remaining),
        "total_sessions": total_pt_sessions,
        "sessions_remaining": pt_sessions_remaining,
        "near_expiry_warning": near_expiry,
        "warning_message": warning_msg,
        "streak_days": streak,
        "total_checkins": total_ci,
        "badges": compute_badges(total_ci, streak),
    }


@router.get(
    "/expiring-soon",
    summary="[Bonus T3CD43D] Danh sách hội viên có thẻ sắp hết hạn trong N ngày (mặc định 3-7 ngày)",
)
def list_expiring_subscriptions(
    within_days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    today = today_vn()
    cutoff = today + timedelta(days=within_days)
    rows = (
        db.query(Subscription, Member, MembershipPlan)
        .join(Member, Member.member_id == Subscription.member_id)
        .join(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
        .filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date >= today,
            Subscription.end_date <= cutoff,
        )
        .order_by(Subscription.end_date.asc())
        .all()
    )
    items = []
    for sub, mem, plan in rows:
        days_left = (sub.end_date - today).days
        items.append(
            {
                "subscription_id": sub.subscription_id,
                "member_id": mem.member_id,
                "user_id": mem.user_id,
                "full_name": mem.full_name,
                "email": mem.email,
                "phone": mem.phone,
                "plan_name": plan.plan_name,
                "end_date": sub.end_date,
                "days_remaining": days_left,
            }
        )
    return {
        "within_days": within_days,
        "total": len(items),
        "items": items,
    }


@router.post(
    "/send-expiry-reminders",
    summary="[Bonus T3CD43D] Gửi email nhắc thẻ sắp hết hạn trong 3 ngày (BackgroundTasks + SMTP)",
)
def send_expiry_reminders(
    background_tasks: BackgroundTasks,
    within_days: int = Query(default=3, ge=1, le=14),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    today = today_vn()
    cutoff = today + timedelta(days=within_days)
    rows = (
        db.query(Subscription, Member, MembershipPlan)
        .join(Member, Member.member_id == Subscription.member_id)
        .join(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
        .filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date >= today,
            Subscription.end_date <= cutoff,
        )
        .all()
    )

    recipients = []
    for sub, mem, plan in rows:
        end_str = sub.end_date.strftime("%d/%m/%Y")
        background_tasks.add_task(
            _send_expiry_email_task,
            mem.email,
            mem.full_name,
            plan.plan_name,
            end_str,
        )
        if mem.user_id:
            notif = Notification(
                user_id=mem.user_id,
                title=f"Nhắc hạn thẻ tập: Gói {plan.plan_name}",
                content=f"Thẻ hội viên của bạn sẽ hết hạn vào ngày {end_str}. Vui lòng gia hạn để không gián đoạn lịch tập.",
                type=NotificationType.SUBSCRIPTION_EXPIRY,
                is_read=False,
            )
            db.add(notif)
        recipients.append(
            {
                "member_id": mem.member_id,
                "full_name": mem.full_name,
                "email": mem.email,
                "plan_name": plan.plan_name,
                "end_date": sub.end_date,
            }
        )

    db.commit()
    return {
        "message": f"Đã đưa {len(recipients)} email nhắc hạn thẻ (còn <= {within_days} ngày) vào hàng đợi gửi ngầm (BackgroundTasks).",
        "queued_count": len(recipients),
        "recipients": recipients,
    }
