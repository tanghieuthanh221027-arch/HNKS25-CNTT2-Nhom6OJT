from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exception import BusinessRuleException, NotFoundException
from app.core.qr_utils import generate_card_code, generate_qr_base64
from app.core.security import hash_password
from app.core.timezone_utils import now_vn, today_vn
from app.db.database import get_db
from app.dependencies.auth import require_staff_or_admin
from app.models.discount import Discount
from app.models.enums import (
    Gender,
    InvoiceStatus,
    MemberStatus,
    PaymentMethod,
    PaymentStatus,
    PlanStatus,
    SubscriptionStatus,
    SubscriptionType,
    UserRole,
    UserStatus,
)
from app.models.invoice import Invoice
from app.models.member import Member
from app.models.member_card import MemberCard
from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(prefix="/pos", tags=["Reception POS & Invoices"])


class POSCheckoutRequest(BaseModel):
    phone: str = Field(min_length=9, max_length=20, description="Số điện thoại hội viên")
    full_name: Optional[str] = Field(default=None, description="Tên hội viên (nếu tạo nhanh tại quầy)")
    email: Optional[str] = None
    plan_id: int = Field(gt=0)
    subscription_mode: str = Field(default="AUTO", description="NEW, RENEW hoặc AUTO")
    discount_code: Optional[str] = None
    payment_method: str = Field(default="CASH", description="CASH hoặc BANK_TRANSFER")


@router.get(
    "/member-lookup",
    summary="[Task T067DF1] Tìm nhanh hội viên theo SĐT tại quầy POS (< 1 giây)",
)
def lookup_member_by_phone(
    phone: str = Query(min_length=3, max_length=30),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    clean_phone = phone.strip()
    member = (
        db.query(Member)
        .join(User, User.user_id == Member.user_id)
        .filter(
            or_(
                User.phone == clean_phone,
                User.phone.ilike(f"%{clean_phone}%"),
                User.full_name.ilike(f"%{clean_phone}%"),
            )
        )
        .first()
    )
    if not member:
        return {
            "found": False,
            "phone": clean_phone,
            "message": "Chưa tìm thấy hội viên với SĐT này. Bạn có thể nhập Họ tên để đăng ký nhanh tại quầy.",
        }

    card = db.query(MemberCard).filter(MemberCard.member_id == member.member_id).first()
    today = today_vn()
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

    sub_data = None
    if latest_sub:
        sub, plan = latest_sub
        is_active = sub.status == SubscriptionStatus.ACTIVE and sub.end_date >= today
        sub_data = {
            "subscription_id": sub.subscription_id,
            "plan_id": plan.plan_id,
            "plan_name": plan.plan_name,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "status": "ACTIVE" if is_active else "EXPIRED",
            "days_remaining": (sub.end_date - today).days,
        }

    return {
        "found": True,
        "member_id": member.member_id,
        "user_id": member.user_id,
        "full_name": member.full_name,
        "phone": member.phone,
        "email": member.email,
        "member_code": card.card_code if card else f"DG-{member.member_id:06d}",
        "current_subscription": sub_data,
    }


@router.post(
    "/checkout",
    status_code=status.HTTP_201_CREATED,
    summary="[Task T067DF1] Thanh toán tại quầy POS (Lưu hóa đơn & cập nhật hạn thẻ trong 1 Transaction)",
)
def pos_checkout(
    payload: POSCheckoutRequest,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    clean_phone = payload.phone.strip()
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

    today = today_vn()

    try:
        # 1. Tìm hoặc tạo nhanh hội viên tại quầy trong cùng 1 transaction (Chuẩn 3NF: User <-> Member 1-1)
        existing_user = db.query(User).filter(User.phone == clean_phone).first()
        member = (
            db.query(Member).filter(Member.user_id == existing_user.user_id).first()
            if existing_user
            else None
        )
        if not member:
            if existing_user and existing_user.role != UserRole.MEMBER:
                raise BusinessRuleException("Số điện thoại này thuộc tài khoản nhân sự, không thể đăng ký hội viên.")
            if not existing_user:
                if not payload.full_name or len(payload.full_name.strip()) < 2:
                    raise BusinessRuleException(
                        "Không tìm thấy hội viên theo SĐT này. Vui lòng nhập Họ và tên để tạo hồ sơ hội viên mới tại quầy."
                    )
                auto_email = (
                    payload.email.strip().lower()
                    if (payload.email and payload.email.strip())
                    else f"pos_{clean_phone}@duckygym.vn"
                )
                auto_username = f"hv_{clean_phone}"
                existing_user = User(
                    username=auto_username,
                    password_hash=hash_password("Member123"),
                    full_name=payload.full_name.strip(),
                    email=auto_email,
                    phone=clean_phone,
                    role=UserRole.MEMBER,
                    status=UserStatus.ACTIVE,
                )
                db.add(existing_user)
                db.flush()

            member = Member(
                user_id=existing_user.user_id,
                gender=Gender.MALE,
                date_of_birth=date(1998, 1, 1),
                address="Đăng ký tại quầy POS",
                join_date=today,
                status=MemberStatus.ACTIVE,
            )
            db.add(member)
            db.flush()

        card = db.query(MemberCard).filter(MemberCard.member_id == member.member_id).first()
        if not card and member.user_id:
            card = db.query(MemberCard).filter(MemberCard.user_id == member.user_id).first()
        if not card and member.user_id:
            c_code = generate_card_code(member.user_id)
            card = MemberCard(
                user_id=member.user_id,
                member_id=member.member_id,
                card_code=c_code,
                qr_base64=generate_qr_base64(c_code),
            )
            db.add(card)
            db.flush()

        # 2. Kiểm tra thẻ còn hạn hiện tại để nối tiếp hạn thẻ
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
            start_dt = active_sub.end_date + timedelta(days=1)
            sub_type = SubscriptionType.RENEW
            prev_sub_id = active_sub.subscription_id
        else:
            start_dt = today
            sub_type = SubscriptionType.NEW
            prev_sub_id = None

        end_dt = start_dt + timedelta(days=plan.duration_days)

        # 3. Kiểm tra & áp dụng Voucher (nếu có)
        total_amount = plan.price
        discount_amount = Decimal("0.00")
        applied_voucher = None

        if payload.discount_code and payload.discount_code.strip():
            v_code = payload.discount_code.strip().upper()
            disc = db.query(Discount).filter(Discount.code == v_code).first()
            if not disc or not disc.is_active:
                raise BusinessRuleException(f"Mã voucher '{v_code}' không tồn tại hoặc đã bị khóa.")
            if disc.expiry_date < today:
                raise BusinessRuleException(f"Mã voucher '{v_code}' đã hết hạn sử dụng.")
            if disc.used_count >= disc.usage_limit:
                raise BusinessRuleException(f"Mã voucher '{v_code}' đã hết lượt sử dụng.")
            if total_amount < disc.min_order_amount:
                raise BusinessRuleException(
                    f"Gói tập chưa đạt giá trị tối thiểu {int(disc.min_order_amount):,} đ để áp mã '{v_code}'."
                )

            if disc.discount_type == "PERCENT":
                discount_amount = (total_amount * disc.discount_value) / Decimal("100")
                if disc.max_discount_amount and discount_amount > disc.max_discount_amount:
                    discount_amount = disc.max_discount_amount
            else:
                discount_amount = min(total_amount, disc.discount_value)

            discount_amount = round(discount_amount, 2)
            disc.used_count += 1
            applied_voucher = disc.code

        final_amount = max(Decimal("0.00"), total_amount - discount_amount)

        # 4. Tạo Subscription mới / gia hạn (cấp số buổi PT theo gói tập - Mục 3.2.4)
        new_sub = Subscription(
            member_id=member.member_id,
            plan_id=plan.plan_id,
            subscription_type=sub_type,
            previous_subscription_id=prev_sub_id,
            start_date=start_dt,
            end_date=end_dt,
            total_sessions=plan.pt_sessions,
            sessions_remaining=plan.pt_sessions,
            status=SubscriptionStatus.ACTIVE,
        )
        db.add(new_sub)
        db.flush()

        # 5. Tạo Hóa đơn (Invoice) & Thanh toán (Payment)
        inv = Invoice(
            member_id=member.member_id,
            subscription_id=new_sub.subscription_id,
            created_by=current_staff.user_id,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            status=InvoiceStatus.PAID,
        )
        db.add(inv)
        db.flush()

        pay_method = (
            PaymentMethod.BANK_TRANSFER
            if payload.payment_method.strip().upper() in ("BANK_TRANSFER", "QR", "TRANSFER", "CHUYEN_KHOAN")
            else PaymentMethod.CASH
        )
        pay = Payment(
            invoice_id=inv.invoice_id,
            received_by=current_staff.user_id,
            amount=final_amount if final_amount > 0 else Decimal("1.00"),
            payment_method=pay_method,
            status=PaymentStatus.SUCCESS,
            transaction_code=f"POS-{inv.invoice_id:06d}-{int(now_vn().timestamp())}",
        )
        db.add(pay)

        # Commit toàn bộ trong 1 Transaction duy nhất
        db.commit()
        db.refresh(inv)
        db.refresh(new_sub)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Thanh toán POS và cập nhật hạn thẻ hội viên thành công!",
        "invoice_id": inv.invoice_id,
        "invoice_code": f"INV-{inv.invoice_id:06d}",
        "transaction_code": pay.transaction_code,
        "created_at": inv.created_at,
        "staff_name": current_staff.full_name,
        "member": {
            "member_id": member.member_id,
            "full_name": member.full_name,
            "phone": member.phone,
            "email": member.email,
            "member_code": card.card_code if card else f"DG-{member.member_id:06d}",
        },
        "subscription": {
            "subscription_id": new_sub.subscription_id,
            "subscription_type": sub_type.value,
            "plan_id": plan.plan_id,
            "plan_name": plan.plan_name,
            "duration_days": plan.duration_days,
            "total_sessions": new_sub.total_sessions,
            "sessions_remaining": new_sub.sessions_remaining,
            "start_date": start_dt,
            "end_date": end_dt,
        },
        "billing": {
            "total_amount": total_amount,
            "discount_code": applied_voucher,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "payment_method": pay_method.value,
            "status": inv.status.value,
        },
    }


@router.get(
    "/invoices",
    summary="[Task T067DF1] Danh sách hóa đơn POS (lọc theo ngày, phương thức thanh toán, hội viên)",
)
def list_pos_invoices(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    query = (
        db.query(Invoice, Member, Subscription, MembershipPlan, User)
        .join(Member, Member.member_id == Invoice.member_id)
        .join(Subscription, Subscription.subscription_id == Invoice.subscription_id)
        .join(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
        .outerjoin(User, User.user_id == Invoice.created_by)
    )

    if from_date:
        query = query.filter(
            Invoice.created_at >= datetime.combine(from_date, datetime.min.time())
        )
    if to_date:
        query = query.filter(
            Invoice.created_at <= datetime.combine(to_date, datetime.max.time())
        )
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        member_user = db.query(User.user_id).filter(
            or_(User.full_name.ilike(kw), User.phone.ilike(kw))
        )
        query = query.filter(
            or_(
                Member.user_id.in_(member_user),
                MembershipPlan.plan_name.ilike(kw),
            )
        )

    total = query.count()
    rows = (
        query.order_by(Invoice.created_at.desc(), Invoice.invoice_id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    items = []
    for inv, mem, sub, plan, creator in rows:
        payment = (
            db.query(Payment)
            .filter(Payment.invoice_id == inv.invoice_id)
            .order_by(Payment.payment_id.desc())
            .first()
        )
        items.append(
            {
                "invoice_id": inv.invoice_id,
                "invoice_code": f"INV-{inv.invoice_id:06d}",
                "member_id": mem.member_id,
                "member_name": mem.full_name,
                "member_phone": mem.phone,
                "plan_name": plan.plan_name,
                "subscription_type": sub.subscription_type.value,
                "start_date": sub.start_date,
                "end_date": sub.end_date,
                "total_amount": inv.total_amount,
                "discount_amount": inv.discount_amount,
                "final_amount": inv.final_amount,
                "payment_method": payment.payment_method.value if payment else "CASH",
                "transaction_code": payment.transaction_code if payment else None,
                "status": inv.status.value,
                "staff_name": creator.full_name if creator else "Hệ thống",
                "created_at": inv.created_at,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
    }
