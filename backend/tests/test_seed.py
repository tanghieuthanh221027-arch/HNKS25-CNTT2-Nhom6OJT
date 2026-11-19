from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.base import Base
from app.db.seed import TEST_ACCOUNTS, seed_data
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.equipment import Equipment
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


def test_seed_data_is_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        assert len(Base.metadata.tables) == 14

        first_run = seed_data(db)
        second_run = seed_data(db)

        assert first_run == {
            "plans": 5,
            "members": 20,
            "equipment": 10,
            "trainers": 3,
            "accounts": 2,
            "subscriptions": 20,
            "invoices": 20,
            "payments": 15,
            "trainer_schedules": 9,
            "trainer_members": 20,
            "training_bookings": 9,
            "attendance_records": 9,
            "feedbacks": 8,
            "notifications": 5,
            "audit_logs": 5,
        }
        assert second_run == {
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
        assert db.scalar(select(func.count()).select_from(MembershipPlan)) == 5
        assert db.scalar(select(func.count()).select_from(Member)) == 20
        assert db.scalar(select(func.count()).select_from(Equipment)) == 10
        assert db.scalar(
            select(func.count()).select_from(User).where(User.role == "TRAINER")
        ) == 3
        assert db.scalar(select(func.count()).select_from(User)) == 5
        assert db.scalar(select(func.count()).select_from(Subscription)) == 20
        assert db.scalar(select(func.count()).select_from(Invoice)) == 20
        assert db.scalar(select(func.count()).select_from(Payment)) == 15
        assert db.scalar(select(func.count()).select_from(TrainerSchedule)) == 9
        assert db.scalar(select(func.count()).select_from(TrainerMember)) == 20
        assert db.scalar(select(func.count()).select_from(TrainingBooking)) == 9
        assert db.scalar(select(func.count()).select_from(AttendanceRecord)) == 9
        assert db.scalar(select(func.count()).select_from(Feedback)) == 8
        assert db.scalar(select(func.count()).select_from(Notification)) == 5
        assert db.scalar(select(func.count()).select_from(AuditLog)) == 5

        admin = db.scalar(select(User).where(User.username == "admin"))
        receptionist = db.scalar(select(User).where(User.username == "le_tan"))
        assert admin is not None
        assert receptionist is not None
        assert verify_password(TEST_ACCOUNTS[0]["password"], admin.password_hash)
        assert verify_password(
            TEST_ACCOUNTS[1]["password"], receptionist.password_hash
        )

    Base.metadata.drop_all(engine)
    engine.dispose()
