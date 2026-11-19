from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.enums import BookingStatus
from app.models.training_booking import TrainingBooking
from app.models.user import User
from app.schemas.pt_schedule import (
    PTScheduleCancelRequest,
    PTScheduleCreate,
    PTScheduleResponse,
    PTScheduleUpdate,
)
from app.services import pt_schedule_service

router = APIRouter(prefix="/pt-schedules", tags=["PT Schedules"])


def _to_response(booking: TrainingBooking) -> PTScheduleResponse:
    return PTScheduleResponse(
        booking_id=booking.booking_id,
        schedule_id=booking.schedule_id,
        trainer_id=booking.trainer_id,
        trainer_name=booking.trainer.full_name if booking.trainer else None,
        member_id=booking.member_id,
        member_name=booking.member.full_name if booking.member else None,
        booking_date=booking.booking_date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        created_at=booking.created_at,
    )


@router.post("", response_model=PTScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    data: PTScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hội viên đặt ca tập với PT.
    Tự động chặn trùng giờ của PT và của hội viên.
    """
    booking = pt_schedule_service.create_pt_schedule(db=db, data=data, current_user=current_user)
    return _to_response(booking)


@router.get("", response_model=list[PTScheduleResponse])
def get_schedules(
    trainer_id: Optional[int] = Query(None, description="Lọc theo ID của PT"),
    week: Optional[int] = Query(None, ge=1, le=53, description="Lọc theo tuần trong năm (1-53)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Năm (mặc định năm hiện tại khi dùng tuần)"),
    start_date: Optional[date] = Query(None, description="Lọc từ ngày (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Lọc đến ngày (YYYY-MM-DD)"),
    member_id: Optional[int] = Query(None, description="Lọc theo ID hội viên"),
    booking_status: Optional[BookingStatus] = Query(None, alias="status", description="Lọc theo trạng thái ca tập"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách ca tập theo PT và theo tuần hoặc theo khoảng ngày.
    """
    clean_trainer_id = trainer_id if isinstance(trainer_id, int) else None
    clean_week = week if isinstance(week, int) else None
    clean_year = year if isinstance(year, int) else None
    clean_start_date = start_date if isinstance(start_date, date) else None
    clean_end_date = end_date if isinstance(end_date, date) else None
    clean_member_id = member_id if isinstance(member_id, int) else None
    clean_status = booking_status if isinstance(booking_status, BookingStatus) else None

    bookings = pt_schedule_service.list_pt_schedules(
        db=db,
        trainer_id=clean_trainer_id,
        week=clean_week,
        year=clean_year,
        start_date=clean_start_date,
        end_date=clean_end_date,
        member_id=clean_member_id,
        status=clean_status,
    )
    return [_to_response(b) for b in bookings]


@router.get("/{booking_id}", response_model=PTScheduleResponse)
def get_schedule_detail(
    booking_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Xem chi tiết một ca tập.
    """
    booking = pt_schedule_service.get_pt_schedule(db=db, booking_id=booking_id)
    return _to_response(booking)


@router.put("/{booking_id}", response_model=PTScheduleResponse)
def update_schedule(
    booking_id: int,
    data: PTScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chỉnh sửa ca tập (ngày, giờ) có kiểm tra chặn trùng lịch.
    """
    booking = pt_schedule_service.update_pt_schedule(
        db=db,
        booking_id=booking_id,
        data=data,
        current_user=current_user,
    )
    return _to_response(booking)


@router.patch("/{booking_id}/confirm", response_model=PTScheduleResponse)
def confirm_schedule(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Huấn luyện viên PT xác nhận ca tập.
    """
    booking = pt_schedule_service.confirm_pt_schedule(
        db=db,
        booking_id=booking_id,
        current_user=current_user,
    )
    return _to_response(booking)


@router.patch("/{booking_id}/cancel", response_model=PTScheduleResponse)
def cancel_schedule(
    booking_id: int,
    cancel_in: Optional[PTScheduleCancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Huấn luyện viên hoặc hội viên huỷ ca tập.
    """
    reason = cancel_in.reason if cancel_in else None
    booking = pt_schedule_service.cancel_pt_schedule(
        db=db,
        booking_id=booking_id,
        current_user=current_user,
        _reason=reason,
    )
    return _to_response(booking)


@router.patch("/{booking_id}/complete", response_model=PTScheduleResponse)
def complete_schedule(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Đánh dấu hoàn thành ca tập.
    """
    booking = pt_schedule_service.complete_pt_schedule(
        db=db,
        booking_id=booking_id,
        current_user=current_user,
    )
    return _to_response(booking)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xoá ca tập khỏi hệ thống.
    """
    pt_schedule_service.delete_pt_schedule(
        db=db,
        booking_id=booking_id,
        current_user=current_user,
    )
    return None
