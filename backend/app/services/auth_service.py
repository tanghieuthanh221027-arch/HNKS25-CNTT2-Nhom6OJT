from datetime import date
from sqlalchemy.orm import Session

from app.core.exception import ConflictException, ForbiddenException, UnauthorizedException
from app.core.qr_utils import generate_card_code, generate_qr_base64
from app.core.security import create_access_token, hash_password, verify_password
from app.db.seed import seed_all
from app.models.enums import Gender, MemberStatus, UserRole
from app.models.member import Member
from app.models.member_card import MemberCard
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


def ensure_member_and_card(db: Session, user: User) -> tuple[Member | None, MemberCard | None]:
    """Đảm bảo mọi tài khoản MEMBER đều có bản ghi Member và thẻ điện tử MemberCard có QR."""
    if user.role != UserRole.MEMBER:
        return None, None

    member = db.query(Member).filter(Member.user_id == user.user_id).first()
    if not member:
        member = (
            db.query(Member)
            .filter((Member.email == user.email) | (Member.phone == user.phone))
            .first()
        )
        if member and member.user_id is None:
            member.user_id = user.user_id
            db.flush()
    if not member:
        member = Member(
            user_id=user.user_id,
            full_name=user.full_name,
            gender=Gender.MALE,
            date_of_birth=date(2000, 1, 1),
            phone=user.phone,
            email=user.email,
            address="Hà Nội",
            join_date=date.today(),
            status=MemberStatus.ACTIVE,
        )
        db.add(member)
        db.flush()

    card = db.query(MemberCard).filter(MemberCard.user_id == user.user_id).first()
    if not card:
        code = generate_card_code(user.user_id)
        card = MemberCard(
            user_id=user.user_id,
            member_id=member.member_id,
            card_code=code,
            qr_base64=generate_qr_base64(code),
        )
        db.add(card)
        db.flush()
    elif card.member_id != member.member_id:
        card.member_id = member.member_id
        db.flush()

    return member, card


def register_user(db: Session, user_in: RegisterRequest) -> User:
    if db.query(User).filter(User.email == user_in.email.strip().lower()).first():
        raise ConflictException(message="Email đã tồn tại trong hệ thống.")

    if db.query(User).filter(User.phone == user_in.phone.strip()).first():
        raise ConflictException(message="Số điện thoại đã tồn tại trong hệ thống.")

    base_username = user_in.email.split("@")[0]
    username = base_username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}{counter}"
        counter += 1

    new_user = User(
        username=username,
        email=user_in.email,
        phone=user_in.phone,
        full_name=user_in.name,
        password_hash=hash_password(user_in.password),
        role=UserRole.MEMBER,
    )

    db.add(new_user)
    db.flush()
    ensure_member_and_card(db, new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def _find_user_by_login(db: Session, login_id: str) -> User | None:
    clean_id = login_id.strip()
    return (
        db.query(User)
        .filter(
            (User.email == clean_id.lower())
            | (User.username == clean_id)
            | (User.phone == clean_id)
        )
        .first()
    )


def authenticate_user(db: Session, login_data: LoginRequest) -> dict:
    user = _find_user_by_login(db, login_data.username)

    # Nếu chưa tìm thấy tài khoản mẫu (do DB chưa chạy seed_all), tự động seed ngay lập tức
    if not user or not verify_password(login_data.password, user.password_hash):
        try:
            seed_all(db)
            user = _find_user_by_login(db, login_data.username)
        except Exception:
            db.rollback()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise UnauthorizedException(
            message="Email/Tên đăng nhập hoặc mật khẩu không chính xác."
        )

    if not user.can_login:
        raise ForbiddenException(
            message="Tài khoản đã bị khóa hoặc không thể đăng nhập."
        )

    if user.role == UserRole.MEMBER:
        ensure_member_and_card(db, user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user_id=user.user_id, role=user.role)

    return {
        "token": {
            "access_token": access_token,
            "token_type": "bearer",
        },
        "user": user,
    }
