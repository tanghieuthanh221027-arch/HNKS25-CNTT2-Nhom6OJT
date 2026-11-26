from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.core.qr_utils import generate_card_code, generate_qr_base64
from app.core.security import hash_password
from app.core.timezone_utils import now_vn, today_vn
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.db.schema_upgrade import upgrade_mysql_schema
from app.models.attendance_record import AttendanceRecord
from app.models.body_metric import BodyMetric
from app.models.discount import Discount
from app.models.enums import (
    AttendanceStatus,
    BookingStatus,
    Gender,
    InvoiceStatus,
    MemberStatus,
    PaymentMethod,
    PaymentStatus,
    PlanStatus,
    ScheduleStatus,
    SubscriptionStatus,
    SubscriptionType,
    UserRole,
    UserStatus,
)
from app.models.equipment import Equipment
from app.models.group_class import GroupClass, GroupClassEnrollment
from app.models.invoice import Invoice
from app.models.member import Member
from app.models.member_card import MemberCard
from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.trainer_schedule import TrainerSchedule
from app.models.training_booking import TrainingBooking
from app.models.user import User


def ensure_sql_views(db: Session) -> None:
    """Tạo các SQL Views thống kê doanh thu, top gói tập và hội viên mới (Task T067D16)."""
    views = [
        """
        CREATE OR REPLACE VIEW vw_daily_revenue AS
        SELECT
            DATE(i.created_at) AS revenue_date,
            COUNT(i.invoice_id) AS invoice_count,
            COALESCE(SUM(i.total_amount), 0) AS gross_revenue,
            COALESCE(SUM(i.discount_amount), 0) AS total_discount,
            COALESCE(SUM(i.final_amount), 0) AS net_revenue
        FROM invoices i
        WHERE i.status = 'PAID'
        GROUP BY DATE(i.created_at)
        """,
        """
        CREATE OR REPLACE VIEW vw_monthly_revenue AS
        SELECT
            DATE_FORMAT(i.created_at, '%Y-%m') AS revenue_month,
            COUNT(i.invoice_id) AS invoice_count,
            COALESCE(SUM(i.total_amount), 0) AS gross_revenue,
            COALESCE(SUM(i.discount_amount), 0) AS total_discount,
            COALESCE(SUM(i.final_amount), 0) AS net_revenue
        FROM invoices i
        WHERE i.status = 'PAID'
        GROUP BY DATE_FORMAT(i.created_at, '%Y-%m')
        """,
        """
        CREATE OR REPLACE VIEW vw_top_gym_plans AS
        SELECT
            mp.plan_id,
            mp.plan_name,
            mp.category,
            mp.duration_days,
            mp.price,
            (
                SELECT COUNT(*)
                FROM subscriptions s
                WHERE s.plan_id = mp.plan_id
            ) AS total_subscriptions,
            (
                SELECT COUNT(*)
                FROM subscriptions s
                WHERE s.plan_id = mp.plan_id
                  AND s.status = 'ACTIVE'
            ) AS active_subscriptions,
            COALESCE((
                SELECT SUM(i.final_amount)
                FROM subscriptions s
                INNER JOIN invoices i ON i.subscription_id = s.subscription_id
                WHERE s.plan_id = mp.plan_id
                  AND i.status = 'PAID'
            ), 0) AS total_revenue
        FROM membership_plans mp
        """,
        """
        CREATE OR REPLACE VIEW vw_monthly_new_members AS
        SELECT
            DATE_FORMAT(m.join_date, '%Y-%m') AS join_month,
            COUNT(m.member_id) AS new_members_count
        FROM members m
        GROUP BY DATE_FORMAT(m.join_date, '%Y-%m')
        """,
    ]
    for view_sql in views:
        try:
            db.execute(text(view_sql))
            db.commit()
        except Exception:
            db.rollback()


def _upsert_user(
    db: Session,
    username: str,
    email: str,
    phone: str,
    full_name: str,
    password_hash: str,
    role: UserRole,
    **extra_fields,
) -> User:
    """Tìm hoặc tạo mới User an toàn (không bị lỗi trùng username/email/phone)."""
    user = (
        db.query(User)
        .filter(
            or_(
                User.username == username,
                User.email == email,
                User.phone == phone,
            )
        )
        .first()
    )
    if not user:
        user = User(
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            status=UserStatus.ACTIVE,
            **extra_fields,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Đảm bảo mật khẩu và trạng thái khớp với tài khoản seed để đăng nhập được ngay
        user.password_hash = password_hash
        user.status = UserStatus.ACTIVE
        if user.username == "admin" and user.email == "admin@duckygym.local":
            user.email = "admin@duckygym.vn"
        db.commit()
        db.refresh(user)
    return user


def seed_all(db: Session) -> dict[str, int]:
    """
    Seed dữ liệu mẫu chuẩn Idempotent (Task T067CD7):
    - 2 tài khoản quản trị & lễ tân (admin, lễ tân)
    - 3 PT (Huấn luyện viên cá nhân)
    - 5 Gói tập (Gym Plans)
    - 20 Hội viên (Members + MemberCards + Subscriptions + Invoices + Check-ins)
    - 10 Thiết bị phòng gym (Equipment + lịch bảo trì)
    - 4 Mã giảm giá (Discounts)
    - 4 Lớp tập nhóm (Group Classes)
    """
    Base.metadata.create_all(bind=engine)
    upgrade_mysql_schema(db)
    ensure_sql_views(db)

    today = today_vn()
    default_pw = hash_password("Admin123")
    staff_pw = hash_password("Staff123")
    pt_pw = hash_password("Trainer123")
    member_pw = hash_password("Member123")

    # 1. Seed Admin & Lễ tân (STAFF)
    admin_user = _upsert_user(
        db,
        username="admin",
        email="admin@duckygym.vn",
        phone="0900000000",
        full_name="Quản trị viên DuckyGym",
        password_hash=default_pw,
        role=UserRole.ADMIN,
        position="Quản lý hệ thống",
        hire_date=today - timedelta(days=365),
        salary=Decimal("25000000.00"),
    )

    staff_user = _upsert_user(
        db,
        username="letan",
        email="staff@duckygym.vn",
        phone="0900000001",
        full_name="Nguyễn Thu Hà (Lễ tân)",
        password_hash=staff_pw,
        role=UserRole.STAFF,
        position="Lễ tân & Thu ngân POS",
        hire_date=today - timedelta(days=200),
        salary=Decimal("10500000.00"),
    )

    # 2. Seed 3 PT (Huấn luyện viên)
    pt_specs = [
        (
            "pt_tuananh",
            "Trần Tuấn Anh",
            "pt@duckygym.vn",
            "0902000001",
            "Master Trainer · Thể hình & Tăng cơ",
            8,
            "Chứng chỉ NASM CPT quốc tế, 8 năm kinh nghiệm huấn luyện thể hình chuyên nghiệp.",
        ),
        (
            "pt_mailinh",
            "Nguyễn Mai Linh",
            "mailinh.pt@duckygym.vn",
            "0902000002",
            "Chuyên gia Dinh dưỡng, Yoga & Pilates",
            6,
            "Chuyên gia giảm mỡ, phục hồi tư thế và thiết kế thực đơn dinh dưỡng cá nhân hóa.",
        ),
        (
            "pt_quocbao",
            "Lê Quốc Bảo",
            "quocbao.pt@duckygym.vn",
            "0902000003",
            "Boxing, HIIT & Conditioning",
            7,
            "Cựu VĐV Boxing quốc gia, chuyên huấn luyện sức bền tim mạch và đốt mỡ cường độ cao.",
        ),
    ]
    pt_users: list[User] = []
    for uname, fname, email, phone, spec, exp, bio in pt_specs:
        pt = _upsert_user(
            db,
            username=uname,
            email=email,
            phone=phone,
            full_name=fname,
            password_hash=pt_pw,
            role=UserRole.TRAINER,
            position="Personal Trainer",
            hire_date=today - timedelta(days=180),
            salary=Decimal("16000000.00"),
            specialization=spec,
            experience_years=exp,
            bio=bio,
        )
        pt_users.append(pt)

    # 3. Seed 5 Gói tập (Gym Plans - kèm định mức số buổi PT)
    plan_specs = [
        (
            "Starter 1 Tháng",
            "Gói Cơ Bản",
            30,
            3,
            Decimal("499000.00"),
            "Tập luyện không giới hạn khung giờ, tủ đồ cá nhân, tặng 3 buổi PT định hướng.",
        ),
        (
            "Pro Fitness 3 Tháng",
            "Gói Tiêu Chuẩn",
            90,
            5,
            Decimal("1290000.00"),
            "Full quyền lợi khu Cardio & Free Weights, đo InBody định kỳ hàng tháng.",
        ),
        (
            "Pro Fitness 6 Tháng",
            "Gói Phổ Biến",
            180,
            7,
            Decimal("2394000.00"),
            "Tặng 7 ngày PT hướng dẫn, tham gia lớp Yoga & HIIT mỗi tuần, sử dụng khu Sauna đá muối.",
        ),
        (
            "VIP Elite 12 Tháng",
            "Gói Cao Cấp",
            365,
            12,
            Decimal("3840000.00"),
            "Toàn bộ quyền lợi Pro, dẫn theo 1 bạn tập miễn phí cuối tuần, khăn tập & nước uống miễn phí.",
        ),
        (
            "Coaching PT 1-1 (10 Buổi)",
            "Gói Huấn Luyện Viên",
            60,
            10,
            Decimal("4500000.00"),
            "10 buổi tập 1-1 độc quyền cùng Master Trainer, giáo án và thực đơn thiết kế riêng.",
        ),
    ]
    plans: list[MembershipPlan] = []
    for pname, cat, days, pt_sess, price, desc in plan_specs:
        plan = db.query(MembershipPlan).filter(MembershipPlan.plan_name == pname).first()
        if not plan:
            plan = MembershipPlan(
                plan_name=pname,
                category=cat,
                duration_days=days,
                pt_sessions=pt_sess,
                price=price,
                description=desc,
                status=PlanStatus.ACTIVE,
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)
        elif plan.pt_sessions == 0:
            plan.pt_sessions = pt_sess
            db.commit()
            db.refresh(plan)
        plans.append(plan)

    if not plans:
        plans = db.query(MembershipPlan).all()

    # 4. Seed 10 Thiết bị phòng gym
    equipment_specs = [
        ("Máy chạy bộ Technogym Artis Run #01", "Khu Cardio", "HOAT_DONG", 30, 5),
        ("Máy chạy bộ Technogym Artis Run #02", "Khu Cardio", "HOAT_DONG", 30, 18),
        ("Xe đạp tập Assault AirBike Pro", "Khu Cardio", "BAO_TRI", 15, -1),
        ("Giàn tạ đa năng Rogue Monster Rack", "Khu Free Weights", "HOAT_DONG", 45, 22),
        ("Ghế đẩy ngực Olympic Bench Press", "Khu Free Weights", "HOAT_DONG", 30, 4),
        ("Máy ép ngực Seated Chest Press Matrix", "Khu Máy Khối", "HOAT_DONG", 30, 12),
        ("Máy kéo xô Lat Pulldown Technogym", "Khu Máy Khối", "HOAT_DONG", 30, 3),
        ("Máy đạp đùi Leg Press 45 Độ", "Khu Chân & Mông", "HONG", 20, -2),
        ("Khung kéo cáp đôi Functional Trainer", "Khu Functional", "HOAT_DONG", 30, 25),
        ("Phòng xông hơi đá muối Himalaya", "Khu Recovery & Spa", "HOAT_DONG", 14, 6),
    ]
    for eq_name, zone, st, interval, due_offset in equipment_specs:
        eq = db.query(Equipment).filter(Equipment.name == eq_name).first()
        if not eq:
            next_due = today + timedelta(days=due_offset)
            last_maint = next_due - timedelta(days=interval)
            eq = Equipment(
                name=eq_name,
                zone=zone,
                status=st,
                purchase_date=today - timedelta(days=300),
                last_maintained_at=last_maint,
                maintenance_interval_days=interval,
                next_maintenance_date=next_due,
                notes="Thiết bị chính hãng nhập khẩu, kiểm tra định kỳ theo tiêu chuẩn an toàn.",
            )
            db.add(eq)
    db.commit()

    # 5. Seed Mã giảm giá (Discounts)
    discount_specs = [
        ("WELCOME20", "Giảm 20% cho hội viên đăng ký mới", "PERCENT", Decimal("20.00"), Decimal("400000.00"), Decimal("500000.00"), today + timedelta(days=90), 100),
        ("SUMMER100K", "Giảm trực tiếp 100.000đ cho mọi gói tập", "FIXED", Decimal("100000.00"), Decimal("499000.00"), None, today + timedelta(days=60), 50),
        ("DUCKYVIP", "Giảm 15% gói VIP 6-12 tháng", "PERCENT", Decimal("15.00"), Decimal("2000000.00"), Decimal("800000.00"), today + timedelta(days=120), 30),
        ("EXPIRED10", "Voucher hết hạn dùng để test validate", "PERCENT", Decimal("10.00"), Decimal("0.00"), None, today - timedelta(days=5), 10),
    ]
    for code, desc, dtype, dval, min_ord, max_disc, exp_date, limit in discount_specs:
        disc = db.query(Discount).filter(Discount.code == code).first()
        if not disc:
            disc = Discount(
                code=code,
                description=desc,
                discount_type=dtype,
                discount_value=dval,
                min_order_amount=min_ord,
                max_discount_amount=max_disc,
                start_date=today - timedelta(days=30),
                expiry_date=exp_date,
                usage_limit=limit,
                used_count=2 if code == "WELCOME20" else 0,
                is_active=exp_date >= today,
            )
            db.add(disc)
    db.commit()

    # 6. Seed 20 Hội viên
    member_names = [
        "Nguyễn Văn Hoàng",
        "Trần Thị Minh Thư",
        "Lê Hoàng Nam",
        "Phạm Quỳnh Anh",
        "Vũ Minh Tuấn",
        "Đặng Thu Trang",
        "Bùi Đức Duy",
        "Đỗ Ngọc Ánh",
        "Hoàng Gia Bảo",
        "Ngô Phương Linh",
        "Dương Thanh Tùng",
        "Lý Khánh Huyền",
        "Trương Quốc Khánh",
        "Phan Bảo Ngọc",
        "Võ Nhật Minh",
        "Đinh Thảo Nguyên",
        "Hồ Anh Dũng",
        "Mai Thanh Hà",
        "Lương Tuấn Kiệt",
        "Chu Diệu Linh",
    ]

    for idx, full_name in enumerate(member_names, start=1):
        try:
            uname = "hoivien" if idx == 1 else f"member{idx:02d}"
            email = "member@duckygym.vn" if idx == 1 else f"member{idx:02d}@duckygym.vn"
            phone = f"09010000{idx:02d}"
            gender = Gender.MALE if idx % 2 == 1 else Gender.FEMALE

            u = _upsert_user(
                db,
                username=uname,
                email=email,
                phone=phone,
                full_name=full_name,
                password_hash=member_pw,
                role=UserRole.MEMBER,
            )

            m = db.query(Member).filter(Member.user_id == u.user_id).first()
            if not m:
                join_offset = (idx * 7) % 120
                m = Member(
                    user_id=u.user_id,
                    gender=gender,
                    date_of_birth=date(1995 + (idx % 10), (idx % 12) + 1, (idx % 25) + 1),
                    address=f"Số {idx * 12} Nguyễn Trãi, Hà Đông, Hà Nội",
                    join_date=today - timedelta(days=join_offset),
                    status=MemberStatus.ACTIVE,
                )
                db.add(m)
                db.commit()
                db.refresh(m)

            card = db.query(MemberCard).filter(MemberCard.user_id == u.user_id).first()
            if not card:
                c_code = f"DG-{u.user_id:06d}" if idx <= 5 else generate_card_code(u.user_id, deterministic_for_seed=True)
                if db.query(MemberCard).filter(MemberCard.card_code == c_code).first():
                    c_code = generate_card_code(u.user_id, deterministic_for_seed=False)
                height = Decimal("172.0") if gender == Gender.MALE else Decimal("160.0")
                weight = Decimal(str(65 + (idx % 12))) if gender == Gender.MALE else Decimal(str(50 + (idx % 8)))
                bmi = round(weight / ((height / Decimal("100")) ** 2), 1)
                card = MemberCard(
                    user_id=u.user_id,
                    member_id=m.member_id,
                    card_code=c_code,
                    qr_base64=generate_qr_base64(c_code),
                    height_cm=height,
                    weight_kg=weight,
                    bmi=bmi,
                    target_weight_kg=weight - Decimal("2.0"),
                    weekly_workouts=4,
                    emergency_contact=f"Người thân ({u.phone[:-2]}99)",
                    streak_days=5 if idx == 1 else (idx % 12),
                    total_checkins=32 if idx == 1 else (idx * 3),
                )
                db.add(card)
                db.commit()
                db.refresh(card)

            existing_sub = db.query(Subscription).filter(Subscription.member_id == m.member_id).first()
            if not existing_sub and plans:
                chosen_plan = plans[(idx - 1) % len(plans)]
                if idx in (4, 9, 15):
                    start_dt = today - timedelta(days=chosen_plan.duration_days - 2)
                    end_dt = today + timedelta(days=2)
                    sub_status = SubscriptionStatus.ACTIVE
                elif idx in (18, 20):
                    start_dt = today - timedelta(days=chosen_plan.duration_days + 10)
                    end_dt = today - timedelta(days=10)
                    sub_status = SubscriptionStatus.EXPIRED
                else:
                    start_dt = today - timedelta(days=(idx * 3) % 25)
                    end_dt = start_dt + timedelta(days=chosen_plan.duration_days)
                    sub_status = SubscriptionStatus.ACTIVE

                sub_type = SubscriptionType.RENEW if idx % 3 == 0 else SubscriptionType.NEW
                sub = Subscription(
                    member_id=m.member_id,
                    plan_id=chosen_plan.plan_id,
                    subscription_type=sub_type,
                    start_date=start_dt,
                    end_date=end_dt,
                    total_sessions=chosen_plan.pt_sessions,
                    sessions_remaining=chosen_plan.pt_sessions,
                    status=sub_status,
                )
                db.add(sub)
                db.flush()

                inv = Invoice(
                    member_id=m.member_id,
                    subscription_id=sub.subscription_id,
                    created_by=staff_user.user_id,
                    total_amount=chosen_plan.price,
                    discount_amount=Decimal("0.00"),
                    final_amount=chosen_plan.price,
                    status=InvoiceStatus.PAID,
                )
                inv_dt = datetime.now() - timedelta(days=(idx * 8) % 95)
                inv.created_at = inv_dt
                inv.updated_at = inv_dt
                db.add(inv)
                db.flush()

                pay = Payment(
                    invoice_id=inv.invoice_id,
                    received_by=staff_user.user_id,
                    amount=chosen_plan.price,
                    payment_method=PaymentMethod.BANK_TRANSFER if idx % 2 == 0 else PaymentMethod.CASH,
                    payment_date=inv_dt,
                    status=PaymentStatus.SUCCESS,
                    transaction_code=f"TXN-DG-{inv.invoice_id:06d}-{idx}",
                )
                db.add(pay)

                if idx <= 6 and sub_status == SubscriptionStatus.ACTIVE:
                    for d_back in range(4, -1, -1):
                        ci_time = datetime.now() - timedelta(days=d_back, hours=2)
                        co_time = None if (idx in (1, 2) and d_back == 0) else (ci_time + timedelta(minutes=75))
                        att = AttendanceRecord(
                            member_id=m.member_id,
                            subscription_id=sub.subscription_id,
                            checked_in_by=staff_user.user_id,
                            check_in=ci_time,
                            check_out=co_time,
                            status=AttendanceStatus.CHECKED_IN if co_time is None else AttendanceStatus.CHECKED_OUT,
                        )
                        db.add(att)

                if idx == 1:
                    for w_idx, w_val in enumerate([68.5, 67.8, 67.1, 66.5, 66.0]):
                        rec_date = today - timedelta(days=(4 - w_idx) * 7)
                        h_cm = Decimal("172.0")
                        w_kg = Decimal(str(w_val))
                        bmi_val = round(w_kg / ((h_cm / Decimal("100")) ** 2), 1)
                        bm = BodyMetric(
                            user_id=u.user_id,
                            recorded_date=rec_date,
                            height_cm=h_cm,
                            weight_kg=w_kg,
                            bmi=bmi_val,
                            body_fat_pct=Decimal(str(18.5 - w_idx * 0.4)),
                            muscle_mass_kg=Decimal(str(31.0 + w_idx * 0.3)),
                            waist_cm=Decimal(str(79.0 - w_idx * 0.5)),
                            notes=f"Đo InBody tuần {w_idx + 1}",
                        )
                        db.add(bm)

                db.commit()
        except Exception:
            db.rollback()

    # 7. Seed Lịch ca trực mở của PT (TrainerSchedule) trước 60 ngày & Booking mẫu (Mục 5.3)
    try:
        monday = today - timedelta(days=today.weekday())
        first_member = db.query(Member).order_by(Member.member_id.asc()).first()
        first_sub = (
            db.query(Subscription)
            .filter(
                Subscription.member_id == first_member.member_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .order_by(Subscription.end_date.desc())
            .first()
            if first_member
            else None
        )
        existing_keys = {
            (r.trainer_id, r.work_date, r.start_time)
            for r in db.query(
                TrainerSchedule.trainer_id,
                TrainerSchedule.work_date,
                TrainerSchedule.start_time,
            )
            .filter(TrainerSchedule.work_date >= monday)
            .all()
        }
        new_schedules: list[TrainerSchedule] = []
        standard_hours = (7, 8, 9, 10, 14, 15, 16, 17, 18, 19, 20)
        for pt in pt_users:
            for day_offset in range(0, 62):
                w_date = monday + timedelta(days=day_offset)
                for hour in standard_hours:
                    st_time = time(hour, 0)
                    if (pt.user_id, w_date, st_time) in existing_keys:
                        continue
                    en_time = time(hour + 1, 0)
                    new_schedules.append(
                        TrainerSchedule(
                            trainer_id=pt.user_id,
                            work_date=w_date,
                            start_time=st_time,
                            end_time=en_time,
                            start_at=datetime.combine(w_date, st_time),
                            end_at=datetime.combine(w_date, en_time),
                            status=ScheduleStatus.ACTIVE,
                        )
                    )
        if new_schedules:
            db.add_all(new_schedules)
            db.flush()

        # Tạo 1 booking mẫu trong tương lai gần cho first_member nếu chưa có booking nào trong tuần
        if first_member and first_sub and pt_users:
            sample_day = today + timedelta(days=2)
            sample_st = time(18, 0)
            sample_en = time(19, 0)
            has_bk = (
                db.query(TrainingBooking)
                .filter(
                    TrainingBooking.member_id == first_member.member_id,
                    TrainingBooking.booking_date >= monday,
                )
                .first()
            )
            sample_sched = (
                db.query(TrainerSchedule)
                .filter(
                    TrainerSchedule.trainer_id == pt_users[0].user_id,
                    TrainerSchedule.work_date == sample_day,
                    TrainerSchedule.start_time == sample_st,
                )
                .first()
            )
            if not has_bk and sample_sched:
                bk = TrainingBooking(
                    member_id=first_member.member_id,
                    trainer_id=pt_users[0].user_id,
                    subscription_id=first_sub.subscription_id,
                    schedule_id=sample_sched.schedule_id,
                    booking_date=sample_day,
                    start_time=sample_st,
                    end_time=sample_en,
                    start_at=datetime.combine(sample_day, sample_st),
                    end_at=datetime.combine(sample_day, sample_en),
                    status=BookingStatus.CONFIRMED,
                )
                db.add(bk)
        db.commit()
    except Exception:
        db.rollback()

    # 8. Seed Lớp tập nhóm (Group Classes)
    try:
        if db.query(GroupClass).count() == 0 and len(pt_users) >= 3:
            first_member = db.query(Member).order_by(Member.member_id.asc()).first()
            class_specs = [
                ("Hatha Yoga Phục Hồi & Thở", "YOGA", pt_users[1].user_id, "Studio A · Tầng 2", today + timedelta(days=1), time(7, 0), time(8, 0), 15, "Lớp Yoga cân bằng tâm trí, kéo giãn cột sống và cải thiện độ dẻo dai."),
                ("Zumba Latin Đốt Mỡ Sôi Động", "ZUMBA", pt_users[1].user_id, "Studio B · Tầng 1", today + timedelta(days=1), time(18, 0), time(19, 0), 20, "Đốt 600 kcal mỗi giờ trên nền nhạc Latin tràn đầy năng lượng."),
                ("HIIT Full Body Burn", "HIIT", pt_users[2].user_id, "Khu Functional", today + timedelta(days=2), time(17, 30), time(18, 30), 12, "Tập luyện cường độ cao ngắt quãng giúp tăng sức bền và giảm mỡ tối đa."),
                ("Boxing & Footwork Cơ Bản", "BOXING", pt_users[2].user_id, "Khu Boxing Ring", today + timedelta(days=3), time(19, 0), time(20, 0), 10, "Kỹ thuật đấm, di chuyển và phản xạ thực chiến cùng HLV Quốc Bảo."),
            ]
            for cname, ccat, tid, room, sdate, st, et, cap, cdesc in class_specs:
                gc = GroupClass(
                    class_name=cname,
                    category=ccat,
                    trainer_id=tid,
                    room=room,
                    schedule_date=sdate,
                    start_time=st,
                    end_time=et,
                    max_capacity=cap,
                    status="ACTIVE",
                    description=cdesc,
                )
                db.add(gc)
                db.flush()
                if first_member and first_member.user_id:
                    enr = GroupClassEnrollment(
                        class_id=gc.class_id,
                        user_id=first_member.user_id,
                        status="REGISTERED",
                    )
                    db.add(enr)
            db.commit()
    except Exception:
        db.rollback()

    return {
        "plans": db.query(MembershipPlan).count(),
        "members": db.query(Member).count(),
        "equipment": db.query(Equipment).count(),
        "trainers": db.query(User).filter(User.role == UserRole.TRAINER).count(),
        "discounts": db.query(Discount).count(),
        "group_classes": db.query(GroupClass).count(),
    }


if __name__ == "__main__":
    session = SessionLocal()
    try:
        counts = seed_all(session)
        print("MySQL: connected | Seed dữ liệu mẫu thành công:", counts)
    finally:
        session.close()
