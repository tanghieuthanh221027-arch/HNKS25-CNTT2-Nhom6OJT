import time as perf_time
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_staff_or_admin
from app.models.attendance_record import AttendanceRecord
from app.models.enums import AttendanceStatus, SubscriptionStatus, UserRole
from app.models.member import Member
from app.models.member_card import MemberCard
from app.models.membership_plan import MembershipPlan
from app.models.subscription import Subscription
from app.models.user import User
from app.services.user import compute_badges

router = APIRouter(prefix="/checkins", tags=["QR Check-in & Attendance History"])


class QRCheckInRequest(BaseModel):
    qr_code: str = Field(min_length=2, max_length=100, description="Mã QR trên thẻ hội viên (VD: DG-000001)")


def _recalculate_member_streak(db: Session, member_id: int, card: Optional[MemberCard]) -> tuple[int, int]:
    """Tính chuỗi ngày tập liên tiếp (streak) và tổng số buổi tập từ lịch sử check-in (Bonus T3CD518)."""
    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.member_id == member_id)
        .order_by(AttendanceRecord.check_in.desc())
        .all()
    )
    total_sessions = len(records)
    if not records:
        if card:
            card.streak_days = 0
            card.total_checkins = 0
        return 0, 0

    unique_days = sorted({r.check_in.date() for r in records}, reverse=True)
    streak = 1
    for i in range(len(unique_days) - 1):
        if (unique_days[i] - unique_days[i + 1]).days == 1:
            streak += 1
        else:
            break

    if card:
        card.streak_days = max(card.streak_days, streak)
        card.total_checkins = max(card.total_checkins, total_sessions)
        return card.streak_days, card.total_checkins
    return streak, total_sessions


@router.post(
    "/qr",
    summary="[Task T067E27 - POS Lễ tân] Quét mã QR Check-in / Check-out hội viên (< 1 giây)",
)
def qr_checkin_checkout(
    payload: QRCheckInRequest,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    start_ts = perf_time.perf_counter()
    raw_code = payload.qr_code.strip()
    today = date.today()
    now = datetime.now()

    # 1. Tìm thẻ hội viên theo card_code (hoặc DG-XXXXXX)
    card = db.query(MemberCard).filter(MemberCard.card_code == raw_code).first()
    if not card and raw_code.upper().startswith("DG-"):
        # Hỗ trợ định dạng rút gọn DG-000003 khớp với tiền tố của card_code
        card = (
            db.query(MemberCard)
            .filter(MemberCard.card_code.like(f"{raw_code.upper()}%"))
            .first()
        )

    member: Optional[Member] = None
    if card and card.member_id:
        member = db.query(Member).filter(Member.member_id == card.member_id).first()
    elif card and card.user_id:
        member = db.query(Member).filter(Member.user_id == card.user_id).first()

    if not card or not member:
        elapsed_ms = round((perf_time.perf_counter() - start_ts) * 1000, 2)
        return {
            "valid": False,
            "status": "INVALID_CODE",
            "action": "REJECTED",
            "message": f"Mã QR '{raw_code}' không tồn tại trong hệ thống.",
            "response_time_ms": elapsed_ms,
        }

    # 2. Tự động khoá các gói đã quá hạn của hội viên này (Task T067CF6)
    all_subs = (
        db.query(Subscription, MembershipPlan)
        .join(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
        .filter(Subscription.member_id == member.member_id)
        .order_by(Subscription.end_date.desc())
        .all()
    )
    for s, _p in all_subs:
        if s.status == SubscriptionStatus.ACTIVE and s.end_date < today:
            s.status = SubscriptionStatus.EXPIRED
    db.flush()

    active_subs = [
        (s, p)
        for s, p in all_subs
        if s.status == SubscriptionStatus.ACTIVE and s.end_date >= today
    ]

    if not active_subs:
        db.commit()
        elapsed_ms = round((perf_time.perf_counter() - start_ts) * 1000, 2)
        if all_subs:
            latest_expired, exp_plan = all_subs[0]
            return {
                "valid": False,
                "status": "EXPIRED_CARD",
                "action": "REJECTED",
                "member_id": member.member_id,
                "full_name": member.full_name,
                "member_code": card.card_code,
                "plan_name": exp_plan.plan_name,
                "end_date": latest_expired.end_date,
                "message": f"Thẻ hội viên của {member.full_name} đã hết hạn vào ngày {latest_expired.end_date.strftime('%d/%m/%Y')}. Vui lòng gia hạn tại quầy lễ tân!",
                "response_time_ms": elapsed_ms,
            }
        return {
            "valid": False,
            "status": "NO_SUBSCRIPTION",
            "action": "REJECTED",
            "member_id": member.member_id,
            "full_name": member.full_name,
            "member_code": card.card_code,
            "message": f"Hội viên {member.full_name} chưa đăng ký gói tập nào.",
            "response_time_ms": elapsed_ms,
        }

    active_sub, active_plan = active_subs[0]

    # 3. Kiểm tra xem hội viên đang trong phòng tập (CHECKED_IN hôm nay) hay chưa
    open_record = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.member_id == member.member_id,
            AttendanceRecord.status == AttendanceStatus.CHECKED_IN,
            AttendanceRecord.check_out.is_(None),
        )
        .order_by(AttendanceRecord.check_in.desc())
        .first()
    )

    if open_record:
        # Quét lần 2 -> Ghi nhận CHECK-OUT
        open_record.check_out = now
        open_record.status = AttendanceStatus.CHECKED_OUT
        duration_min = max(1, int((now - open_record.check_in).total_seconds() // 60))
        streak, total_ci = _recalculate_member_streak(db, member.member_id, card)
        db.commit()
        elapsed_ms = round((perf_time.perf_counter() - start_ts) * 1000, 2)
        return {
            "valid": True,
            "status": "VALID_CHECKOUT",
            "action": "CHECK_OUT",
            "attendance_id": open_record.attendance_id,
            "member_id": member.member_id,
            "full_name": member.full_name,
            "phone": member.phone,
            "member_code": card.card_code,
            "plan_name": active_plan.plan_name,
            "end_date": active_sub.end_date,
            "check_in": open_record.check_in,
            "check_out": open_record.check_out,
            "duration_minutes": duration_min,
            "streak_days": streak,
            "total_checkins": total_ci,
            "badges": compute_badges(total_ci, streak),
            "message": f"Check-out thành công! Tạm biệt {member.full_name} (Thời gian tập: {duration_min} phút).",
            "response_time_ms": elapsed_ms,
        }

    # Quét lần 1 -> Ghi nhận CHECK-IN bởi Lễ tân trực quầy POS
    new_record = AttendanceRecord(
        member_id=member.member_id,
        subscription_id=active_sub.subscription_id,
        checked_in_by=current_staff.user_id,
        check_in=now,
        check_out=None,
        status=AttendanceStatus.CHECKED_IN,
    )
    db.add(new_record)
    db.flush()
    streak, total_ci = _recalculate_member_streak(db, member.member_id, card)
    db.commit()
    db.refresh(new_record)

    elapsed_ms = round((perf_time.perf_counter() - start_ts) * 1000, 2)
    return {
        "valid": True,
        "status": "VALID_CHECKIN",
        "action": "CHECK_IN",
        "attendance_id": new_record.attendance_id,
        "member_id": member.member_id,
        "full_name": member.full_name,
        "phone": member.phone,
        "member_code": card.card_code,
        "plan_name": active_plan.plan_name,
        "end_date": active_sub.end_date,
        "days_remaining": (active_sub.end_date - today).days,
        "check_in": new_record.check_in,
        "check_out": None,
        "streak_days": streak,
        "total_checkins": total_ci,
        "badges": compute_badges(total_ci, streak),
        "message": f"Check-in hợp lệ! Chào mừng {member.full_name} ({active_plan.plan_name} · Còn {(active_sub.end_date - today).days} ngày).",
        "response_time_ms": elapsed_ms,
    }


@router.get(
    "/history",
    summary="[Task T067E45] Lịch sử check-in/out phân trang, lọc theo ngày & số người đang tập trong phòng",
)
def get_checkin_history(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    member_id: Optional[int] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    # Đếm số người hiện đang tập trong phòng (CHECKED_IN và chưa check_out hôm nay)
    today_start = datetime.combine(date.today(), datetime.min.time())
    active_in_gym_count = (
        db.query(func.count(AttendanceRecord.attendance_id))
        .filter(
            AttendanceRecord.status == AttendanceStatus.CHECKED_IN,
            AttendanceRecord.check_out.is_(None),
            AttendanceRecord.check_in >= today_start - timedelta(hours=12),
        )
        .scalar()
        or 0
    )

    query = (
        db.query(AttendanceRecord, Member, MemberCard, MembershipPlan)
        .join(Member, Member.member_id == AttendanceRecord.member_id)
        .outerjoin(MemberCard, MemberCard.member_id == Member.member_id)
        .outerjoin(
            Subscription,
            Subscription.subscription_id == AttendanceRecord.subscription_id,
        )
        .outerjoin(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
    )

    # Phân quyền: Hội viên (MEMBER) chỉ xem được lịch sử của chính mình
    if current_user.role == UserRole.MEMBER:
        own_member = db.query(Member).filter(Member.user_id == current_user.user_id).first()
        if not own_member:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0,
                "active_in_gym_count": active_in_gym_count,
            }
        query = query.filter(AttendanceRecord.member_id == own_member.member_id)
    else:
        if member_id is not None:
            query = query.filter(AttendanceRecord.member_id == member_id)
        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    Member.full_name.ilike(kw),
                    Member.phone.ilike(kw),
                    MemberCard.card_code.ilike(kw),
                )
            )

    if from_date:
        query = query.filter(
            AttendanceRecord.check_in >= datetime.combine(from_date, datetime.min.time())
        )
    if to_date:
        query = query.filter(
            AttendanceRecord.check_in <= datetime.combine(to_date, datetime.max.time())
        )

    total = query.count()
    rows = (
        query.order_by(AttendanceRecord.check_in.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    items = []
    for rec, mem, card, plan in rows:
        dur = None
        if rec.check_out:
            dur = max(1, int((rec.check_out - rec.check_in).total_seconds() // 60))
        items.append(
            {
                "attendance_id": rec.attendance_id,
                "member_id": mem.member_id,
                "full_name": mem.full_name,
                "phone": mem.phone,
                "member_code": card.card_code if card else f"DG-{mem.member_id:06d}",
                "plan_name": plan.plan_name if plan else "Gói Hội Viên",
                "check_in": rec.check_in,
                "check_out": rec.check_out,
                "status": rec.status.value,
                "duration_minutes": dur,
            }
        )

    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "active_in_gym_count": active_in_gym_count,
    }
