from datetime import date, time, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exception import (
    BusinessRuleException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.enums import BookingStatus, ScheduleStatus, UserRole, UserStatus
from app.models.member import Member
from app.models.trainer_schedule import TrainerSchedule
from app.models.training_booking import TrainingBooking
from app.models.user import User
from app.services.auth_service import ensure_member_and_card

router = APIRouter(prefix="/pt-schedules", tags=["PT 1-1 Scheduling"])


class PTBookingCreate(BaseModel):
    trainer_id: int = Field(gt=0)
    booking_date: date
    start_time: time
    end_time: Optional[time] = None


class PTBookingStatusUpdate(BaseModel):
    status: str = Field(description="CONFIRMED, CANCELLED, COMPLETED")


def _serialize_booking(
    bk: TrainingBooking,
    trainer: Optional[User],
    member: Optional[Member],
) -> dict[str, Any]:
    return {
        "booking_id": bk.booking_id,
        "schedule_id": bk.schedule_id,
        "trainer_id": bk.trainer_id,
        "trainer_name": trainer.full_name if trainer else f"PT #{bk.trainer_id}",
        "trainer_specialization": trainer.specialization if trainer else None,
        "member_id": bk.member_id,
        "member_name": member.full_name if member else f"Hội viên #{bk.member_id}",
        "member_phone": member.phone if member else None,
        "booking_date": bk.booking_date,
        "start_time": bk.start_time.strftime("%H:%M"),
        "end_time": bk.end_time.strftime("%H:%M"),
        "status": bk.status.value,
        "created_at": bk.created_at,
    }


@router.get(
    "",
    summary="[Task T067DB0] Xem lịch đặt PT 1-1 theo PT và theo tuần",
)
def list_pt_schedules(
    trainer_id: Optional[int] = Query(default=None),
    week_start: Optional[date] = Query(default=None, description="Ngày đầu tuần (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    today = date.today()
    monday = week_start or (today - timedelta(days=today.weekday()))
    sunday = monday + timedelta(days=6)

    trainers = (
        db.query(User)
        .filter(User.role == UserRole.TRAINER, User.status == UserStatus.ACTIVE)
        .order_by(User.user_id.asc())
        .all()
    )

    query = (
        db.query(TrainingBooking, User, Member)
        .join(User, User.user_id == TrainingBooking.trainer_id)
        .join(Member, Member.member_id == TrainingBooking.member_id)
        .filter(
            TrainingBooking.booking_date >= monday,
            TrainingBooking.booking_date <= sunday,
        )
    )

    if trainer_id is not None:
        query = query.filter(TrainingBooking.trainer_id == trainer_id)
    elif current_user.role == UserRole.TRAINER:
        query = query.filter(TrainingBooking.trainer_id == current_user.user_id)

    rows = query.order_by(
        TrainingBooking.booking_date.asc(),
        TrainingBooking.start_time.asc(),
    ).all()

    own_member = None
    if current_user.role == UserRole.MEMBER:
        own_member, _ = ensure_member_and_card(db, current_user)

    bookings = []
    for bk, tr, mem in rows:
        item = _serialize_booking(bk, tr, mem)
        item["is_mine"] = bool(
            (own_member and bk.member_id == own_member.member_id)
            or (current_user.role == UserRole.TRAINER and bk.trainer_id == current_user.user_id)
        )
        bookings.append(item)

    return {
        "week_start": monday,
        "week_end": sunday,
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
        "standard_hours": ["07:00", "08:00", "09:00", "10:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"],
        "bookings": bookings,
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="[Task T067DB0] Hội viên đặt ca tập PT 1-1 (chặn trùng khung giờ của cả PT và hội viên)",
)
def create_pt_booking(
    payload: PTBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    trainer = (
        db.query(User)
        .filter(
            User.user_id == payload.trainer_id,
            User.role == UserRole.TRAINER,
            User.status == UserStatus.ACTIVE,
        )
        .first()
    )
    if not trainer:
        raise NotFoundException("Huấn luyện viên (PT) không tồn tại hoặc đang tạm ngưng hoạt động.")

    member, _ = ensure_member_and_card(db, current_user)
    if not member:
        raise BusinessRuleException("Chỉ tài khoản Hội viên mới có thể đặt lịch tập PT 1-1.")

    start_t = payload.start_time
    if payload.end_time:
        end_t = payload.end_time
    else:
        next_hour = min(23, start_t.hour + 1)
        end_t = time(next_hour, start_t.minute)

    if end_t <= start_t:
        raise BusinessRuleException("Giờ kết thúc ca tập phải lớn hơn giờ bắt đầu.")

    # 1. Kiểm tra trùng khung giờ của PT (BR12 - Task T067DB0)
    pt_overlap = (
        db.query(TrainingBooking)
        .filter(
            TrainingBooking.trainer_id == trainer.user_id,
            TrainingBooking.booking_date == payload.booking_date,
            TrainingBooking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            TrainingBooking.start_time < end_t,
            TrainingBooking.end_time > start_t,
        )
        .first()
    )
    if pt_overlap:
        raise ConflictException(
            f"Trùng lịch PT: HLV {trainer.full_name} đã có lịch đặt trong khung giờ "
            f"{pt_overlap.start_time.strftime('%H:%M')} - {pt_overlap.end_time.strftime('%H:%M')} "
            f"ngày {payload.booking_date.strftime('%d/%m/%Y')}."
        )

    # 2. Kiểm tra trùng khung giờ của chính Hội viên (Task T067DB0)
    member_overlap = (
        db.query(TrainingBooking)
        .filter(
            TrainingBooking.member_id == member.member_id,
            TrainingBooking.booking_date == payload.booking_date,
            TrainingBooking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            TrainingBooking.start_time < end_t,
            TrainingBooking.end_time > start_t,
        )
        .first()
    )
    if member_overlap:
        raise ConflictException(
            f"Trùng lịch cá nhân: Bạn đã có một ca tập PT khác trong khung giờ "
            f"{member_overlap.start_time.strftime('%H:%M')} - {member_overlap.end_time.strftime('%H:%M')} "
            f"ngày {payload.booking_date.strftime('%d/%m/%Y')}."
        )

    # 3. Đảm bảo có slot TrainerSchedule tương ứng
    schedule = (
        db.query(TrainerSchedule)
        .filter(
            TrainerSchedule.trainer_id == trainer.user_id,
            TrainerSchedule.work_date == payload.booking_date,
            TrainerSchedule.start_time == start_t,
        )
        .first()
    )
    if not schedule:
        schedule = TrainerSchedule(
            trainer_id=trainer.user_id,
            work_date=payload.booking_date,
            start_time=start_t,
            end_time=end_t,
            status=ScheduleStatus.ACTIVE,
        )
        db.add(schedule)
        db.flush()

    booking = TrainingBooking(
        member_id=member.member_id,
        trainer_id=trainer.user_id,
        schedule_id=schedule.schedule_id,
        booking_date=payload.booking_date,
        start_time=start_t,
        end_time=end_t,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    result = _serialize_booking(booking, trainer, member)
    result["message"] = (
        f"Đặt lịch tập 1-1 cùng HLV {trainer.full_name} lúc {start_t.strftime('%H:%M')} "
        f"ngày {payload.booking_date.strftime('%d/%m/%Y')} thành công!"
    )
    return result


@router.put(
    "/{booking_id}/status",
    summary="[Task T067DB0] PT xác nhận / huỷ / đánh dấu hoàn thành ca tập (hoặc Hội viên huỷ lịch)",
)
def update_pt_booking_status(
    booking_id: int,
    payload: PTBookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    booking = (
        db.query(TrainingBooking)
        .filter(TrainingBooking.booking_id == booking_id)
        .first()
    )
    if not booking:
        raise NotFoundException(f"Không tìm thấy lịch đặt PT #{booking_id}.")

    target_str = payload.status.strip().upper()
    if target_str not in ("CONFIRMED", "CANCELLED", "COMPLETED"):
        raise BusinessRuleException("Trạng thái chỉ nhận CONFIRMED, CANCELLED hoặc COMPLETED.")
    target_status = BookingStatus(target_str)

    # Kiểm tra quyền
    if current_user.role == UserRole.MEMBER:
        own_member = db.query(Member).filter(Member.user_id == current_user.user_id).first()
        if not own_member or booking.member_id != own_member.member_id:
            raise ForbiddenException("Bạn chỉ được thao tác trên lịch tập của chính mình.")
        if target_status != BookingStatus.CANCELLED:
            raise ForbiddenException("Hội viên chỉ có quyền Hủy (CANCELLED) lịch đặt.")
    elif current_user.role == UserRole.TRAINER:
        if booking.trainer_id != current_user.user_id:
            raise ForbiddenException("Bạn chỉ có thể xác nhận/huỷ lịch tập của chính mình.")

    booking.status = target_status
    db.commit()
    db.refresh(booking)

    trainer = db.query(User).filter(User.user_id == booking.trainer_id).first()
    member = db.query(Member).filter(Member.member_id == booking.member_id).first()
    res = _serialize_booking(booking, trainer, member)
    res["message"] = f"Đã cập nhật trạng thái lịch tập #{booking_id} sang {target_status.value}."
    return res
