from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exception import BusinessRuleException, ConflictException
from models.user import User
from schemas.user import UserUpdateSelf


def update_my_profile(
    db: Session,
    current_user: User,
    data: UserUpdateSelf,
) -> User:
    update_data = data.model_dump(exclude_unset=True)

    # Ràng buộc DB ck_users_trainer_only_fields: chỉ TRAINER mới được cập nhật bio
    if "bio" in update_data and update_data["bio"] is not None and not current_user.is_trainer:
        raise BusinessRuleException("Trường tiểu sử (bio) chỉ áp dụng cho vai trò TRAINER (PT)")

    # Kiểm tra trùng email (BR03)
    if "email" in update_data and update_data["email"] is not None:
        new_email = update_data["email"].strip().lower()
        if new_email != current_user.email:
            existing_email = db.scalar(
                select(User).where(User.email == new_email, User.user_id != current_user.user_id)
            )
            if existing_email:
                raise ConflictException("Email này đã được sử dụng (BR03).")
            current_user.email = new_email
            if current_user.member:
                current_user.member.email = new_email

    # Kiểm tra trùng số điện thoại (BR03)
    if "phone" in update_data and update_data["phone"] is not None:
        new_phone = update_data["phone"].strip()
        if new_phone != current_user.phone:
            existing_phone = db.scalar(
                select(User).where(User.phone == new_phone, User.user_id != current_user.user_id)
            )
            if existing_phone:
                raise ConflictException("Số điện thoại này đã được sử dụng (BR03).")
            current_user.phone = new_phone
            if current_user.member:
                current_user.member.phone = new_phone

    # Cập nhật họ tên (đồng bộ sang bảng members nếu có)
    if "full_name" in update_data and update_data["full_name"] is not None:
        current_user.full_name = update_data["full_name"]
        if current_user.member:
            current_user.member.full_name = update_data["full_name"]

    # Cập nhật bio (cho TRAINER)
    if "bio" in update_data and current_user.is_trainer:
        current_user.bio = update_data["bio"]

    db.commit()
    db.refresh(current_user)
    return current_user