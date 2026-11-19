from datetime import date, datetime, time, timedelta
from decimal import Decimal
from getpass import getpass

from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.init_db import create_tables
from app.core.config import settings
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.equipment import Equipment
from app.models.enums import (
    AssignmentStatus,
    AttendanceStatus,
    BookingStatus,
    FeedbackStatus,
    FeedbackType,
    Gender,
    InvoiceStatus,
    MemberStatus,
    NotificationType,
    PaymentMethod,
    PaymentStatus,
    PlanStatus,
    ScheduleStatus,
    SubscriptionStatus,
    SubscriptionType,
    UserRole,
    UserStatus,
)
from app.models.feedback import Feedback
from app.models.invoice import Invoice
from app.models.member import Member
from app.models.membership_plan import MembershipPlan
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.trainer_member import TrainerMember
from app.models.trainer_schedule import TrainerSchedule
from app.models.training_booking import TrainingBooking
from app.models.user import User

PLANS = (
    {
        "plan_name": "Goi Co Ban 1 Thang",
        "category": "Co ban",
        "duration_days": 30,
        "price": 500_000,
        "description": "Quyen tap gym trong 1 thang.",
    },
    {
        "plan_name": "Goi Tieu Chuan 3 Thang",
        "category": "Tieu chuan",
        "duration_days": 90,
        "price": 1_300_000,
        "description": "Quyen tap gym trong 3 thang.",
    },
    {
        "plan_name": "Goi Nang Cao 6 Thang",
        "category": "Nang cao",
        "duration_days": 180,
        "price": 2_400_000,
        "description": "Quyen tap gym trong 6 thang.",
    },
    {
        "plan_name": "Goi Premium 12 Thang",
        "category": "Premium",
        "duration_days": 365,
        "price": 4_200_000,
        "description": "Quyen tap gym va cac tien ich premium trong 12 thang.",
    },
    {
        "plan_name": "Goi PT 10 Buoi",
        "category": "PT",
        "duration_days": 60,
        "price": 3_000_000,
        "description": "10 buoi tap cung huan luyen vien ca nhan.",
    },
)

EQUIPMENT = (
    ("EQ-001", "May chay bo", "Cardio", "Technogym"),
    ("EQ-002", "Xe dap tap", "Cardio", "Technogym"),
    ("EQ-003", "May elliptical", "Cardio", "Life Fitness"),
    ("EQ-004", "May rowing", "Cardio", "Concept2"),
    ("EQ-005", "Gian ta da nang", "Strength", "Rogue"),
    ("EQ-006", "May day nguc", "Strength", "Life Fitness"),
    ("EQ-007", "May keo xo", "Strength", "Technogym"),
    ("EQ-008", "May leg press", "Strength", "Hammer Strength"),
    ("EQ-009", "Gian ta don", "Free weights", "Rogue"),
    ("EQ-010", "May cap kickback", "Strength", "Technogym"),
)

MEMBER_NAMES = (
    "Nguyen Minh Anh",
    "Tran Hoang Nam",
    "Le Thu Ha",
    "Pham Quoc Bao",
    "Hoang Ngoc Mai",
    "Vo Duc Huy",
    "Dang Thanh Thao",
    "Bui Gia Khanh",
    "Do Phuong Linh",
    "Ngo Tuan Kiet",
    "Duong Bao Chau",
    "Ly Thanh Tung",
    "Truong Khanh Vy",
    "Mai Hoang Long",
    "Cao Ngoc Han",
    "Vu Anh Tuan",
    "Dinh My Duyen",
    "Phan Nhat Minh",
    "Ta Thu Trang",
    "Chau Van Khoa",
)

TRAINERS = (
    ("pt_tuan_anh", "Tuấn Anh", "pt.tuananh@duckygym.local", "0911000001",
     "Strength training", 8),
    ("pt_mai_linh", "Mai Linh", "pt.mailinh@duckygym.local", "0911000002",
     "Yoga and nutrition", 6),
    ("pt_quoc_bao", "Quốc Bảo", "pt.quocbao@duckygym.local", "0911000003",
     "Boxing and conditioning", 7),
)

TEST_ACCOUNTS = (
    {
        "username": "admin",
        "password": "Admin123",
        "full_name": "System Administrator",
        "email": "admin@duckygym.local",
        "phone": "0900000000",
        "role": UserRole.ADMIN,
        "position": "Administrator",
    },
    {
        "username": "le_tan",
        "password": "Receptionist123",
        "full_name": "Nhan vien le tan",
        "email": "receptionist@duckygym.local",
        "phone": "0900000001",
        "role": UserRole.STAFF,
        "position": "Le tan",
    },
)


def seed_data(db: Session) -> dict[str, int]:
    """Insert missing sample records; stable natural keys make reruns idempotent."""
    inserted = {
        "plans": 0,
        "members": 0,
        "equipment": 0,
        "trainers": 0,
        "accounts": 0,
        "subscriptions": 0,
        "invoices": 0,
        "payments": 0,
        "trainer_schedules": 0,
        "trainer_members": 0,
        "training_bookings": 0,
        "attendance_records": 0,
        "feedbacks": 0,
        "notifications": 0,
        "audit_logs": 0,
    }

    for data in PLANS:
        exists = db.scalar(
            select(MembershipPlan.plan_id).where(
                MembershipPlan.plan_name == data["plan_name"]
            )
        )
        if exists is None:
            db.add(MembershipPlan(**data, status=PlanStatus.ACTIVE))
            inserted["plans"] += 1

    for index, full_name in enumerate(MEMBER_NAMES, start=1):
        email = f"member{index:02d}@duckygym.local"
        exists = db.scalar(select(Member.member_id).where(Member.email == email))
        if exists is None:
            db.add(
                Member(
                    full_name=full_name,
                    gender=Gender.OTHER,
                    date_of_birth=date(1985 + (index % 15), (index % 12) + 1, 15),
                    phone=f"093{index:07d}",
                    card_code=f"DG-SEED-{index:04d}",
                    email=email,
                    address=f"So {index} Duong Mau, Ha Noi",
                    join_date=date.today() - timedelta(days=index),
                    status=MemberStatus.ACTIVE,
                )
            )
            inserted["members"] += 1

    for code, name, category, brand in EQUIPMENT:
        exists = db.scalar(
            select(Equipment.equipment_id).where(Equipment.equipment_code == code)
        )
        if exists is None:
            db.add(
                Equipment(
                    equipment_code=code,
                    equipment_name=name,
                    category=category,
                    brand=brand,
                    status="ACTIVE",
                )
            )
            inserted["equipment"] += 1

    for username, full_name, email, phone, specialization, experience in TRAINERS:
        exists = db.scalar(select(User.user_id).where(User.username == username))
        if exists is None:
            db.add(
                User(
                    username=username,
                    password_hash=hash_password("Trainer123"),
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    role=UserRole.TRAINER,
                    status=UserStatus.ACTIVE,
                    position="Personal Trainer",
                    hire_date=date(2020, 1, 1),
                    specialization=specialization,
                    experience_years=experience,
                    bio=f"Huấn luyện viên {specialization}.",
                )
            )
            inserted["trainers"] += 1

    for account in TEST_ACCOUNTS:
        exists = db.scalar(
            select(User.user_id).where(User.username == account["username"])
        )
        if exists is None:
            db.add(
                User(
                    username=account["username"],
                    password_hash=hash_password(account["password"]),
                    full_name=account["full_name"],
                    email=account["email"],
                    phone=account["phone"],
                    role=account["role"],
                    status=UserStatus.ACTIVE,
                    position=account["position"],
                )
            )
            inserted["accounts"] += 1

    db.flush()
    plans_by_name = {
        plan.plan_name: plan for plan in db.scalars(select(MembershipPlan))
    }
    members_by_email = {member.email: member for member in db.scalars(select(Member))}
    users_by_name = {user.username: user for user in db.scalars(select(User))}

    today = date.today()
    subscriptions_by_member: dict[int, Subscription] = {}
    for index in range(1, len(MEMBER_NAMES) + 1):
        member = members_by_email[f"member{index:02d}@duckygym.local"]
        plan_data = PLANS[(index - 1) % len(PLANS)]
        plan = plans_by_name[plan_data["plan_name"]]
        start_date = today - timedelta(days=5)
        subscription = db.scalar(
            select(Subscription).where(
                Subscription.member_id == member.member_id,
                Subscription.plan_id == plan.plan_id,
                Subscription.subscription_type == SubscriptionType.NEW,
            )
        )
        is_unpaid = index % 4 == 0
        if subscription is None:
            subscription = Subscription(
                member_id=member.member_id,
                plan_id=plan.plan_id,
                subscription_type=SubscriptionType.NEW,
                start_date=start_date,
                end_date=start_date + timedelta(days=plan.duration_days),
                status=(
                    SubscriptionStatus.PENDING
                    if is_unpaid
                    else SubscriptionStatus.ACTIVE
                ),
            )
            db.add(subscription)
            inserted["subscriptions"] += 1
        subscriptions_by_member[member.member_id] = subscription
    db.flush()

    invoices_by_member: dict[int, Invoice] = {}
    for index in range(1, len(MEMBER_NAMES) + 1):
        member = members_by_email[f"member{index:02d}@duckygym.local"]
        subscription = subscriptions_by_member[member.member_id]
        plan = plans_by_name[PLANS[(index - 1) % len(PLANS)]["plan_name"]]
        invoice = db.scalar(
            select(Invoice).where(Invoice.subscription_id == subscription.subscription_id)
        )
        if invoice is None:
            amount = Decimal(plan.price)
            invoice = Invoice(
                member_id=member.member_id,
                subscription_id=subscription.subscription_id,
                created_by=users_by_name["admin"].user_id,
                total_amount=amount,
                discount_amount=Decimal("0.00"),
                final_amount=amount,
                status=(
                    InvoiceStatus.UNPAID
                    if index % 4 == 0
                    else InvoiceStatus.PAID
                ),
            )
            db.add(invoice)
            inserted["invoices"] += 1
        invoices_by_member[member.member_id] = invoice
    db.flush()

    receptionist_id = users_by_name["le_tan"].user_id
    for index in range(1, len(MEMBER_NAMES) + 1):
        member = members_by_email[f"member{index:02d}@duckygym.local"]
        invoice = invoices_by_member[member.member_id]
        if invoice.status == InvoiceStatus.UNPAID:
            continue
        transaction_code = f"SEED-PAY-{index:04d}"
        payment_exists = db.scalar(
            select(Payment.payment_id).where(
                Payment.transaction_code == transaction_code
            )
        )
        if payment_exists is None:
            db.add(
                Payment(
                    invoice_id=invoice.invoice_id,
                    received_by=receptionist_id,
                    amount=invoice.final_amount,
                    payment_method=(
                        PaymentMethod.CASH
                        if index % 2
                        else PaymentMethod.BANK_TRANSFER
                    ),
                    payment_date=datetime.combine(today - timedelta(days=4), time(10, 0)),
                    status=PaymentStatus.SUCCESS,
                    transaction_code=transaction_code,
                )
            )
            inserted["payments"] += 1
    db.flush()

    for index, (username, _name, _email, _phone, _specialization, _experience) in enumerate(
        TRAINERS
    ):
        trainer_id = users_by_name[username].user_id
        for day_offset in (1, 2, 3):
            work_date = today + timedelta(days=day_offset)
            start_time = time(8 + index * 3, 0)
            schedule = db.scalar(
                select(TrainerSchedule).where(
                    TrainerSchedule.trainer_id == trainer_id,
                    TrainerSchedule.work_date == work_date,
                    TrainerSchedule.start_time == start_time,
                )
            )
            if schedule is None:
                schedule = TrainerSchedule(
                    trainer_id=trainer_id,
                    work_date=work_date,
                    start_time=start_time,
                    end_time=time(start_time.hour + 1, 0),
                    status=ScheduleStatus.ACTIVE,
                )
                db.add(schedule)
                inserted["trainer_schedules"] += 1
            db.flush()

            member_index = (index * 3 + day_offset - 1) % len(MEMBER_NAMES) + 1
            member = members_by_email[f"member{member_index:02d}@duckygym.local"]
            booking_exists = db.scalar(
                select(TrainingBooking.booking_id).where(
                    TrainingBooking.trainer_id == trainer_id,
                    TrainingBooking.member_id == member.member_id,
                    TrainingBooking.booking_date == work_date,
                    TrainingBooking.start_time == start_time,
                )
            )
            if booking_exists is None:
                db.add(
                    TrainingBooking(
                        member_id=member.member_id,
                        trainer_id=trainer_id,
                        schedule_id=schedule.schedule_id,
                        booking_date=work_date,
                        start_time=start_time,
                        end_time=time(start_time.hour + 1, 0),
                        status=BookingStatus.CONFIRMED,
                    )
                )
                inserted["training_bookings"] += 1

    for index in range(1, len(MEMBER_NAMES) + 1):
        member = members_by_email[f"member{index:02d}@duckygym.local"]
        trainer = TRAINERS[(index - 1) % len(TRAINERS)]
        trainer_id = users_by_name[trainer[0]].user_id
        assignment_exists = db.scalar(
            select(TrainerMember.id).where(
                TrainerMember.trainer_id == trainer_id,
                TrainerMember.member_id == member.member_id,
            )
        )
        if assignment_exists is None:
            db.add(
                TrainerMember(
                    trainer_id=trainer_id,
                    member_id=member.member_id,
                    assigned_by=receptionist_id,
                    start_date=today,
                    status=AssignmentStatus.ACTIVE,
                )
            )
            inserted["trainer_members"] += 1

    db.flush()
    for index in range(1, 13):
        member = members_by_email[f"member{index:02d}@duckygym.local"]
        subscription = subscriptions_by_member[member.member_id]
        if subscription.status != SubscriptionStatus.ACTIVE:
            continue
        check_in = datetime.combine(today, time(6 + index % 10, 0))
        attendance_exists = db.scalar(
            select(AttendanceRecord.attendance_id).where(
                AttendanceRecord.member_id == member.member_id,
                AttendanceRecord.subscription_id == subscription.subscription_id,
                AttendanceRecord.checked_in_by == receptionist_id,
            )
        )
        if attendance_exists is None:
            db.add(
                AttendanceRecord(
                    member_id=member.member_id,
                    subscription_id=subscription.subscription_id,
                    checked_in_by=receptionist_id,
                    check_in=check_in,
                    check_out=check_in + timedelta(minutes=60),
                    status=AttendanceStatus.CHECKED_OUT,
                )
            )
            inserted["attendance_records"] += 1

    feedback_samples = (
        ("Dich vu rat tot", FeedbackType.RATING, 5),
        ("Phong tap sach se", FeedbackType.RATING, 4),
        ("Nhan vien than thien", FeedbackType.RATING, 5),
        ("Can them lop yoga", FeedbackType.COMPLAINT, None),
        ("Thiet bi hien dai", FeedbackType.RATING, 5),
        ("Lich PT linh hoat", FeedbackType.RATING, 4),
        ("Can bo sung khan", FeedbackType.COMPLAINT, None),
        ("Trai nghiem tot", FeedbackType.RATING, 5),
    )
    for index, (title, feedback_type, rating) in enumerate(feedback_samples, start=1):
        member = members_by_email[f"member{index:02d}@duckygym.local"]
        feedback_exists = db.scalar(
            select(Feedback.feedback_id).where(
                Feedback.member_id == member.member_id,
                Feedback.title == title,
            )
        )
        if feedback_exists is None:
            db.add(
                Feedback(
                    member_id=member.member_id,
                    handled_by=receptionist_id,
                    type=feedback_type,
                    rating=rating,
                    title=title,
                    content=f"Phan hoi mau cua hoi vien {member.full_name}.",
                    status=FeedbackStatus.RESOLVED,
                    response="Cam on ban da gui phan hoi.",
                    responded_at=datetime.combine(today, time(9, 0)),
                )
            )
            inserted["feedbacks"] += 1

    notification_users = (
        ("admin", "Thong bao he thong", NotificationType.SYSTEM),
        ("le_tan", "Quy trinh tiep don", NotificationType.SYSTEM),
        ("pt_tuan_anh", "Lich huan luyen", NotificationType.TRAINING_SCHEDULE),
        ("pt_mai_linh", "Lich huan luyen", NotificationType.TRAINING_SCHEDULE),
        ("pt_quoc_bao", "Lich huan luyen", NotificationType.TRAINING_SCHEDULE),
    )
    for username, title, notification_type in notification_users:
        user = users_by_name[username]
        notification_exists = db.scalar(
            select(Notification.notification_id).where(
                Notification.user_id == user.user_id,
                Notification.title == title,
            )
        )
        if notification_exists is None:
            db.add(
                Notification(
                    user_id=user.user_id,
                    title=title,
                    content="Day la thong bao du lieu mau.",
                    type=notification_type,
                    is_read=False,
                )
            )
            inserted["notifications"] += 1

    audit_targets = (
        ("membership_plans", plans_by_name[PLANS[0]["plan_name"]].plan_id),
        ("members", members_by_email["member01@duckygym.local"].member_id),
        (
            "subscriptions",
            subscriptions_by_member[
                members_by_email["member01@duckygym.local"].member_id
            ].subscription_id,
        ),
        (
            "invoices",
            invoices_by_member[
                members_by_email["member01@duckygym.local"].member_id
            ].invoice_id,
        ),
        ("equipment", db.scalar(select(Equipment.equipment_id).order_by(Equipment.equipment_id))),
    )
    for entity_name, entity_id in audit_targets:
        log_exists = db.scalar(
            select(AuditLog.log_id).where(
                AuditLog.user_id == users_by_name["admin"].user_id,
                AuditLog.action == "CREATE",
                AuditLog.entity_name == entity_name,
                AuditLog.entity_id == entity_id,
            )
        )
        if log_exists is None:
            db.add(
                AuditLog(
                    user_id=users_by_name["admin"].user_id,
                    action="CREATE",
                    entity_name=entity_name,
                    entity_id=entity_id,
                    new_value="Sample seed data",
                )
            )
            inserted["audit_logs"] += 1

    db.commit()
    return inserted


def seed(database_url: URL | str | None = None) -> dict[str, int]:
    seed_engine = create_engine(
        database_url or settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    try:
        create_tables(seed_engine)
        with Session(seed_engine) as db:
            return seed_data(db)
    finally:
        seed_engine.dispose()


if __name__ == "__main__":
    database_url = make_url(settings.DATABASE_URL)
    if database_url.drivername.startswith("mysql"):
        password = getpass(
            "MySQL password (press Enter to use DATABASE_URL): "
        )
        if password:
            database_url = database_url.set(password=password)
    counts = seed(database_url)
    print("Seed completed:", ", ".join(f"{key}={value}" for key, value in counts.items()))
