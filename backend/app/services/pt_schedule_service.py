from datetime import date, time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exception import (
    BusinessRuleException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.enums import BookingStatus, ScheduleStatus, UserRole, UserStatus, MemberStatus
from app.models.member import Member
from app.models.trainer_schedule import TrainerSchedule
from app.models.training_booking import TrainingBooking
from app.models.user import User
from app.schemas.pt_schedule import PTScheduleCreate, PTScheduleUpdate


def check_pt_overlap(
    db: Session,
    trainer_id: int,
    booking_date: date,
    start_time: time,
    end_time: time,
    exclude_booking_id: Optional[int] = None,
) -> None:
    """Chặn trùng ca tập của huấn luyện viên PT (BR12)."""
    stmt = select(TrainingBooking).where(
        TrainingBooking.trainer_id == trainer_id,
        TrainingBooking.booking_date == booking_date,
        TrainingBooking.status != BookingStatus.CANCELLED,
        TrainingBooking.start_time < end_time,
        TrainingBooking.end_time > start_time,
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(TrainingBooking.booking_id != exclude_booking_id)

    existing = db.scalars(stmt).first()
    if existing:
        raise ConflictException(
            f"Huấn luyện viên đã có ca tập trùng khung giờ ({existing.start_time.strftime('%H:%M')} - {existing.end_time.strftime('%H:%M')})."
        )


def check_member_overlap(
    db: Session,
    member_id: int,
    booking_date: date,
    start_time: time,
    end_time: time,
    exclude_booking_id: Optional[int] = None,
) -> None:
    """Chặn trùng ca tập của hội viên."""
    stmt = select(TrainingBooking).where(
        TrainingBooking.member_id == member_id,
        TrainingBooking.booking_date == booking_date,
        TrainingBooking.status != BookingStatus.CANCELLED,
        TrainingBooking.start_time < end_time,
        TrainingBooking.end_time > start_time,
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(TrainingBooking.booking_id != exclude_booking_id)

    existing = db.scalars(stmt).first()
    if existing:
        raise ConflictException(
            f"Hội viên đã có ca tập trùng khung giờ ({existing.start_time.strftime('%H:%M')} - {existing.end_time.strftime('%H:%M')})."
        )


def create_pt_schedule(
    db: Session,
    data: PTScheduleCreate,
    current_user: Optional[User] = None,
) -> TrainingBooking:
    """Hội viên (hoặc Admin/Staff) đặt ca tập với PT."""
    # Xác định member_id
    if current_user and current_user.role == UserRole.MEMBER:
        if not current_user.member:
            raise BusinessRuleException("Tài khoản chưa được liên kết với hồ sơ hội viên.")
        member_id = current_user.member.member_id
    else:
        if not data.member_id:
            raise BusinessRuleException("Vui lòng cung cấp member_id của hội viên.")
        member_id = data.member_id

    # Xác thực HLV (PT)
    trainer = db.get(User, data.trainer_id)
    if not trainer:
        raise NotFoundException("Không tìm thấy huấn luyện viên.")
    if trainer.role != UserRole.TRAINER:
        raise BusinessRuleException("Người dùng được chọn không phải là huấn luyện viên (PT).")
    if trainer.status != UserStatus.ACTIVE:
        raise BusinessRuleException("Huấn luyện viên hiện không ở trạng thái hoạt động.")

    # Xác thực Hội viên
    member = db.get(Member, member_id)
    if not member:
        raise NotFoundException("Không tìm thấy thông tin hội viên.")
    if member.status != MemberStatus.ACTIVE:
        raise BusinessRuleException("Hội viên hiện không ở trạng thái hoạt động.")

    # Chặn trùng giờ của PT và của Hội viên
    check_pt_overlap(db, data.trainer_id, data.booking_date, data.start_time, data.end_time)
    check_member_overlap(db, member_id, data.booking_date, data.start_time, data.end_time)

    # Đảm bảo có bản ghi TrainerSchedule tương ứng
    schedule_id = data.schedule_id
    if schedule_id is not None:
        schedule = db.get(TrainerSchedule, schedule_id)
        if not schedule:
            raise NotFoundException("Không tìm thấy ca làm việc chỉ định của huấn luyện viên.")
        if schedule.trainer_id != data.trainer_id:
            raise BusinessRuleException("Ca làm việc không khớp với huấn luyện viên được chọn.")
    else:
        # Tìm hoặc tạo tự động TrainerSchedule
        schedule = db.scalars(
            select(TrainerSchedule).where(
                TrainerSchedule.trainer_id == data.trainer_id,
                TrainerSchedule.work_date == data.booking_date,
                TrainerSchedule.start_time == data.start_time,
            )
        ).first()
        if not schedule:
            schedule = TrainerSchedule(
                trainer_id=data.trainer_id,
                work_date=data.booking_date,
                start_time=data.start_time,
                end_time=data.end_time,
                status=ScheduleStatus.ACTIVE,
            )
            db.add(schedule)
            db.flush()
        schedule_id = schedule.schedule_id

    booking = TrainingBooking(
        member_id=member_id,
        trainer_id=data.trainer_id,
        schedule_id=schedule_id,
        booking_date=data.booking_date,
        start_time=data.start_time,
        end_time=data.end_time,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def list_pt_schedules(
    db: Session,
    trainer_id: Optional[int] = None,
    week: Optional[int] = None,
    year: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    member_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
) -> list[TrainingBooking]:
    """Lấy danh sách ca tập theo PT, theo tuần hoặc theo khoảng ngày."""
    stmt = (
        select(TrainingBooking)
        .options(
            joinedload(TrainingBooking.trainer),
            joinedload(TrainingBooking.member),
        )
    )

    if trainer_id is not None:
        stmt = stmt.where(TrainingBooking.trainer_id == trainer_id)

    if member_id is not None:
        stmt = stmt.where(TrainingBooking.member_id == member_id)

    if status is not None:
        stmt = stmt.where(TrainingBooking.status == status)

    # Lọc theo tuần (ISO calendar: Monday=1 .. Sunday=7)
    if week is not None:
        selected_year = year or date.today().year
        week_start = date.fromisocalendar(selected_year, week, 1)
        week_end = date.fromisocalendar(selected_year, week, 7)
        stmt = stmt.where(
            TrainingBooking.booking_date >= week_start,
            TrainingBooking.booking_date <= week_end,
        )
    else:
        if start_date is not None:
            stmt = stmt.where(TrainingBooking.booking_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(TrainingBooking.booking_date <= end_date)

    stmt = stmt.order_by(TrainingBooking.booking_date.asc(), TrainingBooking.start_time.asc())
    return list(db.scalars(stmt).all())


def get_pt_schedule(db: Session, booking_id: int) -> TrainingBooking:
    """Lấy thông tin chi tiết ca tập theo ID."""
    stmt = (
        select(TrainingBooking)
        .options(
            joinedload(TrainingBooking.trainer),
            joinedload(TrainingBooking.member),
        )
        .where(TrainingBooking.booking_id == booking_id)
    )
    booking = db.scalars(stmt).first()
    if not booking:
        raise NotFoundException("Không tìm thấy ca tập yêu cầu.")
    return booking


def confirm_pt_schedule(
    db: Session,
    booking_id: int,
    current_user: Optional[User] = None,
) -> TrainingBooking:
    """PT (hoặc Admin/Staff) xác nhận ca tập (PENDING -> CONFIRMED)."""
    booking = get_pt_schedule(db, booking_id)

    if current_user:
        if current_user.role == UserRole.TRAINER and current_user.user_id != booking.trainer_id:
            raise ForbiddenException("Bạn không thể xác nhận ca tập của huấn luyện viên khác.")
        if current_user.role == UserRole.MEMBER:
            raise ForbiddenException("Hội viên không có quyền xác nhận ca tập.")

    if not booking.can_transition_to(BookingStatus.CONFIRMED):
        raise BusinessRuleException(
            f"Không thể xác nhận ca tập đang ở trạng thái {booking.status.value}."
        )

    # Kiểm tra lại xung đột trước khi chuyển trạng thái CONFIRMED
    check_pt_overlap(
        db,
        booking.trainer_id,
        booking.booking_date,
        booking.start_time,
        booking.end_time,
        exclude_booking_id=booking.booking_id,
    )
    check_member_overlap(
        db,
        booking.member_id,
        booking.booking_date,
        booking.start_time,
        booking.end_time,
        exclude_booking_id=booking.booking_id,
    )

    booking.status = BookingStatus.CONFIRMED
    db.commit()
    db.refresh(booking)
    return booking


def cancel_pt_schedule(
    db: Session,
    booking_id: int,
    current_user: Optional[User] = None,
    _reason: Optional[str] = None,
) -> TrainingBooking:
    """PT hoặc Hội viên huỷ ca tập (PENDING/CONFIRMED -> CANCELLED)."""
    booking = get_pt_schedule(db, booking_id)

    if current_user:
        if current_user.role == UserRole.TRAINER and current_user.user_id != booking.trainer_id:
            raise ForbiddenException("Bạn không thể huỷ ca tập của huấn luyện viên khác.")
        if current_user.role == UserRole.MEMBER:
            if not current_user.member or current_user.member.member_id != booking.member_id:
                raise ForbiddenException("Bạn không thể huỷ ca tập của hội viên khác.")

    if not booking.can_transition_to(BookingStatus.CANCELLED):
        raise BusinessRuleException(
            f"Không thể huỷ ca tập đang ở trạng thái {booking.status.value}."
        )

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking


def complete_pt_schedule(
    db: Session,
    booking_id: int,
    current_user: Optional[User] = None,
) -> TrainingBooking:
    """Đánh dấu hoàn thành ca tập (CONFIRMED -> COMPLETED)."""
    booking = get_pt_schedule(db, booking_id)

    if current_user:
        if current_user.role == UserRole.TRAINER and current_user.user_id != booking.trainer_id:
            raise ForbiddenException("Bạn không thể đánh dấu hoàn thành ca tập của huấn luyện viên khác.")
        if current_user.role == UserRole.MEMBER:
            raise ForbiddenException("Hội viên không có quyền đánh dấu hoàn thành ca tập.")

    if not booking.can_transition_to(BookingStatus.COMPLETED):
        raise BusinessRuleException(
            f"Không thể đánh dấu hoàn thành ca tập đang ở trạng thái {booking.status.value}."
        )

    booking.status = BookingStatus.COMPLETED
    db.commit()
    db.refresh(booking)
    return booking


def update_pt_schedule(
    db: Session,
    booking_id: int,
    data: PTScheduleUpdate,
    current_user: Optional[User] = None,
) -> TrainingBooking:
    """Cập nhật thông tin ca tập (chỉ khi đang ở PENDING hoặc CONFIRMED)."""
    booking = get_pt_schedule(db, booking_id)

    if current_user:
        if current_user.role == UserRole.TRAINER and current_user.user_id != booking.trainer_id:
            raise ForbiddenException("Bạn không thể chỉnh sửa ca tập của huấn luyện viên khác.")
        if current_user.role == UserRole.MEMBER:
            if not current_user.member or current_user.member.member_id != booking.member_id:
                raise ForbiddenException("Bạn không thể chỉnh sửa ca tập của hội viên khác.")

    if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
        raise BusinessRuleException(
            f"Không thể chỉnh sửa ca tập đã ở trạng thái {booking.status.value}."
        )

    new_date = data.booking_date or booking.booking_date
    new_start = data.start_time or booking.start_time
    new_end = data.end_time or booking.end_time

    if new_end <= new_start:
        raise BusinessRuleException("Giờ kết thúc phải sau giờ bắt đầu.")
    if new_date < date.today():
        raise BusinessRuleException("Ngày tập không được ở trong quá khứ.")

    # Chặn trùng giờ
    check_pt_overlap(
        db,
        booking.trainer_id,
        new_date,
        new_start,
        new_end,
        exclude_booking_id=booking.booking_id,
    )
    check_member_overlap(
        db,
        booking.member_id,
        new_date,
        new_start,
        new_end,
        exclude_booking_id=booking.booking_id,
    )

    booking.booking_date = new_date
    booking.start_time = new_start
    booking.end_time = new_end

    db.commit()
    db.refresh(booking)
    return booking


def delete_pt_schedule(
    db: Session,
    booking_id: int,
    current_user: Optional[User] = None,
) -> None:
    """Xoá ca tập khỏi hệ thống."""
    booking = get_pt_schedule(db, booking_id)

    if current_user:
        if current_user.role == UserRole.TRAINER and current_user.user_id != booking.trainer_id:
            raise ForbiddenException("Bạn không có quyền xoá ca tập này.")
        if current_user.role == UserRole.MEMBER:
            raise ForbiddenException("Hội viên không có quyền xoá trực tiếp ca tập (hãy sử dụng thao tác huỷ).")

    db.delete(booking)
    db.commit()

