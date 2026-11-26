from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception import BusinessRuleException, ConflictException, UnauthorizedException
from app.core.security import hash_password, verify_password
from app.core.timezone_utils import today_vn
from app.models.body_metric import BodyMetric
from app.models.member_card import MemberCard
from app.models.user import User
from app.schemas.user import UserUpdateSelf
from app.services.auth_service import ensure_member_and_card


def compute_badges(total_checkins: int, streak_days: int) -> list[dict[str, Any]]:
    """Tính huy hiệu thành tích hội viên (Bonus T3CD518: mốc 10, 30, 100 buổi)."""
    milestones = [
        (10, "Tân Binh Kỷ Luật", "military_tech", "Hoàn thành 10 buổi tập tại Ducky Gym"),
        (30, "Chiến Binh Bền Bỉ", "workspace_premium", "Hoàn thành 30 buổi tập tại Ducky Gym"),
        (100, "Huyền Thoại Ducky Gym", "emoji_events", "Hoàn thành 100 buổi tập tại Ducky Gym"),
    ]
    result = []
    for target, title, icon, desc in milestones:
        result.append(
            {
                "threshold": target,
                "title": title,
                "icon": icon,
                "description": desc,
                "unlocked": total_checkins >= target,
                "progress": min(100, int((total_checkins / target) * 100)),
            }
        )
    return result


def build_user_profile_dict(db: Session, current_user: User) -> dict[str, Any]:
    """Đóng gói thông tin User kèm chiều cao, cân nặng, BMI, mã thẻ QR, streak & huy hiệu."""
    member, card = ensure_member_and_card(db, current_user)
    if member or card:
        db.commit()

    height_cm = card.height_cm if card else None
    weight_kg = card.weight_kg if card else None
    bmi = card.bmi if card else None
    if height_cm and weight_kg and not bmi:
        bmi = round(weight_kg / ((height_cm / Decimal("100")) ** 2), 1)

    total_ci = card.total_checkins if card else 0
    streak = card.streak_days if card else 0

    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "position": current_user.position,
        "hire_date": current_user.hire_date,
        "salary": current_user.salary,
        "specialization": current_user.specialization,
        "experience_years": current_user.experience_years,
        "bio": current_user.bio,
        "status": current_user.status,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "member_id": member.member_id if member else None,
        "member_code": card.card_code if card else f"DG-{current_user.user_id:06d}",
        "qr_base64": card.qr_base64 if card else None,
        "gender": member.gender.value if member and member.gender else None,
        "date_of_birth": member.date_of_birth if member else None,
        "address": member.address if member else None,
        "emergency_contact": card.emergency_contact if card else None,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
        "target_weight_kg": card.target_weight_kg if card else None,
        "weekly_workouts": card.weekly_workouts if card else None,
        "streak_days": streak,
        "total_checkins": total_ci,
        "badges": compute_badges(total_ci, streak),
    }


def update_my_profile(
    db: Session,
    current_user: User,
    data: UserUpdateSelf,
) -> dict[str, Any]:
    update_data = data.model_dump(exclude_unset=True)

    # Đổi mật khẩu nếu có truyền new_password (Task T067D56)
    if update_data.get("new_password"):
        curr_pw = update_data.get("current_password")
        if not curr_pw or not verify_password(curr_pw, current_user.password_hash):
            raise UnauthorizedException("Mật khẩu hiện tại không chính xác.")
        if len(update_data["new_password"]) < 8:
            raise BusinessRuleException("Mật khẩu mới phải có ít nhất 8 ký tự.")
        current_user.password_hash = hash_password(update_data["new_password"])

    # Kiểm tra trùng email (BR03)
    if "email" in update_data and update_data["email"] is not None:
        new_email = update_data["email"].strip().lower()
        if new_email != current_user.email:
            existing_email = db.scalar(
                select(User).where(
                    User.email == new_email, User.user_id != current_user.user_id
                )
            )
            if existing_email:
                raise ConflictException("Email này đã được sử dụng (BR03).")
            current_user.email = new_email

    # Kiểm tra trùng số điện thoại (BR03)
    if "phone" in update_data and update_data["phone"] is not None:
        new_phone = update_data["phone"].strip()
        if new_phone != current_user.phone:
            existing_phone = db.scalar(
                select(User).where(
                    User.phone == new_phone, User.user_id != current_user.user_id
                )
            )
            if existing_phone:
                raise ConflictException("Số điện thoại này đã được sử dụng (BR03).")
            current_user.phone = new_phone

    # Cập nhật họ tên
    if "full_name" in update_data and update_data["full_name"] is not None:
        current_user.full_name = update_data["full_name"]

    # Cập nhật bio (cho TRAINER)
    if "bio" in update_data and current_user.is_trainer:
        current_user.bio = update_data["bio"]

    member, card = ensure_member_and_card(db, current_user)
    if member:
        if "gender" in update_data and update_data["gender"] is not None:
            member.gender = update_data["gender"]
        if "date_of_birth" in update_data and update_data["date_of_birth"] is not None:
            member.date_of_birth = update_data["date_of_birth"]
        if "address" in update_data and update_data["address"] is not None:
            member.address = update_data["address"]

    if card:
        if "emergency_contact" in update_data:
            card.emergency_contact = update_data["emergency_contact"]
        if "target_weight_kg" in update_data:
            card.target_weight_kg = update_data["target_weight_kg"]
        if "weekly_workouts" in update_data:
            card.weekly_workouts = update_data["weekly_workouts"]
        if "height_cm" in update_data and update_data["height_cm"] is not None:
            card.height_cm = update_data["height_cm"]
        if "weight_kg" in update_data and update_data["weight_kg"] is not None:
            card.weight_kg = update_data["weight_kg"]

        # Tự động tính lại BMI khi có chiều cao & cân nặng (Task T067D56)
        if card.height_cm and card.weight_kg and card.height_cm > 0:
            card.bmi = round(
                card.weight_kg / ((card.height_cm / Decimal("100")) ** 2), 1
            )
            # Tự động lưu bản ghi vào lịch sử BodyMetric nếu có thay đổi chiều cao/cân nặng (Bonus T3CD409)
            if "height_cm" in update_data or "weight_kg" in update_data:
                bm = BodyMetric(
                    user_id=current_user.user_id,
                    recorded_date=today_vn(),
                    height_cm=card.height_cm,
                    weight_kg=card.weight_kg,
                    bmi=card.bmi,
                    notes="Cập nhật từ hồ sơ cá nhân",
                )
                db.add(bm)

    db.commit()
    db.refresh(current_user)
    return build_user_profile_dict(db, current_user)
