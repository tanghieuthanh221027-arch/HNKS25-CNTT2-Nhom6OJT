"""
Tầng Dịch vụ Nghiệp vụ Quản lý Lịch tập PT 1-1 (pt_schedule_service.py)
Đã khắc phục toàn bộ các điểm đánh dấu đỏ trong Báo cáo Kỹ thuật:
- Mục 1.4 & 5.6: Cấm xoá vật lý (DELETE) ca tập với mọi vai trò; bổ sung PATCH /confirm, /cancel, /complete, /no-show.
- Mục 3.2.4 & 3.2.6: Quản lý total_sessions / sessions_remaining trên Subscription, gắn subscription_id vào TrainingBooking, trừ 1 buổi khi COMPLETED hoặc NO_SHOW.
- Mục 4.4 (BR15, BR16, BR17):
  + BR15: Kiểm tra ghép ngày + giờ (start_at > now_vn() + 30 phút), chặn đặt giờ đã qua trong ngày (HTTP 400).
  + BR16: Bắt buộc hội viên có gói PT còn hạn và sessions_remaining khả dụng > 0, nếu hết buổi trả HTTP 403.
  + BR17: Hội viên chỉ được tự huỷ ca miễn phí trước giờ bắt đầu tối thiểu 2 tiếng (sát giờ trả HTTP 400).
- Mục 4.5: Bổ sung nhánh PENDING -> EXPIRED (tự động hết hạn sau 2 giờ nếu PT không duyệt) và CONFIRMED -> NO_SHOW.
- Mục 5.2: Chống Race Condition bằng khoá bi quan SELECT ... FOR UPDATE (with_for_update) và hỗ trợ ca qua đêm (start_at / end_at DATETIME).
- Mục 5.3: Không tự ý tạo TrainerSchedule khi học viên đặt lịch; bắt buộc nằm trong ca trực ACTIVE đã mở trước của PT.
- Mục 5.5: Xử lý tuần chuẩn ISO 8601 có bắt lỗi ValueError (week=53 -> HTTP 400) và chuẩn múi giờ Asia/Ho_Chi_Minh.
- Mục 8.2: Eager Loading (joinedload) gộp 1 câu SQL chống N+1 Queries.
"""

from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exception import (
    BadRequestException,
    BusinessRuleException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.timezone_utils import now_vn, resolve_iso_week_range, today_vn
from app.models.enums import (
    BookingStatus,
    ScheduleStatus,
    SubscriptionStatus,
    UserRole,
    UserStatus,
)
from app.models.member import Member
from app.models.subscription import Subscription
from app.models.trainer_schedule import TrainerSchedule
from app.models.training_booking import TrainingBooking
from app.models.user import User
from app.services.auth_service import ensure_member_and_card

PENDING_EXPIRY_HOURS = 2
MIN_ADVANCE_BOOKING_MINUTES = 30
MIN_FREE_CANCEL_HOURS = 2


def serialize_booking(bk: TrainingBooking, current_user: Optional[User] = None, own_member_id: Optional[int] = None) -> dict[str, Any]:
    trainer = bk.trainer
    member = bk.member
    sub = bk.subscription
    is_mine = False
    if current_user:
        if own_member_id and bk.member_id == own_member_id:
            is_mine = True
        elif current_user.role == UserRole.TRAINER and bk.trainer_id == current_user.user_id:
            is_mine = True

    return {
        "booking_id": bk.booking_id,
        "schedule_id": bk.schedule_id,
        "subscription_id": bk.subscription_id,
        "trainer_id": bk.trainer_id,
        "trainer_name": trainer.full_name if trainer else f"PT #{bk.trainer_id}",
        "trainer_specialization": trainer.specialization if trainer else None,
        "member_id": bk.member_id,
        "member_name": member.full_name if member else f"Hội viên #{bk.member_id}",
        "member_phone": member.phone if member else None,
        "booking_date": bk.booking_date,
        "start_time": bk.start_time.strftime("%H:%M"),
        "end_time": bk.end_time.strftime("%H:%M"),
        "start_at": bk.start_at,
        "end_at": bk.end_at,
        "status": bk.status.value,
        "cancel_reason": bk.cancel_reason,
        "sessions_remaining": sub.sessions_remaining if sub else None,
        "created_at": bk.created_at,
        "is_mine": is_mine,
    }


def auto_expire_stale_pending_bookings(db: Session) -> int:
    """
    Mục 4.5: Tự động chuyển các ca PENDING quá 2 giờ chưa được PT duyệt (hoặc đã tới giờ bắt đầu)
    sang trạng thái EXPIRED để giải phóng khung giờ.
    """
    now = now_vn()
    cutoff_created = now - timedelta(hours=PENDING_EXPIRY_HOURS)
    stale_rows = (
        db.query(TrainingBooking)
        .filter(
            TrainingBooking.status == BookingStatus.PENDING,
            (TrainingBooking.created_at <= cutoff_created) | (TrainingBooking.start_at <= now),
        )
        .all()
    )
    if not stale_rows:
        return 0

    for bk in stale_rows:
        bk.status = BookingStatus.EXPIRED
        if not bk.cancel_reason:
            bk.cancel_reason = "Tự động hết hạn (EXPIRED) do quá 2 giờ PT chưa xác nhận"
    db.commit()
    return len(stale_rows)


def compute_slot_datetimes(
    work_date: date,
    start_time: time,
    end_time: Optional[time] = None,
    overnight: bool = False,
) -> tuple[time, datetime, datetime]:
    """
    Mục 5.2: Tính toán start_at & end_at kiểu DATETIME hỗ trợ cả ca ngày lẫn ca xuyên đêm (VD: 23:00 -> 01:00).
    """
    clean_start = start_time.replace(second=0, microsecond=0)
    start_at = datetime.combine(work_date, clean_start)

    if end_time is None:
        end_at = start_at + timedelta(hours=1)
        clean_end = end_at.time()
        return clean_end, start_at, end_at

    clean_end = end_time.replace(second=0, microsecond=0)
    is_auto_overnight = overnight or (clean_start >= time(22, 0) and clean_end <= time(6, 0))
    if is_auto_overnight and clean_end <= clean_start:
        end_at = datetime.combine(work_date + timedelta(days=1), clean_end)
    else:
        if clean_end <= clean_start:
            raise BusinessRuleException("Giờ kết thúc ca tập phải lớn hơn giờ bắt đầu.")
        end_at = datetime.combine(work_date, clean_end)

    return clean_end, start_at, end_at


def create_trainer_work_slot(
    db: Session,
    current_user: User,
    trainer_id: int,
    work_date: date,
    start_time: time,
    end_time: time,
    overnight: bool = False,
) -> TrainerSchedule:
    """Đăng ký ca trực mở của PT (TrainerSchedule) trước khi học viên đặt lịch (Mục 5.3)."""
    if current_user.role == UserRole.TRAINER and current_user.user_id != trainer_id:
        raise ForbiddenException("Huấn luyện viên chỉ được mở ca trực cho chính mình.")
    if current_user.role not in (UserRole.ADMIN, UserRole.STAFF, UserRole.TRAINER):
        raise ForbiddenException("Bạn không có quyền mở ca trực huấn luyện viên.")

    trainer = (
        db.query(User)
        .filter(
            User.user_id == trainer_id,
            User.role == UserRole.TRAINER,
            User.status == UserStatus.ACTIVE,
        )
        .first()
    )
    if not trainer:
        raise NotFoundException("Huấn luyện viên (PT) không tồn tại hoặc đang ngừng hoạt động.")

    clean_end, start_at, end_at = compute_slot_datetimes(
        work_date, start_time, end_time, overnight=overnight
    )
    clean_start = start_time.replace(second=0, microsecond=0)

    existing = (
        db.query(TrainerSchedule)
        .filter(
            TrainerSchedule.trainer_id == trainer_id,
            TrainerSchedule.work_date == work_date,
            TrainerSchedule.start_time == clean_start,
        )
        .first()
    )
    if existing:
        existing.end_time = clean_end
        existing.start_at = start_at
        existing.end_at = end_at
        existing.status = ScheduleStatus.ACTIVE
        db.commit()
        db.refresh(existing)
        return existing

    slot = TrainerSchedule(
        trainer_id=trainer_id,
        work_date=work_date,
        start_time=clean_start,
        end_time=clean_end,
        start_at=start_at,
        end_at=end_at,
        status=ScheduleStatus.ACTIVE,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


def get_pt_schedules(
    db: Session,
    current_user: User,
    trainer_id: Optional[int] = None,
    week: Optional[int] = None,
    year: Optional[int] = None,
    week_start: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[BookingStatus] = None,
) -> dict[str, Any]:
    """
    Mục 5.5 & 8.2: Lọc lịch tập theo PT, theo tuần ISO 8601 (bắt lỗi week=53 -> 400) hoặc khoảng ngày,
    kết hợp Eager Loading (joinedload) gộp 1 câu SQL duy nhất chống N+1 Queries.
    """
    auto_expire_stale_pending_bookings(db)
    today = today_vn()

    if start_date and end_date:
        if end_date < start_date:
            raise BadRequestException("end_date phải lớn hơn hoặc bằng start_date.")
        range_start, range_end = start_date, end_date
    elif week is not None:
        range_start, range_end = resolve_iso_week_range(week=week, year=year)
    elif week_start is not None:
        range_start = week_start
        range_end = week_start + timedelta(days=6)
    else:
        range_start = today - timedelta(days=today.weekday())
        range_end = range_start + timedelta(days=6)

    trainers = (
        db.query(User)
        .filter(User.role == UserRole.TRAINER, User.status == UserStatus.ACTIVE)
        .order_by(User.user_id.asc())
        .all()
    )

    stmt = (
        select(TrainingBooking)
        .options(
            joinedload(TrainingBooking.trainer),
            joinedload(TrainingBooking.member).joinedload(Member.user),
            joinedload(TrainingBooking.subscription),
        )
        .where(
            TrainingBooking.booking_date >= range_start,
            TrainingBooking.booking_date <= range_end,
        )
    )

    if trainer_id is not None:
        stmt = stmt.where(TrainingBooking.trainer_id == trainer_id)
    elif current_user.role == UserRole.TRAINER:
        stmt = stmt.where(TrainingBooking.trainer_id == current_user.user_id)

    if status_filter is not None:
        stmt = stmt.where(TrainingBooking.status == status_filter)

    stmt = stmt.order_by(TrainingBooking.start_at.asc())
    booking_objs = list(db.scalars(stmt).unique().all())

    own_member_id: Optional[int] = None
    pt_quota_info: Optional[dict[str, int]] = None
    if current_user.role == UserRole.MEMBER:
        own_member, _ = ensure_member_and_card(db, current_user)
        if own_member:
            own_member_id = own_member.member_id
            active_subs = (
                db.query(Subscription)
                .filter(
                    Subscription.member_id == own_member.member_id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.end_date >= today,
                )
                .all()
            )
            total_s = sum((s.total_sessions for s in active_subs), 0)
            rem_s = sum((s.sessions_remaining for s in active_subs), 0)
            pt_quota_info = {
                "total_sessions": total_s,
                "sessions_remaining": rem_s,
            }

    work_slots_q = db.query(TrainerSchedule).filter(
        TrainerSchedule.work_date >= range_start,
        TrainerSchedule.work_date <= range_end,
        TrainerSchedule.status == ScheduleStatus.ACTIVE,
    )
    if trainer_id is not None:
        work_slots_q = work_slots_q.filter(TrainerSchedule.trainer_id == trainer_id)
    open_slots = [
        {
            "schedule_id": s.schedule_id,
            "trainer_id": s.trainer_id,
            "work_date": s.work_date,
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
        }
        for s in work_slots_q.order_by(TrainerSchedule.work_date.asc(), TrainerSchedule.start_time.asc()).all()
    ]

    return {
        "week_start": range_start,
        "week_end": range_end,
        "pt_quota": pt_quota_info,
        "trainers": [
            {
                "user_id": t.user_id,
                "full_name": t.full_name,
                "specialization": t.specialization,
                "experience_years": t.experience_years,
                "bio": t.bio,
            }
            for t in trainers
        ],
        "standard_hours": [
            "07:00",
            "08:00",
            "09:00",
            "10:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
            "19:00",
            "20:00",
        ],
        "open_work_slots": open_slots,
        "bookings": [serialize_booking(bk, current_user, own_member_id) for bk in booking_objs],
    }


def create_pt_booking(
    db: Session,
    current_user: User,
    trainer_id: int,
    booking_date: date,
    start_time: time,
    end_time: Optional[time] = None,
    schedule_id: Optional[int] = None,
    member_id: Optional[int] = None,
    overnight: bool = False,
) -> dict[str, Any]:
    auto_expire_stale_pending_bookings(db)

    # Phân quyền đặt lịch (Mục 1.4): MEMBER tự đặt, hoặc STAFF/ADMIN đặt hộ có truyền member_id
    target_member: Optional[Member] = None
    if current_user.role == UserRole.MEMBER:
        target_member, _ = ensure_member_and_card(db, current_user)
    elif current_user.role in (UserRole.ADMIN, UserRole.STAFF):
        if not member_id:
            raise BusinessRuleException("Chỉ tài khoản Hội viên mới tự đặt lịch PT 1-1 (hoặc Lễ tân/Admin cần truyền member_id).")
        target_member = db.query(Member).filter(Member.member_id == member_id).first()
        if not target_member:
            raise NotFoundException(f"Không tìm thấy hội viên #{member_id}.")
    else:
        raise ForbiddenException("Vai trò của bạn không có quyền đặt ca tập PT 1-1.")

    if not target_member:
        raise BusinessRuleException("Không xác định được hồ sơ Hội viên.")

    clean_start = start_time.replace(second=0, microsecond=0)
    clean_end, req_start_at, req_end_at = compute_slot_datetimes(
        booking_date, clean_start, end_time, overnight=overnight
    )

    # BR15 (Mục 4.4 - TC_PAST_01): Ghép cả ngày + giờ theo múi giờ Việt Nam, phải cách hiện tại > 30 phút
    now = now_vn()
    if req_start_at <= now + timedelta(minutes=MIN_ADVANCE_BOOKING_MINUTES):
        raise BadRequestException(
            "BR15: Thời điểm bắt đầu ca tập phải sau thời gian hiện tại tối thiểu 30 phút (không được đặt lịch vào giờ đã qua)."
        )

    # Mục 5.2: Khoá bi quan (SELECT ... FOR UPDATE) trên dòng User của PT để tuần tự hoá mọi request đặt cùng PT
    trainer = db.execute(
        select(User)
        .where(
            User.user_id == trainer_id,
            User.role == UserRole.TRAINER,
            User.status == UserStatus.ACTIVE,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if not trainer:
        raise NotFoundException("Huấn luyện viên (PT) không tồn tại hoặc đang tạm ngưng hoạt động (BR12).")

    # BR16 (Mục 4.4 - TC_QUOTA_01): Bắt buộc có hợp đồng gói tập còn hạn & sessions_remaining khả dụng > 0
    # Hỗ trợ chuỗi gói gia hạn nối tiếp (RENEW): mọi gói ACTIVE có end_date >= today đều đóng góp quỹ buổi PT
    today = today_vn()
    candidate_subs = list(
        db.scalars(
            select(Subscription)
            .where(
                Subscription.member_id == target_member.member_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date >= today,
                Subscription.sessions_remaining > 0,
            )
            .order_by(Subscription.start_date.asc(), Subscription.end_date.asc())
            .with_for_update()
        ).all()
    )

    chosen_sub: Optional[Subscription] = None
    for sub in candidate_subs:
        held_bookings = (
            db.query(func.count(TrainingBooking.booking_id))
            .filter(
                TrainingBooking.subscription_id == sub.subscription_id,
                TrainingBooking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            )
            .scalar()
            or 0
        )
        if sub.sessions_remaining - held_bookings > 0:
            chosen_sub = sub
            break

    if not chosen_sub:
        raise ForbiddenException(
            "BR16: Hội viên không có gói tập PT còn hạn hoặc đã sử dụng hết số buổi tập PT (sessions_remaining = 0)."
        )

    # Mục 5.3: Bắt buộc khung giờ đặt phải nằm trong ca trực mở (TrainerSchedule ACTIVE) của PT — KHÔNG tự ý tạo mới!
    sched_query = db.query(TrainerSchedule).filter(
        TrainerSchedule.trainer_id == trainer.user_id,
        TrainerSchedule.status == ScheduleStatus.ACTIVE,
    )
    if schedule_id is not None:
        sched_query = sched_query.filter(TrainerSchedule.schedule_id == schedule_id)

    candidate_schedules = sched_query.filter(
        TrainerSchedule.work_date.in_([booking_date, booking_date - timedelta(days=1)])
    ).with_for_update().all()

    matched_schedule: Optional[TrainerSchedule] = None
    for s in candidate_schedules:
        s_start = s.start_at or datetime.combine(s.work_date, s.start_time)
        s_end = s.end_at or (
            datetime.combine(s.work_date, s.end_time)
            if s.end_time > s.start_time
            else datetime.combine(s.work_date + timedelta(days=1), s.end_time)
        )
        if s_start <= req_start_at and s_end >= req_end_at:
            matched_schedule = s
            break

    if not matched_schedule:
        raise BadRequestException(
            "Huấn luyện viên chưa mở ca trực làm việc (TrainerSchedule) bao phủ khung giờ này. Vui lòng chọn khung giờ thuộc ca trực của PT."
        )

    # BR13 (Mục 5.2): Kiểm tra trùng khung giờ của PT trên trục DATETIME [start_at, end_at) với khoá FOR UPDATE
    pt_overlap = db.execute(
        select(TrainingBooking)
        .where(
            TrainingBooking.trainer_id == trainer.user_id,
            TrainingBooking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            TrainingBooking.start_at < req_end_at,
            TrainingBooking.end_at > req_start_at,
        )
        .with_for_update()
    ).scalars().first()
    if pt_overlap:
        raise ConflictException(
            f"Trùng lịch PT (BR13): HLV {trainer.full_name} đã có ca tập trong khung giờ "
            f"{pt_overlap.start_time.strftime('%H:%M')} - {pt_overlap.end_time.strftime('%H:%M')} "
            f"ngày {pt_overlap.booking_date.strftime('%d/%m/%Y')}."
        )

    # BR14 (Mục 5.2): Kiểm tra trùng khung giờ cá nhân của Hội viên
    member_overlap = db.execute(
        select(TrainingBooking)
        .where(
            TrainingBooking.member_id == target_member.member_id,
            TrainingBooking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            TrainingBooking.start_at < req_end_at,
            TrainingBooking.end_at > req_start_at,
        )
        .with_for_update()
    ).scalars().first()
    if member_overlap:
        raise ConflictException(
            f"Trùng lịch cá nhân (BR14): Bạn đã có một ca tập PT khác trong khung giờ "
            f"{member_overlap.start_time.strftime('%H:%M')} - {member_overlap.end_time.strftime('%H:%M')} "
            f"ngày {member_overlap.booking_date.strftime('%d/%m/%Y')}."
        )

    booking = TrainingBooking(
        member_id=target_member.member_id,
        trainer_id=trainer.user_id,
        subscription_id=chosen_sub.subscription_id,
        schedule_id=matched_schedule.schedule_id,
        booking_date=booking_date,
        start_time=clean_start,
        end_time=clean_end,
        start_at=req_start_at,
        end_at=req_end_at,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()

    # Eager reload để đóng gói response không phát sinh N+1
    loaded = db.scalars(
        select(TrainingBooking)
        .options(
            joinedload(TrainingBooking.trainer),
            joinedload(TrainingBooking.member).joinedload(Member.user),
            joinedload(TrainingBooking.subscription),
        )
        .where(TrainingBooking.booking_id == booking.booking_id)
    ).first()
    res = serialize_booking(loaded or booking, current_user, target_member.member_id)
    res["message"] = (
        f"Đặt lịch tập 1-1 cùng HLV {trainer.full_name} lúc {clean_start.strftime('%H:%M')} "
        f"ngày {booking_date.strftime('%d/%m/%Y')} thành công!"
    )
    return res


def transition_booking_status(
    db: Session,
    booking_id: int,
    target_status: BookingStatus,
    current_user: User,
    reason: Optional[str] = None,
) -> dict[str, Any]:
    """
    Mục 4.5, 5.4 & 5.6: Điều chuyển máy trạng thái ca tập nghiêm ngặt:
    - PENDING -> CONFIRMED | CANCELLED | EXPIRED
    - CONFIRMED -> COMPLETED | CANCELLED | NO_SHOW
    - Trừ 1 buổi sessions_remaining khi COMPLETED hoặc NO_SHOW.
    - Kiểm tra BR17: Hội viên chỉ được tự huỷ trước giờ bắt đầu >= 2 tiếng.
    """
    auto_expire_stale_pending_bookings(db)

    booking = db.scalars(
        select(TrainingBooking)
        .options(
            joinedload(TrainingBooking.trainer),
            joinedload(TrainingBooking.member).joinedload(Member.user),
            joinedload(TrainingBooking.subscription),
        )
        .where(TrainingBooking.booking_id == booking_id)
        .with_for_update()
    ).first()
    if not booking:
        raise NotFoundException(f"Không tìm thấy lịch đặt PT #{booking_id}.")

    # Kiểm tra phân quyền theo vai trò (Mục 1.4)
    own_member_id: Optional[int] = None
    if current_user.role == UserRole.MEMBER:
        own_member = db.query(Member).filter(Member.user_id == current_user.user_id).first()
        own_member_id = own_member.member_id if own_member else None
        if not own_member or booking.member_id != own_member.member_id:
            raise ForbiddenException("Bạn chỉ được thao tác trên lịch tập của chính mình.")
        if target_status != BookingStatus.CANCELLED:
            raise ForbiddenException("Hội viên chỉ có quyền Hủy (CANCELLED) lịch đặt.")
        # BR17 (Mục 4.4 - TC_CANCEL_LATE): Hội viên không được huỷ sát giờ (< 2 tiếng)
        if booking.start_at - now_vn() < timedelta(hours=MIN_FREE_CANCEL_HOURS):
            raise BadRequestException(
                f"BR17: Hội viên chỉ được hủy ca miễn phí trước giờ bắt đầu tối thiểu {MIN_FREE_CANCEL_HOURS} tiếng."
            )
    elif current_user.role == UserRole.TRAINER:
        if booking.trainer_id != current_user.user_id:
            raise ForbiddenException("Bạn chỉ có thể thao tác trên lịch dạy của chính mình.")
    elif current_user.role not in (UserRole.ADMIN, UserRole.STAFF):
        raise ForbiddenException("Vai trò của bạn không có quyền cập nhật trạng thái ca tập.")

    if not booking.can_transition_to(target_status):
        raise BadRequestException(
            f"Chuyển đổi trạng thái không hợp lệ: Không thể chuyển ca tập #{booking_id} từ '{booking.status.value}' sang '{target_status.value}'."
        )

    booking.status = target_status
    if reason and reason.strip():
        booking.cancel_reason = reason.strip()

    # Mục 3.2.4 & 4.5: Khi hoàn thành (COMPLETED) hoặc học viên bỏ ca (NO_SHOW), trừ 1 buổi PT
    if target_status in (BookingStatus.COMPLETED, BookingStatus.NO_SHOW):
        sub = (
            db.query(Subscription)
            .filter(Subscription.subscription_id == booking.subscription_id)
            .with_for_update()
            .first()
        )
        if sub and sub.sessions_remaining > 0:
            sub.sessions_remaining -= 1

    db.commit()
    db.refresh(booking)

    res = serialize_booking(booking, current_user, own_member_id)
    res["message"] = f"Đã cập nhật trạng thái lịch tập #{booking_id} sang {target_status.value}."
    return res
