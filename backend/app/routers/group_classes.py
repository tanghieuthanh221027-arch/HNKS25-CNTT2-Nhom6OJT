from datetime import date, datetime, time
from typing import Any, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exception import BusinessRuleException, ConflictException, NotFoundException
from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_staff_or_admin
from app.models.group_class import GroupClass, GroupClassEnrollment
from app.models.user import User

router = APIRouter(prefix="/group-classes", tags=["Group Classes (Yoga, Zumba, HIIT)"])


class GroupClassCreate(BaseModel):
    class_name: str = Field(min_length=2, max_length=120)
    category: str = Field(default="YOGA")
    trainer_id: Optional[int] = None
    room: str = Field(min_length=2, max_length=100)
    schedule_date: date
    start_time: time
    end_time: time
    max_capacity: int = Field(default=15, gt=0, le=100)
    description: Optional[str] = None


class AttendanceUpdate(BaseModel):
    status: str = Field(description="ATTENDED hoặc ABSENT")


def _serialize_group_class(
    db: Session,
    gc: GroupClass,
    current_user_id: Optional[int] = None,
) -> dict[str, Any]:
    trainer = (
        db.query(User).filter(User.user_id == gc.trainer_id).first()
        if gc.trainer_id
        else None
    )
    enrolled_count = (
        db.query(func.count(GroupClassEnrollment.enrollment_id))
        .filter(
            GroupClassEnrollment.class_id == gc.class_id,
            GroupClassEnrollment.status.in_(["REGISTERED", "ATTENDED"]),
        )
        .scalar()
        or 0
    )
    my_enrollment = None
    if current_user_id:
        my_enrollment = (
            db.query(GroupClassEnrollment)
            .filter(
                GroupClassEnrollment.class_id == gc.class_id,
                GroupClassEnrollment.user_id == current_user_id,
                GroupClassEnrollment.status != "CANCELLED",
            )
            .first()
        )

    return {
        "class_id": gc.class_id,
        "class_name": gc.class_name,
        "category": gc.category,
        "trainer_id": gc.trainer_id,
        "trainer_name": trainer.full_name if trainer else "HLV Ducky Gym",
        "room": gc.room,
        "schedule_date": gc.schedule_date,
        "start_time": gc.start_time.strftime("%H:%M"),
        "end_time": gc.end_time.strftime("%H:%M"),
        "max_capacity": gc.max_capacity,
        "enrolled_count": enrolled_count,
        "available_slots": max(0, gc.max_capacity - enrolled_count),
        "is_full": enrolled_count >= gc.max_capacity,
        "is_enrolled": my_enrollment is not None,
        "my_enrollment_status": my_enrollment.status if my_enrollment else None,
        "status": gc.status,
        "description": gc.description,
    }


@router.get("", summary="[Bonus T3CD532] Danh sách lịch lớp tập nhóm (Yoga, Zumba, HIIT...)")
def list_group_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    classes = (
        db.query(GroupClass)
        .order_by(GroupClass.schedule_date.asc(), GroupClass.start_time.asc())
        .all()
    )
    return [_serialize_group_class(db, gc, current_user.user_id) for gc in classes]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="[Bonus T3CD532 - STAFF/ADMIN] Tạo lịch lớp tập nhóm mới",
)
def create_group_class(
    payload: GroupClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    if payload.end_time <= payload.start_time:
        raise BusinessRuleException("Giờ kết thúc lớp tập phải lớn hơn giờ bắt đầu.")

    gc = GroupClass(
        class_name=payload.class_name.strip(),
        category=payload.category.strip().upper(),
        trainer_id=payload.trainer_id,
        room=payload.room.strip(),
        schedule_date=payload.schedule_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        max_capacity=payload.max_capacity,
        status="ACTIVE",
        description=payload.description,
    )
    db.add(gc)
    db.commit()
    db.refresh(gc)
    return _serialize_group_class(db, gc, current_user.user_id)


@router.post(
    "/{class_id}/enroll",
    summary="[Bonus T3CD532] Hội viên đăng ký tham gia lớp tập nhóm (kiểm tra giới hạn sĩ số)",
)
def enroll_group_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    gc = db.query(GroupClass).filter(GroupClass.class_id == class_id).first()
    if not gc or gc.status != "ACTIVE":
        raise NotFoundException("Lớp tập không tồn tại hoặc đã đóng đăng ký.")

    existing = (
        db.query(GroupClassEnrollment)
        .filter(
            GroupClassEnrollment.class_id == class_id,
            GroupClassEnrollment.user_id == current_user.user_id,
        )
        .first()
    )
    if existing and existing.status in ("REGISTERED", "ATTENDED"):
        raise ConflictException("Bạn đã đăng ký lớp tập này rồi.")

    enrolled_count = (
        db.query(func.count(GroupClassEnrollment.enrollment_id))
        .filter(
            GroupClassEnrollment.class_id == class_id,
            GroupClassEnrollment.status.in_(["REGISTERED", "ATTENDED"]),
        )
        .scalar()
        or 0
    )
    if enrolled_count >= gc.max_capacity:
        raise BusinessRuleException(
            f"Lớp '{gc.class_name}' đã đủ sĩ số tối đa ({gc.max_capacity} học viên)."
        )

    if existing:
        existing.status = "REGISTERED"
    else:
        enr = GroupClassEnrollment(
            class_id=class_id,
            user_id=current_user.user_id,
            status="REGISTERED",
        )
        db.add(enr)

    db.commit()
    res = _serialize_group_class(db, gc, current_user.user_id)
    res["message"] = f"Đăng ký lớp '{gc.class_name}' thành công!"
    return res


@router.delete(
    "/{class_id}/enroll",
    summary="[Bonus T3CD532] Hội viên hủy đăng ký lớp tập nhóm",
)
def cancel_group_class_enrollment(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    gc = db.query(GroupClass).filter(GroupClass.class_id == class_id).first()
    if not gc:
        raise NotFoundException("Lớp tập không tồn tại.")

    existing = (
        db.query(GroupClassEnrollment)
        .filter(
            GroupClassEnrollment.class_id == class_id,
            GroupClassEnrollment.user_id == current_user.user_id,
        )
        .first()
    )
    if not existing or existing.status == "CANCELLED":
        raise NotFoundException("Bạn chưa đăng ký lớp tập này.")

    existing.status = "CANCELLED"
    db.commit()
    res = _serialize_group_class(db, gc, current_user.user_id)
    res["message"] = f"Đã hủy đăng ký lớp '{gc.class_name}'."
    return res


@router.get(
    "/{class_id}/enrollments",
    summary="[Bonus T3CD532] Xem danh sách học viên đăng ký lớp để điểm danh",
)
def list_class_enrollments(
    class_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    gc = db.query(GroupClass).filter(GroupClass.class_id == class_id).first()
    if not gc:
        raise NotFoundException("Lớp tập không tồn tại.")

    rows = (
        db.query(GroupClassEnrollment, User)
        .join(User, User.user_id == GroupClassEnrollment.user_id)
        .filter(
            GroupClassEnrollment.class_id == class_id,
            GroupClassEnrollment.status != "CANCELLED",
        )
        .order_by(GroupClassEnrollment.created_at.asc())
        .all()
    )
    students = [
        {
            "enrollment_id": enr.enrollment_id,
            "user_id": u.user_id,
            "full_name": u.full_name,
            "phone": u.phone,
            "email": u.email,
            "status": enr.status,
            "attended_at": enr.attended_at,
        }
        for enr, u in rows
    ]
    return {
        "class_info": _serialize_group_class(db, gc),
        "students": students,
    }


@router.put(
    "/{class_id}/attendance/{enrollment_id}",
    summary="[Bonus T3CD532] Lễ tân điểm danh học viên lớp tập nhóm (ATTENDED / ABSENT)",
)
def mark_class_attendance(
    class_id: int,
    enrollment_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    enr = (
        db.query(GroupClassEnrollment)
        .filter(
            GroupClassEnrollment.enrollment_id == enrollment_id,
            GroupClassEnrollment.class_id == class_id,
        )
        .first()
    )
    if not enr:
        raise NotFoundException("Không tìm thấy bản ghi đăng ký học viên.")

    st = payload.status.strip().upper()
    if st not in ("ATTENDED", "ABSENT", "REGISTERED"):
        raise BusinessRuleException("Trạng thái điểm danh chỉ nhận ATTENDED, ABSENT hoặc REGISTERED.")

    enr.status = st
    enr.attended_at = datetime.now() if st == "ATTENDED" else None
    db.commit()
    return {
        "message": f"Đã cập nhật điểm danh ({st}) thành công.",
        "enrollment_id": enr.enrollment_id,
        "status": enr.status,
        "attended_at": enr.attended_at,
    }
