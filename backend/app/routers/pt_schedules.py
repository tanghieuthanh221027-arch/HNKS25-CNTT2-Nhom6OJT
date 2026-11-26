from datetime import date, time
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exception import BadRequestException, ForbiddenException
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.enums import BookingStatus
from app.models.user import User
from app.services import pt_schedule_service

router = APIRouter(prefix="/pt-schedules", tags=["PT 1-1 Scheduling"])


class PTBookingCreate(BaseModel):
    trainer_id: int = Field(gt=0)
    booking_date: date
    start_time: time
    end_time: Optional[time] = None
    schedule_id: Optional[int] = None
    member_id: Optional[int] = None
    overnight: bool = False


class PTWorkSlotCreate(BaseModel):
    trainer_id: int = Field(gt=0)
    work_date: date
    start_time: time
    end_time: time
    overnight: bool = False


class PTBookingStatusUpdate(BaseModel):
    status: str = Field(description="CONFIRMED, CANCELLED, COMPLETED, NO_SHOW")
    reason: Optional[str] = None


class PTCancelRequest(BaseModel):
    reason: Optional[str] = None


@router.get(
    "",
    summary="[Mục 5.5 & 5.6] Xem lịch đặt PT 1-1 theo PT, tuần ISO 8601 (week/year) hoặc khoảng ngày",
)
def list_pt_schedules(
    trainer_id: Optional[int] = Query(default=None),
    week: Optional[int] = Query(default=None, description="Số tuần chuẩn ISO 8601 (1-53)"),
    year: Optional[int] = Query(default=None, description="Năm lọc tuần ISO"),
    week_start: Optional[date] = Query(default=None, description="Ngày đầu tuần (YYYY-MM-DD)"),
    start_date: Optional[date] = Query(default=None, description="Từ ngày (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Đến ngày (YYYY-MM-DD)"),
    status_filter: Optional[BookingStatus] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return pt_schedule_service.get_pt_schedules(
        db=db,
        current_user=current_user,
        trainer_id=trainer_id,
        week=week,
        year=year,
        week_start=week_start,
        start_date=start_date,
        end_date=end_date,
        status_filter=status_filter,
    )


@router.post(
    "/work-slots",
    status_code=status.HTTP_201_CREATED,
    summary="[Mục 5.3] PT / Admin đăng ký mở ca trực làm việc (hỗ trợ cả ca qua đêm)",
)
def create_pt_work_slot(
    payload: PTWorkSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    slot = pt_schedule_service.create_trainer_work_slot(
        db=db,
        current_user=current_user,
        trainer_id=payload.trainer_id,
        work_date=payload.work_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        overnight=payload.overnight,
    )
    return {
        "schedule_id": slot.schedule_id,
        "trainer_id": slot.trainer_id,
        "work_date": slot.work_date,
        "start_time": slot.start_time.strftime("%H:%M"),
        "end_time": slot.end_time.strftime("%H:%M"),
        "start_at": slot.start_at,
        "end_at": slot.end_at,
        "status": slot.status.value,
        "message": "Đã đăng ký mở ca trực PT thành công.",
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="[BR12-BR16 & Mục 5.2-5.3] Đặt ca tập PT 1-1 (khoá bi quan chống Race Condition, kiểm tra gói PT & ca trực)",
)
def create_pt_booking(
    payload: PTBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return pt_schedule_service.create_pt_booking(
        db=db,
        current_user=current_user,
        trainer_id=payload.trainer_id,
        booking_date=payload.booking_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        schedule_id=payload.schedule_id,
        member_id=payload.member_id,
        overnight=payload.overnight,
    )


@router.patch(
    "/{booking_id}/confirm",
    summary="[Mục 5.6] PT / Staff / Admin xác nhận ca tập (PENDING -> CONFIRMED)",
)
def confirm_pt_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return pt_schedule_service.transition_booking_status(
        db=db,
        booking_id=booking_id,
        target_status=BookingStatus.CONFIRMED,
        current_user=current_user,
    )


@router.patch(
    "/{booking_id}/cancel",
    summary="[Mục 5.6 & BR17] Huỷ ca tập (Soft Delete, chặn Hội viên huỷ sát giờ < 2 tiếng)",
)
def cancel_pt_booking(
    booking_id: int,
    payload: Optional[PTCancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return pt_schedule_service.transition_booking_status(
        db=db,
        booking_id=booking_id,
        target_status=BookingStatus.CANCELLED,
        current_user=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch(
    "/{booking_id}/complete",
    summary="[Mục 5.6 & 3.2.4] Hoàn thành buổi tập (CONFIRMED -> COMPLETED, trừ 1 buổi PT)",
)
def complete_pt_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return pt_schedule_service.transition_booking_status(
        db=db,
        booking_id=booking_id,
        target_status=BookingStatus.COMPLETED,
        current_user=current_user,
    )


@router.patch(
    "/{booking_id}/no-show",
    summary="[Mục 4.5 & 5.6] Đánh dấu học viên vắng mặt không lý do (CONFIRMED -> NO_SHOW, vẫn trừ 1 buổi PT)",
)
def mark_pt_booking_no_show(
    booking_id: int,
    payload: Optional[PTCancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return pt_schedule_service.transition_booking_status(
        db=db,
        booking_id=booking_id,
        target_status=BookingStatus.NO_SHOW,
        current_user=current_user,
        reason=(payload.reason if payload and payload.reason else "Học viên vắng mặt không báo trước (NO_SHOW)"),
    )


@router.put(
    "/{booking_id}/status",
    summary="Cập nhật trạng thái ca tập (Tương thích giao diện Web: CONFIRMED, CANCELLED, COMPLETED, NO_SHOW)",
)
def update_pt_booking_status(
    booking_id: int,
    payload: PTBookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    target_str = payload.status.strip().upper()
    if target_str not in ("CONFIRMED", "CANCELLED", "COMPLETED", "NO_SHOW"):
        raise BadRequestException(
            "Trạng thái chỉ nhận CONFIRMED, CANCELLED, COMPLETED hoặc NO_SHOW."
        )
    return pt_schedule_service.transition_booking_status(
        db=db,
        booking_id=booking_id,
        target_status=BookingStatus(target_str),
        current_user=current_user,
        reason=payload.reason,
    )


@router.delete(
    "/{booking_id}",
    summary="[Mục 1.4 & 5.6] Nghiêm cấm xoá vật lý ca tập để bảo toàn dữ liệu kiểm toán & KPI",
)
def delete_pt_booking_forbidden(
    booking_id: int,
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    raise ForbiddenException(
        f"Hệ thống nghiêm cấm xóa vật lý ca tập #{booking_id} (Mục 1.4 & 5.6 - Bảo toàn lịch sử kiểm toán và lương KPI). "
        "Vui lòng sử dụng thao tác Hủy ca (PATCH /pt-schedules/{id}/cancel)."
    )
