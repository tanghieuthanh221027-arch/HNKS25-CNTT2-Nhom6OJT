import sys
import unittest
from datetime import date, time, timedelta
from pathlib import Path

# Thêm đường dẫn backend vào sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.exception import ConflictException, ForbiddenException, NotFoundException
from app.core.security import hash_password
from app.db.base import Base
from app.models.enums import BookingStatus, Gender, MemberStatus, UserRole, UserStatus
from app.models.member import Member
from app.models.user import User
from app.routers.pt_schedule import (
    cancel_schedule,
    complete_schedule,
    confirm_schedule,
    create_schedule,
    delete_schedule,
    get_schedule_detail,
    get_schedules,
    update_schedule,
)
from app.schemas.pt_schedule import (
    PTScheduleCancelRequest,
    PTScheduleCreate,
    PTScheduleUpdate,
)

# Sử dụng SQLite in-memory cho testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestPTSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = TestingSessionLocal()

        # Tạo PT 1
        cls.trainer1 = User(
            username="pt_john",
            email="pt_john@gym.com",
            phone="0901000001",
            full_name="John Trainer",
            password_hash=hash_password("Pass123!"),
            role=UserRole.TRAINER,
            status=UserStatus.ACTIVE,
        )
        # Tạo PT 2
        cls.trainer2 = User(
            username="pt_mike",
            email="pt_mike@gym.com",
            phone="0901000002",
            full_name="Mike Trainer",
            password_hash=hash_password("Pass123!"),
            role=UserRole.TRAINER,
            status=UserStatus.ACTIVE,
        )
        # Tạo Member 1
        cls.member1_user = User(
            username="member_alice",
            email="alice@gmail.com",
            phone="0902000001",
            full_name="Alice Member",
            password_hash=hash_password("Pass123!"),
            role=UserRole.MEMBER,
            status=UserStatus.ACTIVE,
        )
        # Tạo Member 2
        cls.member2_user = User(
            username="member_bob",
            email="bob@gmail.com",
            phone="0902000002",
            full_name="Bob Member",
            password_hash=hash_password("Pass123!"),
            role=UserRole.MEMBER,
            status=UserStatus.ACTIVE,
        )

        cls.db.add_all([cls.trainer1, cls.trainer2, cls.member1_user, cls.member2_user])
        cls.db.commit()

        # Tạo Member profile
        cls.member1 = Member(
            user_id=cls.member1_user.user_id,
            full_name="Alice Member",
            gender=Gender.FEMALE,
            date_of_birth=date(1995, 5, 20),
            phone=cls.member1_user.phone,
            email=cls.member1_user.email,
            address="123 Gym St",
            status=MemberStatus.ACTIVE,
        )
        cls.member2 = Member(
            user_id=cls.member2_user.user_id,
            full_name="Bob Member",
            gender=Gender.MALE,
            date_of_birth=date(1992, 8, 15),
            phone=cls.member2_user.phone,
            email=cls.member2_user.email,
            address="456 Fitness Ave",
            status=MemberStatus.ACTIVE,
        )
        cls.db.add_all([cls.member1, cls.member2])
        cls.db.commit()

        # Refresh objects
        cls.db.refresh(cls.trainer1)
        cls.db.refresh(cls.trainer2)
        cls.db.refresh(cls.member1_user)
        cls.db.refresh(cls.member2_user)
        cls.db.refresh(cls.member1)
        cls.db.refresh(cls.member2)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_01_member_books_pt_schedule(self):
        """Hội viên đặt ca tập với PT thành công (status = PENDING)"""
        tomorrow = date.today() + timedelta(days=1)
        data = PTScheduleCreate(
            trainer_id=self.trainer1.user_id,
            booking_date=tomorrow,
            start_time=time(8, 0),
            end_time=time(9, 0),
        )
        res = create_schedule(data=data, db=self.db, current_user=self.member1_user)
        self.assertEqual(res.trainer_id, self.trainer1.user_id)
        self.assertEqual(res.member_id, self.member1.member_id)
        self.assertEqual(res.status, BookingStatus.PENDING)
        self.assertEqual(res.start_time, time(8, 0))
        self.assertEqual(res.end_time, time(9, 0))
        self.assertEqual(res.trainer_name, "John Trainer")
        self.assertEqual(res.member_name, "Alice Member")

    def test_02_prevent_trainer_overlap(self):
        """Chặn trùng giờ của PT: không thể đặt ca giao thoa với ca đã có của PT"""
        tomorrow = date.today() + timedelta(days=1)
        # Ca giao thoa 08:30 - 09:30 (trùng với 08:00 - 09:00 của PT 1)
        data = PTScheduleCreate(
            trainer_id=self.trainer1.user_id,
            booking_date=tomorrow,
            start_time=time(8, 30),
            end_time=time(9, 30),
        )
        with self.assertRaises(ConflictException) as cm:
            create_schedule(data=data, db=self.db, current_user=self.member2_user)
        self.assertIn("Huấn luyện viên đã có ca tập trùng khung giờ", cm.exception.message)

    def test_03_prevent_member_overlap(self):
        """Chặn trùng giờ của Hội viên: Member 1 đã có ca 08:00-09:00 không thể đặt ca trùng với PT khác"""
        tomorrow = date.today() + timedelta(days=1)
        # Member 1 cố đặt với PT 2 từ 08:15 đến 09:15
        data = PTScheduleCreate(
            trainer_id=self.trainer2.user_id,
            booking_date=tomorrow,
            start_time=time(8, 15),
            end_time=time(9, 15),
        )
        with self.assertRaises(ConflictException) as cm:
            create_schedule(data=data, db=self.db, current_user=self.member1_user)
        self.assertIn("Hội viên đã có ca tập trùng khung giờ", cm.exception.message)

    def test_04_adjacent_time_allowed(self):
        """Khung giờ liền kề (09:00 - 10:00) không trùng và được phép đặt"""
        tomorrow = date.today() + timedelta(days=1)
        data = PTScheduleCreate(
            trainer_id=self.trainer1.user_id,
            booking_date=tomorrow,
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        res = create_schedule(data=data, db=self.db, current_user=self.member2_user)
        self.assertEqual(res.status, BookingStatus.PENDING)

    def test_05_pt_confirm_and_permission(self):
        """PT xác nhận ca tập; kiểm tra hội viên hoặc PT khác không có quyền xác nhận"""
        # Lấy ca của PT 1
        schedules = get_schedules(
            trainer_id=self.trainer1.user_id,
            db=self.db,
            current_user=self.trainer1,
        )
        self.assertTrue(len(schedules) >= 1)
        booking_id = schedules[0].booking_id

        # Hội viên cố xác nhận -> 403 Forbidden
        with self.assertRaises(ForbiddenException):
            confirm_schedule(booking_id=booking_id, db=self.db, current_user=self.member1_user)

        # PT khác cố xác nhận ca không phải của mình -> 403 Forbidden
        with self.assertRaises(ForbiddenException):
            confirm_schedule(booking_id=booking_id, db=self.db, current_user=self.trainer2)

        # Đúng PT xác nhận -> thành công, chuyển sang CONFIRMED
        res = confirm_schedule(booking_id=booking_id, db=self.db, current_user=self.trainer1)
        self.assertEqual(res.status, BookingStatus.CONFIRMED)

    def test_06_complete_schedule(self):
        """Đánh dấu hoàn thành ca tập (CONFIRMED -> COMPLETED)"""
        schedules = get_schedules(
            trainer_id=self.trainer1.user_id,
            booking_status=BookingStatus.CONFIRMED,
            db=self.db,
            current_user=self.trainer1,
        )
        self.assertTrue(len(schedules) >= 1)
        booking_id = schedules[0].booking_id

        # Hội viên cố đánh dấu hoàn thành -> 403 Forbidden
        with self.assertRaises(ForbiddenException):
            complete_schedule(booking_id=booking_id, db=self.db, current_user=self.member1_user)

        # PT đánh dấu hoàn thành -> thành công
        res = complete_schedule(booking_id=booking_id, db=self.db, current_user=self.trainer1)
        self.assertEqual(res.status, BookingStatus.COMPLETED)

    def test_07_cancel_schedule_and_frees_slot(self):
        """PT hoặc Hội viên huỷ ca tập (PENDING/CONFIRMED -> CANCELLED); slot sau đó được giải phóng"""
        target_date = date.today() + timedelta(days=2)
        # Đặt ca mới với PT 2
        data = PTScheduleCreate(
            trainer_id=self.trainer2.user_id,
            booking_date=target_date,
            start_time=time(14, 0),
            end_time=time(15, 0),
        )
        res_book = create_schedule(data=data, db=self.db, current_user=self.member1_user)
        booking_id = res_book.booking_id
        self.assertEqual(res_book.status, BookingStatus.PENDING)

        # Hội viên huỷ ca tập
        cancel_req = PTScheduleCancelRequest(reason="Bận việc gia đình")
        res_cancel = cancel_schedule(
            booking_id=booking_id,
            cancel_in=cancel_req,
            db=self.db,
            current_user=self.member1_user,
        )
        self.assertEqual(res_cancel.status, BookingStatus.CANCELLED)

        # Sau khi ca đã huỷ, khung giờ 14:00 - 15:00 ngày hôm đó có thể đặt lại mà không bị báo trùng
        data_rebook = PTScheduleCreate(
            trainer_id=self.trainer2.user_id,
            booking_date=target_date,
            start_time=time(14, 0),
            end_time=time(15, 0),
        )
        res_rebook = create_schedule(data=data_rebook, db=self.db, current_user=self.member2_user)
        self.assertEqual(res_rebook.status, BookingStatus.PENDING)

    def test_08_list_schedules_by_pt_and_by_week(self):
        """Danh sách ca theo PT và theo tuần (ISO week)"""
        today = date.today()
        cal = today.isocalendar()
        current_year = cal[0]
        current_week = cal[1]

        res = get_schedules(
            trainer_id=self.trainer1.user_id,
            week=current_week,
            year=current_year,
            db=self.db,
            current_user=self.trainer1,
        )
        self.assertIsInstance(res, list)

    def test_09_list_schedules_by_date_range(self):
        """Danh sách ca theo khoảng ngày (start_date, end_date)"""
        start = date.today()
        end = date.today() + timedelta(days=7)

        res = get_schedules(
            trainer_id=self.trainer1.user_id,
            start_date=start,
            end_date=end,
            db=self.db,
            current_user=self.trainer1,
        )
        self.assertIsInstance(res, list)

    def test_10_crud_get_detail_update_and_delete(self):
        """Xem chi tiết, cập nhật thời gian và xoá ca tập (CRUD)"""
        target_date = date.today() + timedelta(days=3)
        res_create = create_schedule(
            data=PTScheduleCreate(
                trainer_id=self.trainer1.user_id,
                booking_date=target_date,
                start_time=time(16, 0),
                end_time=time(17, 0),
            ),
            db=self.db,
            current_user=self.member1_user,
        )
        booking_id = res_create.booking_id

        # GET detail
        detail = get_schedule_detail(booking_id=booking_id, db=self.db, _current_user=self.trainer1)
        self.assertEqual(detail.booking_id, booking_id)

        # UPDATE thời gian
        res_update = update_schedule(
            booking_id=booking_id,
            data=PTScheduleUpdate(start_time=time(16, 30), end_time=time(17, 30)),
            db=self.db,
            current_user=self.trainer1,
        )
        self.assertEqual(res_update.start_time, time(16, 30))
        self.assertEqual(res_update.end_time, time(17, 30))

        # DELETE
        delete_schedule(booking_id=booking_id, db=self.db, current_user=self.trainer1)

        # Sau khi xoá, lấy lại trả về NotFoundException (404)
        with self.assertRaises(NotFoundException):
            get_schedule_detail(booking_id=booking_id, db=self.db, _current_user=self.trainer1)


if __name__ == "__main__":
    unittest.main()
