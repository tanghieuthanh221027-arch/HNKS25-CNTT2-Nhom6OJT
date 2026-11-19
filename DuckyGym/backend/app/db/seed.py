import hashlib
import secrets
from datetime import date
from decimal import Decimal

from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.models.enums import Gender, PlanStatus, UserRole, UserStatus
from app.models.member import Member
from app.models.membership_plan import MembershipPlan
from app.models.user import User


PLANS = [
    {
        "plan_name": "Basic Monthly",
        "category": "STANDARD",
        "duration_days": 30,
        "price": Decimal("300000"),
        "description": "Gym access for one month",
        "status": PlanStatus.ACTIVE,
    },
    {
        "plan_name": "Quarterly",
        "category": "STANDARD",
        "duration_days": 90,
        "price": Decimal("750000"),
        "description": "Gym access for three months",
        "status": PlanStatus.ACTIVE,
    },
    {
        "plan_name": "Half Year",
        "category": "STANDARD",
        "duration_days": 180,
        "price": Decimal("1300000"),
        "description": "Gym access for six months",
        "status": PlanStatus.ACTIVE,
    },
    {
        "plan_name": "Annual",
        "category": "STANDARD",
        "duration_days": 365,
        "price": Decimal("2400000"),
        "description": "Gym access for one year",
        "status": PlanStatus.ACTIVE,
    },
    {
        "plan_name": "Monthly with PT",
        "category": "PERSONAL_TRAINING",
        "duration_days": 30,
        "price": Decimal("900000"),
        "description": "Gym access and personal training",
        "status": PlanStatus.ACTIVE,
    },
]

MEMBERS = [
    ("Nguyen An", Gender.MALE, date(1995, 1, 12)),
    ("Tran Binh", Gender.MALE, date(1992, 3, 5)),
    ("Le Chi", Gender.FEMALE, date(1998, 7, 21)),
    ("Pham Dung", Gender.MALE, date(1990, 11, 9)),
    ("Hoang Giang", Gender.FEMALE, date(1996, 2, 14)),
    ("Vu Hanh", Gender.FEMALE, date(1994, 6, 30)),
    ("Dang Khoa", Gender.MALE, date(1989, 8, 18)),
    ("Bui Linh", Gender.FEMALE, date(2000, 4, 2)),
    ("Do Minh", Gender.MALE, date(1993, 9, 15)),
    ("Ngo Nhi", Gender.FEMALE, date(1997, 12, 4)),
    ("Duong Phong", Gender.MALE, date(1991, 5, 27)),
    ("Ly Quynh", Gender.FEMALE, date(1999, 10, 11)),
    ("Truong Son", Gender.MALE, date(1988, 3, 19)),
    ("Mai Tam", Gender.FEMALE, date(1995, 8, 7)),
    ("Cao Uyen", Gender.FEMALE, date(2001, 1, 25)),
    ("Dinh Vinh", Gender.MALE, date(1994, 4, 13)),
    ("Phan Xuan", Gender.MALE, date(1996, 6, 8)),
    ("Lam Yen", Gender.FEMALE, date(1993, 2, 22)),
    ("Ta Hai", Gender.MALE, date(1997, 7, 16)),
    ("Kim My", Gender.FEMALE, date(1992, 11, 3)),
]

TRAINERS = [
    (
        "trainer01",
        "Alex Trainer",
        "alex.trainer@duckygym.local",
        "0901000001",
        "Strength training",
    ),
    (
        "trainer02",
        "Bella Trainer",
        "bella.trainer@duckygym.local",
        "0901000002",
        "Weight loss",
    ),
    (
        "trainer03",
        "Chris Trainer",
        "chris.trainer@duckygym.local",
        "0901000003",
        "Fitness",
    ),
]

TEST_ACCOUNTS = [
    (
        "admin",
        "Admin1234",
        "Gym Administrator",
        "admin@duckygym.local",
        "0900000000",
        UserRole.ADMIN,
    ),
    (
        "reception",
        "Reception1234",
        "Reception Staff",
        "reception@duckygym.local",
        "0900000001",
        UserRole.STAFF,
    ),
]

PASSWORD_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Băm một mật khẩu mẫu với một giá trị muối (salt) ngẫu nhiên bằng cách sử dụng thư viện chuẩn của Python."""
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${password_hash.hex()}"


def seed_data() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        for plan_data in PLANS:
            plan = (
                db.query(MembershipPlan)
                .filter_by(plan_name=plan_data["plan_name"])
                .first()
            )
            if plan is None:
                db.add(MembershipPlan(**plan_data))

        for index, (name, gender, birth_date) in enumerate(MEMBERS, start=1):
            email = f"member{index:02d}@duckygym.local"
            phone = f"091{index:07d}"
            member = db.query(Member).filter_by(email=email).first()
            if member is None:
                db.add(
                    Member(
                        full_name=name,
                        gender=gender,
                        date_of_birth=birth_date,
                        phone=phone,
                        qr_code=f"QR-MEMBER-{index:04d}",
                        email=email,
                        address=f"{index} Gym Street, Ho Chi Minh City",
                        join_date=date.today(),
                    )
                )

        for username, full_name, email, phone, specialization in TRAINERS:
            trainer = db.query(User).filter_by(username=username).first()
            if trainer is None:
                db.add(
                    User(
                        username=username,
                        password_hash=hash_password("Trainer1234"),
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        role=UserRole.TRAINER,
                        position="Personal Trainer",
                        hire_date=date.today(),
                        specialization=specialization,
                        experience_years=3,
                        status=UserStatus.ACTIVE,
                    )
                )

        for username, password, full_name, email, phone, role in TEST_ACCOUNTS:
            account = db.query(User).filter_by(username=username).first()
            if account is None:
                db.add(
                    User(
                        username=username,
                        password_hash=hash_password(password),
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        role=role,
                        status=UserStatus.ACTIVE,
                    )
                )

        db.commit()
        print("Seed data created successfully.")
        print("Test accounts: admin / Admin1234, reception / Reception1234")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()