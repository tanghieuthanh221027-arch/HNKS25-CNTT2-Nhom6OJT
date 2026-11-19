from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.exception import ForbiddenException, NotFoundException
from app.models.attendance_record import AttendanceRecord
from app.models.enums import AttendanceStatus, UserRole
from app.models.member import Member
from app.models.user import User
from app.schemas.attendance import AttendanceFilter
from app.schemas.common import Page, PageParams

STAFF_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.ADMIN, UserRole.STAFF, UserRole.CASHIER, UserRole.TRAINER}
)


def _resolve_member_id_for_user(db: Session, current_user: User) -> Optional[int]:
    if current_user.role != UserRole.MEMBER:
        return None
    member = db.query(Member).filter(Member.user_id == current_user.user_id).first()
    return member.member_id if member else None


def get_checkin_history(
    db: Session,
    current_user: User,
    params: PageParams,
    filters: AttendanceFilter,
) -> Page[AttendanceRecord]:
    is_staff = current_user.role in STAFF_ROLES

    if not is_staff:
        my_member_id = _resolve_member_id_for_user(db, current_user)
        if my_member_id is None:
            raise NotFoundException("Không tìm thấy hồ sơ hội viên liên kết với tài khoản này.")

        if filters.member_id is not None and filters.member_id != my_member_id:
            raise ForbiddenException("Bạn chỉ có thể xem lịch sử của chính mình.")

        filters = AttendanceFilter(
            member_id=my_member_id,
            status=filters.status,
            date_from=filters.date_from,
            date_to=filters.date_to,
        )

    base_q = (
        db.query(AttendanceRecord)
        .options(joinedload(AttendanceRecord.member))
        .order_by(AttendanceRecord.check_in.desc())
    )

    if filters.member_id is not None:
        base_q = base_q.filter(AttendanceRecord.member_id == filters.member_id)

    if filters.status is not None:
        base_q = base_q.filter(AttendanceRecord.status == filters.status)

    if filters.date_from is not None:
        dt_from = datetime.combine(filters.date_from, datetime.min.time())
        base_q = base_q.filter(AttendanceRecord.check_in >= dt_from)

    if filters.date_to is not None:
        dt_to = datetime.combine(filters.date_to + timedelta(days=1), datetime.min.time())
        base_q = base_q.filter(AttendanceRecord.check_in < dt_to)

    total: int = base_q.count()
    items: list[AttendanceRecord] = (
        base_q.offset(params.offset).limit(params.size).all()
    )

    return Page.create(items=items, total=total, params=params)


def get_active_count(db: Session) -> int:
    count: int = (
        db.query(func.count(AttendanceRecord.attendance_id))
        .filter(AttendanceRecord.status == AttendanceStatus.CHECKED_IN)
        .scalar()
    ) or 0
    return count
