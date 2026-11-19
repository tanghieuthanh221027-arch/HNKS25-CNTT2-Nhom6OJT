from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.enums import AttendanceStatus, UserRole
from app.models.user import User
from app.schemas.attendance import (
    ActiveCountResponse,
    AttendanceDetailResponse,
    AttendanceFilter,
    CheckinHistoryPage,
)
from app.schemas.common import Page, PageParams
from app.services import checkin_service

router = APIRouter(prefix="/checkins", tags=["Check-ins"])

_STAFF_ROLES = (UserRole.ADMIN, UserRole.STAFF, UserRole.CASHIER, UserRole.TRAINER)


@router.get(
    "/history",
    response_model=CheckinHistoryPage,
    summary="Lịch sử ra vào (có phân trang & lọc)",
)
def list_checkin_history(
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    size: int = Query(default=20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    member_id: Optional[int] = Query(default=None, gt=0, description="ID hội viên"),
    status: Optional[AttendanceStatus] = Query(default=None, description="Trạng thái"),
    date_from: Optional[date] = Query(default=None, description="Từ ngày (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(default=None, description="Đến ngày (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Page[AttendanceDetailResponse]:
    params = PageParams(page=page, size=size)
    filters = AttendanceFilter(
        member_id=member_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return checkin_service.get_checkin_history(
        db=db,
        current_user=current_user,
        params=params,
        filters=filters,
    )


@router.get(
    "/active-count",
    response_model=ActiveCountResponse,
    summary="Số người đang tập hiện tại",
)
def get_active_count(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*_STAFF_ROLES)),
) -> ActiveCountResponse:
    count = checkin_service.get_active_count(db=db)
    return ActiveCountResponse(active_count=count)
