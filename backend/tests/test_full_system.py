"""
Bộ Kiểm thử Tự động Toàn hệ thống DuckyGym (Full-System Automated Test Suite)
Bao phủ toàn bộ 11 API Routers, 4 vai trò RBAC, 4 SQL Views, Transaction ACID và dọn dẹp dữ liệu tạm sau khi chạy.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time as dt_time, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.exception import ConflictException
from app.core.timezone_utils import now_vn, today_vn
from app.db.database import SessionLocal
from app.db.seed import seed_all
from app.main import app
from app.services import pt_schedule_service
from app.models.attendance_record import AttendanceRecord
from app.models.body_metric import BodyMetric
from app.models.discount import Discount
from app.models.equipment import Equipment
from app.models.group_class import GroupClass, GroupClassEnrollment
from app.models.invoice import Invoice
from app.models.member import Member
from app.models.member_card import MemberCard
from app.models.membership_plan import MembershipPlan
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.trainer_schedule import TrainerSchedule
from app.models.training_booking import TrainingBooking
from app.models.user import User


@pytest.fixture(scope="module")
def client():
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def cleanup_registry():
    """Lưu lại ID các bản ghi tạm tạo trong quá trình test để dọn dẹp sạch sẽ khi kết thúc."""
    reg: dict[str, list[int]] = {
        "user_ids": [],
        "plan_ids": [],
        "equipment_ids": [],
        "discount_ids": [],
        "booking_ids": [],
        "schedule_ids": [],
        "class_ids": [],
    }
    yield reg

    db = SessionLocal()
    try:
        if reg["booking_ids"]:
            db.query(TrainingBooking).filter(
                TrainingBooking.booking_id.in_(reg["booking_ids"])
            ).delete(synchronize_session=False)

        if reg["schedule_ids"]:
            db.query(TrainerSchedule).filter(
                TrainerSchedule.schedule_id.in_(reg["schedule_ids"])
            ).delete(synchronize_session=False)

        if reg["class_ids"]:
            db.query(GroupClassEnrollment).filter(
                GroupClassEnrollment.class_id.in_(reg["class_ids"])
            ).delete(synchronize_session=False)
            db.query(GroupClass).filter(
                GroupClass.class_id.in_(reg["class_ids"])
            ).delete(synchronize_session=False)

        if reg["discount_ids"]:
            db.query(Discount).filter(
                Discount.discount_id.in_(reg["discount_ids"])
            ).delete(synchronize_session=False)

        if reg["equipment_ids"]:
            db.query(Equipment).filter(
                Equipment.equipment_id.in_(reg["equipment_ids"])
            ).delete(synchronize_session=False)

        if reg["user_ids"]:
            members = (
                db.query(Member)
                .filter(Member.user_id.in_(reg["user_ids"]))
                .all()
            )
            member_ids = [m.member_id for m in members]
            if member_ids:
                invs = (
                    db.query(Invoice)
                    .filter(Invoice.member_id.in_(member_ids))
                    .all()
                )
                inv_ids = [i.invoice_id for i in invs]
                if inv_ids:
                    db.query(Payment).filter(
                        Payment.invoice_id.in_(inv_ids)
                    ).delete(synchronize_session=False)
                    db.query(Invoice).filter(
                        Invoice.invoice_id.in_(inv_ids)
                    ).delete(synchronize_session=False)

                db.query(AttendanceRecord).filter(
                    AttendanceRecord.member_id.in_(member_ids)
                ).delete(synchronize_session=False)
                db.query(TrainingBooking).filter(
                    TrainingBooking.member_id.in_(member_ids)
                ).delete(synchronize_session=False)
                db.query(Subscription).filter(
                    Subscription.member_id.in_(member_ids)
                ).delete(synchronize_session=False)
                db.query(MemberCard).filter(
                    MemberCard.member_id.in_(member_ids)
                ).delete(synchronize_session=False)
                db.query(Member).filter(
                    Member.member_id.in_(member_ids)
                ).delete(synchronize_session=False)

            db.query(MemberCard).filter(
                MemberCard.user_id.in_(reg["user_ids"])
            ).delete(synchronize_session=False)
            db.query(BodyMetric).filter(
                BodyMetric.user_id.in_(reg["user_ids"])
            ).delete(synchronize_session=False)
            db.query(Notification).filter(
                Notification.user_id.in_(reg["user_ids"])
            ).delete(synchronize_session=False)
            db.query(GroupClassEnrollment).filter(
                GroupClassEnrollment.user_id.in_(reg["user_ids"])
            ).delete(synchronize_session=False)
            db.query(User).filter(
                User.user_id.in_(reg["user_ids"])
            ).delete(synchronize_session=False)

        if reg["plan_ids"]:
            db.query(MembershipPlan).filter(
                MembershipPlan.plan_id.in_(reg["plan_ids"])
            ).delete(synchronize_session=False)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@pytest.fixture(scope="module")
def tokens(client: TestClient) -> dict[str, str]:
    accounts = {
        "ADMIN": ("admin@duckygym.vn", "Admin123"),
        "STAFF": ("staff@duckygym.vn", "Staff123"),
        "MEMBER": ("member@duckygym.vn", "Member123"),
        "MEMBER_EXP": ("member02@duckygym.vn", "Member123"),
        "TRAINER": ("pt@duckygym.vn", "Trainer123"),
        "TRAINER2": ("mailinh.pt@duckygym.vn", "Trainer123"),
    }
    out: dict[str, str] = {}
    for role_key, (username, pw) in accounts.items():
        res = client.post("/auth/login", json={"username": username, "password": pw})
        assert res.status_code == 200, f"Login failed for {role_key}: {res.text}"
        out[role_key] = res.json()["token"]["access_token"]
    return out


def auth_h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# MODULE 01: SYSTEM & OPENAPI HEALTH (TC-SYS-01 .. TC-SYS-02)
# ==============================================================================
def test_tc_sys_01_health_check(client: TestClient):
    res = client.get("/health", headers={"Origin": "http://192.168.1.88:5173"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://192.168.1.88:5173"
    body = res.json()
    assert body["success"] is True
    assert "MySQL: connected" in body["database"]


def test_tc_sys_02_openapi_schema(client: TestClient):
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    for expected_path in (
        "/auth/login",
        "/users/me",
        "/gym-plans",
        "/equipment",
        "/subscriptions",
        "/checkins/qr",
        "/pt-schedules",
        "/pos/checkout",
        "/discounts",
        "/dashboard/summary",
        "/group-classes",
    ):
        assert expected_path in paths


# ==============================================================================
# MODULE 02: AUTHENTICATION & RBAC (TC-AUTH-01 .. TC-AUTH-12)
# ==============================================================================
def test_tc_auth_01_register_valid_member(client: TestClient, cleanup_registry: dict):
    suffix = str(int(time.time() * 1000))[-7:]
    email = f"pytest_reg_{suffix}@duckygym.vn"
    phone = f"097{suffix}"
    res = client.post(
        "/auth/register",
        json={
            "name": "Nguyễn Kiểm Thử",
            "email": email,
            "phone": phone,
            "password": "Password123",
        },
    )
    assert res.status_code == 201
    uid = res.json()["user_id"]
    cleanup_registry["user_ids"].append(uid)

    # Verify auto-login & MemberCard QR generation
    login_res = client.post("/auth/login", json={"username": email, "password": "Password123"})
    assert login_res.status_code == 200
    user_data = login_res.json()["user"]
    assert user_data["role"] == "MEMBER"
    assert user_data["member_code"].startswith("DG-")
    assert user_data["qr_base64"].startswith("data:image/svg+xml;base64,")


def test_tc_auth_02_register_duplicate_email(client: TestClient):
    res = client.post(
        "/auth/register",
        json={
            "name": "Trùng Email",
            "email": "member@duckygym.vn",
            "phone": "0969998887",
            "password": "Password123",
        },
    )
    assert res.status_code == 409
    assert "Email đã tồn tại" in res.json()["message"]


def test_tc_auth_03_register_duplicate_phone(client: TestClient):
    res = client.post(
        "/auth/register",
        json={
            "name": "Trùng SĐT",
            "email": f"dup_phone_{int(time.time())}@duckygym.vn",
            "phone": "0901000001",
            "password": "Password123",
        },
    )
    assert res.status_code == 409
    assert "Số điện thoại đã tồn tại" in res.json()["message"]


def test_tc_auth_04_register_invalid_phone_format(client: TestClient):
    res = client.post(
        "/auth/register",
        json={
            "name": "Sai SĐT",
            "email": "invalid_phone@duckygym.vn",
            "phone": "abcdefghij",
            "password": "Password123",
        },
    )
    assert res.status_code == 422
    assert res.json()["error_code"] == "VALIDATION_ERROR"


def test_tc_auth_05_register_short_password(client: TestClient):
    res = client.post(
        "/auth/register",
        json={
            "name": "Mật Khẩu Ngắn",
            "email": "shortpw@duckygym.vn",
            "phone": "0981112223",
            "password": "12345",
        },
    )
    assert res.status_code == 422


def test_tc_auth_06_to_09_login_four_roles(client: TestClient):
    cases = [
        ("admin@duckygym.vn", "Admin123", "ADMIN"),
        ("staff@duckygym.vn", "Staff123", "STAFF"),
        ("member@duckygym.vn", "Member123", "MEMBER"),
        ("pt@duckygym.vn", "Trainer123", "TRAINER"),
    ]
    for email, pw, expected_role in cases:
        r = client.post("/auth/login", json={"username": email, "password": pw})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == expected_role
        assert r.json()["token"]["token_type"] == "bearer"


def test_tc_auth_10_login_by_username_and_phone(client: TestClient):
    r_uname = client.post("/auth/login", json={"username": "hoivien", "password": "Member123"})
    r_phone = client.post("/auth/login", json={"username": "0901000001", "password": "Member123"})
    assert r_uname.status_code == 200
    assert r_phone.status_code == 200
    assert r_uname.json()["user"]["user_id"] == r_phone.json()["user"]["user_id"]


def test_tc_auth_11_login_wrong_credentials(client: TestClient):
    r1 = client.post("/auth/login", json={"username": "member@duckygym.vn", "password": "WrongPassword1"})
    r2 = client.post("/auth/login", json={"username": "nobody_exists@duckygym.vn", "password": "Password123"})
    assert r1.status_code == 401
    assert r2.status_code == 401


def test_tc_auth_12_missing_forged_token_and_rbac_403(client: TestClient, tokens: dict):
    # Missing token -> 401
    assert client.get("/users/me").status_code == 401
    # Forged token -> 401
    assert client.get("/users/me", headers=auth_h("eyJhbGciOiJIUzI1NiJ9.forged.sig")).status_code == 401
    # MEMBER accessing STAFF/ADMIN endpoints -> 403
    assert client.post("/checkins/qr", json={"qr_code": "DG-000006"}, headers=auth_h(tokens["MEMBER"])).status_code == 403
    assert client.get("/dashboard/summary", headers=auth_h(tokens["MEMBER"])).status_code == 403
    assert client.get("/dashboard/export-csv", headers=auth_h(tokens["STAFF"])).status_code == 403


# ==============================================================================
# MODULE 03: USERS, PROFILE, BODY METRICS & BMI (TC-USER-01 .. TC-USER-08)
# ==============================================================================
def test_tc_user_01_get_me_profile(client: TestClient, tokens: dict):
    res = client.get("/users/me", headers=auth_h(tokens["MEMBER"]))
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "member@duckygym.vn"
    assert len(data["badges"]) == 3


def test_tc_user_02_update_height_weight_auto_bmi(client: TestClient, tokens: dict):
    res = client.put(
        "/users/me",
        headers=auth_h(tokens["MEMBER"]),
        json={"height_cm": 175.0, "weight_kg": 70.0, "address": "Hà Đông, Hà Nội"},
    )
    assert res.status_code == 200
    assert float(res.json()["bmi"]) == 22.9


def test_tc_user_03_update_profile_duplicate_email_or_phone(client: TestClient, tokens: dict):
    r_email = client.put(
        "/users/me",
        headers=auth_h(tokens["MEMBER"]),
        json={"email": "admin@duckygym.vn"},
    )
    r_phone = client.put(
        "/users/me",
        headers=auth_h(tokens["MEMBER"]),
        json={"phone": "0900000000"},
    )
    assert r_email.status_code == 409
    assert r_phone.status_code == 409


def test_tc_user_04_change_password_wrong_current(client: TestClient, tokens: dict):
    res = client.put(
        "/users/me",
        headers=auth_h(tokens["MEMBER"]),
        json={"current_password": "IncorrectOldPassword", "new_password": "NewPassword123"},
    )
    assert res.status_code == 401


def test_tc_user_05_change_password_roundtrip(client: TestClient, cleanup_registry: dict):
    suffix = str(int(time.time() * 1000))[-7:]
    email = f"pwchange_{suffix}@duckygym.vn"
    phone = f"096{suffix}"
    reg = client.post(
        "/auth/register",
        json={"name": "HV Đổi MK", "email": email, "phone": phone, "password": "OldPassword123"},
    )
    assert reg.status_code == 201
    cleanup_registry["user_ids"].append(reg.json()["user_id"])

    tok = client.post("/auth/login", json={"username": email, "password": "OldPassword123"}).json()["token"]["access_token"]
    upd = client.put(
        "/users/me",
        headers=auth_h(tok),
        json={"current_password": "OldPassword123", "new_password": "NewPassword456"},
    )
    assert upd.status_code == 200
    assert client.post("/auth/login", json={"username": email, "password": "NewPassword456"}).status_code == 200


def test_tc_user_06_body_metrics_create_and_list(client: TestClient, tokens: dict):
    c_res = client.post(
        "/users/body-metrics",
        headers=auth_h(tokens["MEMBER"]),
        json={
            "height_cm": 175.0,
            "weight_kg": 69.2,
            "body_fat_pct": 16.0,
            "muscle_mass_kg": 33.5,
            "waist_cm": 76.0,
            "notes": "Pytest BodyMetric",
        },
    )
    assert c_res.status_code == 201
    assert float(c_res.json()["bmi"]) == 22.6

    l_res = client.get("/users/body-metrics", headers=auth_h(tokens["MEMBER"]))
    assert l_res.status_code == 200
    assert len(l_res.json()) >= 1


def test_tc_user_07_list_trainers(client: TestClient):
    res = client.get("/users/trainers")
    assert res.status_code == 200
    assert len(res.json()) >= 3


def test_tc_user_08_search_members_rbac(client: TestClient, tokens: dict):
    ok_res = client.get("/users/members?keyword=0901000001", headers=auth_h(tokens["STAFF"]))
    assert ok_res.status_code == 200
    assert len(ok_res.json()) >= 1

    forb_res = client.get("/users/members?keyword=0901000001", headers=auth_h(tokens["MEMBER"]))
    assert forb_res.status_code == 403


# ==============================================================================
# MODULE 04: GYM PLANS CRUD (TC-PLAN-01 .. TC-PLAN-07)
# ==============================================================================
def test_tc_plan_01_list_active_plans(client: TestClient):
    res = client.get("/gym-plans?page=1&size=20")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 5
    assert all(item["status"] == "ACTIVE" for item in data["items"])


def test_tc_plan_02_filter_plans_price_range(client: TestClient):
    res = client.get("/gym-plans?min_price=400000&max_price=1500000")
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert 400000 <= float(item["price"]) <= 1500000


def test_tc_plan_03_get_plan_detail_and_404(client: TestClient):
    assert client.get("/gym-plans/1").status_code == 200
    assert client.get("/gym-plans/999999").status_code == 404


def test_tc_plan_04_to_07_admin_plan_crud_and_discontinue(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    # Non-admin blocked
    assert (
        client.post(
            "/gym-plans",
            headers=auth_h(tokens["STAFF"]),
            json={"plan_name": "Blocked Plan", "category": "Test", "duration_days": 30, "price": 500000},
        ).status_code
        == 403
    )

    # Duplicate name -> 409 & non-positive price -> 422
    assert (
        client.post(
            "/gym-plans",
            headers=auth_h(tokens["ADMIN"]),
            json={"plan_name": "Starter 1 Tháng", "category": "Gói Cơ Bản", "duration_days": 30, "price": 499000},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/gym-plans",
            headers=auth_h(tokens["ADMIN"]),
            json={"plan_name": "Zero Price Plan", "category": "Test", "duration_days": 30, "price": 0},
        ).status_code
        == 422
    )

    # Create valid plan
    pname = f"Pytest VIP {int(time.time() * 1000) % 1000000}"
    c_res = client.post(
        "/gym-plans",
        headers=auth_h(tokens["ADMIN"]),
        json={
            "plan_name": pname,
            "category": "Gói Kiểm Thử",
            "duration_days": 60,
            "price": 990000,
            "description": "Gói test tự động",
        },
    )
    assert c_res.status_code == 201
    pid = c_res.json()["plan_id"]
    cleanup_registry["plan_ids"].append(pid)

    # Update plan & empty update validation
    assert client.put(f"/gym-plans/{pid}", headers=auth_h(tokens["ADMIN"]), json={}).status_code == 422
    u_res = client.put(
        f"/gym-plans/{pid}",
        headers=auth_h(tokens["ADMIN"]),
        json={"price": 1050000, "description": "Đã cập nhật giá"},
    )
    assert u_res.status_code == 200
    assert float(u_res.json()["price"]) == 1050000

    # Soft discontinue
    d_res = client.delete(f"/gym-plans/{pid}", headers=auth_h(tokens["ADMIN"]))
    assert d_res.status_code == 200
    assert d_res.json()["status"] == "DISCONTINUED"

    # Hidden from public list, visible in include_all=true
    pub_ids = [p["plan_id"] for p in client.get("/gym-plans?size=100").json()["items"]]
    all_ids = [p["plan_id"] for p in client.get("/gym-plans?include_all=true&size=100").json()["items"]]
    assert pid not in pub_ids
    assert pid in all_ids


# ==============================================================================
# MODULE 05: EQUIPMENT & MAINTENANCE (TC-EQ-01 .. TC-EQ-07)
# ==============================================================================
def test_tc_eq_01_and_02_list_and_maintenance_due(client: TestClient):
    r_all = client.get("/equipment")
    assert r_all.status_code == 200
    assert r_all.json()["total"] >= 10

    r_zone = client.get("/equipment?zone=Cardio&status=HOAT_DONG")
    assert r_zone.status_code == 200
    assert all(i["status"] == "HOAT_DONG" for i in r_zone.json()["items"])

    r_due = client.get("/equipment/maintenance-due?days=7")
    assert r_due.status_code == 200
    assert "due_count" in r_due.json()


def test_tc_eq_03_to_07_equipment_lifecycle(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    # STAFF cannot create equipment -> 403
    assert (
        client.post(
            "/equipment",
            headers=auth_h(tokens["STAFF"]),
            json={"name": "Staff Machine", "zone": "Cardio"},
        ).status_code
        == 403
    )

    # Invalid status -> 422
    assert (
        client.post(
            "/equipment",
            headers=auth_h(tokens["ADMIN"]),
            json={"name": f"BadStatus {time.time()}", "zone": "Cardio", "status": "UNKNOWN"},
        ).status_code
        == 422
    )

    # Create valid equipment
    eq_name = f"Máy Chèo Thuyền Concept2 #{int(time.time() * 1000) % 100000}"
    c_res = client.post(
        "/equipment",
        headers=auth_h(tokens["ADMIN"]),
        json={
            "name": eq_name,
            "zone": "Khu Cardio",
            "status": "HONG",
            "maintenance_interval_days": 20,
        },
    )
    assert c_res.status_code == 201
    eq_id = c_res.json()["equipment_id"]
    cleanup_registry["equipment_ids"].append(eq_id)

    # Duplicate name -> 409
    assert (
        client.post(
            "/equipment",
            headers=auth_h(tokens["ADMIN"]),
            json={"name": eq_name, "zone": "Khu Cardio"},
        ).status_code
        == 409
    )

    # Update equipment
    u_res = client.put(
        f"/equipment/{eq_id}",
        headers=auth_h(tokens["ADMIN"]),
        json={"status": "BAO_TRI", "notes": "Đang thay dây cáp"},
    )
    assert u_res.status_code == 200
    assert u_res.json()["status"] == "BAO_TRI"

    # STAFF marks equipment maintained today
    m_res = client.post(f"/equipment/{eq_id}/maintain", headers=auth_h(tokens["STAFF"]))
    assert m_res.status_code == 200
    assert m_res.json()["status"] == "HOAT_DONG"
    expected_next = (date.today() + timedelta(days=20)).isoformat()
    assert m_res.json()["next_maintenance_date"] == expected_next

    # Delete equipment & verify 404 afterwards
    del_res = client.delete(f"/equipment/{eq_id}", headers=auth_h(tokens["ADMIN"]))
    assert del_res.status_code == 200
    cleanup_registry["equipment_ids"].remove(eq_id)
    assert client.get(f"/equipment/{eq_id}").status_code == 404


# ==============================================================================
# MODULE 06: SUBSCRIPTIONS, AUTO-RENEWAL & EXPIRY REMINDERS (TC-SUB-01 .. TC-SUB-08)
# ==============================================================================
def test_tc_sub_01_to_05_subscription_new_renew_and_voucher(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    suffix = str(int(time.time() * 1000))[-7:]
    email = f"subflow_{suffix}@duckygym.vn"
    phone = f"093{suffix}"
    reg = client.post(
        "/auth/register",
        json={"name": "HV Gói Tập", "email": email, "phone": phone, "password": "Password123"},
    )
    assert reg.status_code == 201
    cleanup_registry["user_ids"].append(reg.json()["user_id"])
    mem_tok = client.post("/auth/login", json={"username": email, "password": "Password123"}).json()["token"]["access_token"]

    # TC-SUB-01: Initially NO_SUBSCRIPTION
    me0 = client.get("/subscriptions/me", headers=auth_h(mem_tok))
    assert me0.status_code == 200
    assert me0.json()["has_subscription"] is False
    assert me0.json()["card_status"] == "NO_SUBSCRIPTION"

    # TC-SUB-02 & TC-SUB-04: First subscription (NEW) + WELCOME20 (-20%)
    sub1 = client.post(
        "/subscriptions",
        headers=auth_h(mem_tok),
        json={"plan_id": 1, "payment_method": "BANK_TRANSFER", "discount_code": "WELCOME20"},
    )
    assert sub1.status_code == 201
    s1 = sub1.json()
    assert s1["subscription_type"] == "NEW"
    assert float(s1["discount_amount"]) == 99800.0
    assert float(s1["final_amount"]) == 399200.0

    # TC-SUB-03: Immediate renewal (RENEW) -> start_date = s1.end_date + 1 day (BR06)
    sub2 = client.post(
        "/subscriptions",
        headers=auth_h(mem_tok),
        json={"plan_id": 1, "payment_method": "CASH"},
    )
    assert sub2.status_code == 201
    s2 = sub2.json()
    assert s2["subscription_type"] == "RENEW"
    expected_renew_start = (date.fromisoformat(s1["end_date"]) + timedelta(days=1)).isoformat()
    assert s2["start_date"] == expected_renew_start

    # TC-SUB-05: Non-existent plan -> 404 & ADMIN calling /subscriptions -> 422
    assert client.post("/subscriptions", headers=auth_h(mem_tok), json={"plan_id": 999999}).status_code == 404
    assert client.post("/subscriptions", headers=auth_h(tokens["ADMIN"]), json={"plan_id": 1}).status_code == 422


def test_tc_sub_06_to_08_near_expiry_and_email_reminders(client: TestClient, tokens: dict):
    exp_list = client.get("/subscriptions/expiring-soon?within_days=7", headers=auth_h(tokens["STAFF"]))
    assert exp_list.status_code == 200
    assert "items" in exp_list.json()

    # RBAC check for MEMBER
    assert client.get("/subscriptions/expiring-soon", headers=auth_h(tokens["MEMBER"])).status_code == 403

    # Trigger BackgroundTasks reminder
    rem = client.post("/subscriptions/send-expiry-reminders?within_days=7", headers=auth_h(tokens["STAFF"]))
    assert rem.status_code == 200
    assert "queued_count" in rem.json()


# ==============================================================================
# MODULE 07: QR CHECK-IN / CHECK-OUT KIOSK (TC-QR-01 .. TC-QR-08)
# ==============================================================================
def test_tc_qr_01_to_08_qr_kiosk_flows(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    # Create fresh member to test NO_SUBSCRIPTION, then subscribe and test CHECK_IN -> CHECK_OUT
    suffix = str(int(time.time() * 1000))[-7:]
    email = f"qrflow_{suffix}@duckygym.vn"
    phone = f"094{suffix}"
    reg = client.post(
        "/auth/register",
        json={"name": "HV Quét QR", "email": email, "phone": phone, "password": "Password123"},
    )
    cleanup_registry["user_ids"].append(reg.json()["user_id"])
    login_data = client.post("/auth/login", json={"username": email, "password": "Password123"}).json()
    mem_tok = login_data["token"]["access_token"]
    card_code = login_data["user"]["member_code"]

    # TC-QR-03: Scan before buying a plan -> NO_SUBSCRIPTION
    no_sub_scan = client.post(
        "/checkins/qr",
        headers=auth_h(tokens["STAFF"]),
        json={"qr_code": card_code},
    )
    assert no_sub_scan.status_code == 200
    assert no_sub_scan.json()["valid"] is False
    assert no_sub_scan.json()["status"] == "NO_SUBSCRIPTION"

    # Buy plan
    assert client.post("/subscriptions", headers=auth_h(mem_tok), json={"plan_id": 1}).status_code == 201

    # TC-QR-01: 1st Scan -> CHECK_IN (< 1000ms)
    s_in = client.post("/checkins/qr", headers=auth_h(tokens["STAFF"]), json={"qr_code": card_code})
    assert s_in.status_code == 200
    d_in = s_in.json()
    assert d_in["valid"] is True
    assert d_in["action"] == "CHECK_IN"
    assert d_in["response_time_ms"] < 1000

    # TC-QR-02: 2nd Scan -> CHECK_OUT (< 1000ms)
    s_out = client.post("/checkins/qr", headers=auth_h(tokens["STAFF"]), json={"qr_code": card_code})
    assert s_out.status_code == 200
    d_out = s_out.json()
    assert d_out["valid"] is True
    assert d_out["action"] == "CHECK_OUT"
    assert d_out["duration_minutes"] >= 1
    assert d_out["response_time_ms"] < 1000

    # TC-QR-04: Expired card scan (member18@duckygym.vn)
    m18 = client.get("/users/members?keyword=member18@duckygym.vn", headers=auth_h(tokens["STAFF"])).json()
    assert len(m18) >= 1
    exp_scan = client.post(
        "/checkins/qr",
        headers=auth_h(tokens["STAFF"]),
        json={"qr_code": m18[0]["member_code"]},
    )
    assert exp_scan.status_code == 200
    assert exp_scan.json()["valid"] is False
    assert exp_scan.json()["status"] == "EXPIRED_CARD"

    # TC-QR-05: Unknown QR code -> INVALID_CODE
    inv_scan = client.post(
        "/checkins/qr",
        headers=auth_h(tokens["STAFF"]),
        json={"qr_code": "DG-999999-FAKE"},
    )
    assert inv_scan.status_code == 200
    assert inv_scan.json()["valid"] is False
    assert inv_scan.json()["status"] == "INVALID_CODE"

    # TC-QR-07: Attendance history data isolation
    own_hist = client.get("/checkins/history?page=1&size=20", headers=auth_h(mem_tok)).json()
    assert own_hist["total"] == 1
    staff_hist = client.get("/checkins/history?page=1&size=20", headers=auth_h(tokens["STAFF"])).json()
    assert staff_hist["total"] >= own_hist["total"]


# ==============================================================================
# MODULE 08: PT 1-1 WEEKLY SCHEDULING & RED-NOTE FIXES (TC-PT-01 .. TC-PT-17)
# ==============================================================================
def test_tc_pt_01_to_07_pt_booking_and_conflicts(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    sched_res = client.get("/pt-schedules", headers=auth_h(tokens["MEMBER"]))
    assert sched_res.status_code == 200
    trainers = sched_res.json()["trainers"]
    assert len(trainers) >= 2
    t1_id = trainers[0]["user_id"]
    t2_id = trainers[1]["user_id"]

    future_day = (today_vn() + timedelta(days=45)).isoformat()

    # Invalid end_time <= start_time (daytime non-overnight) -> 422
    assert (
        client.post(
            "/pt-schedules",
            headers=auth_h(tokens["MEMBER"]),
            json={"trainer_id": t1_id, "booking_date": future_day, "start_time": "15:00", "end_time": "14:00"},
        ).status_code
        == 422
    )

    # Non-member (STAFF without member_id) cannot self-book PT -> 422
    assert (
        client.post(
            "/pt-schedules",
            headers=auth_h(tokens["STAFF"]),
            json={"trainer_id": t1_id, "booking_date": future_day, "start_time": "15:00"},
        ).status_code
        == 422
    )

    # Clean up any leftover bookings on future_day from interrupted runs
    db = SessionLocal()
    try:
        db.query(TrainingBooking).filter(
            TrainingBooking.booking_date == date.fromisoformat(future_day)
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    # Create a dedicated temporary second member with active PT sessions for conflict check
    suffix2 = str(int(time.time() * 1000))[-7:]
    email2 = f"pt_peer_{suffix2}@duckygym.vn"
    reg2 = client.post(
        "/auth/register",
        json={"name": "HV Đối Chiếu PT", "email": email2, "phone": f"094{suffix2}", "password": "Password123"},
    )
    assert reg2.status_code == 201
    cleanup_registry["user_ids"].append(reg2.json()["user_id"])
    tok_peer = client.post("/auth/login", json={"username": email2, "password": "Password123"}).json()["token"]["access_token"]
    assert client.post("/subscriptions", headers=auth_h(tok_peer), json={"plan_id": 1}).status_code == 201

    # Valid booking inside open TrainerSchedule
    bk_res = client.post(
        "/pt-schedules",
        headers=auth_h(tokens["MEMBER"]),
        json={"trainer_id": t1_id, "booking_date": future_day, "start_time": "15:00"},
    )
    assert bk_res.status_code == 201
    bk_id = bk_res.json()["booking_id"]
    cleanup_registry["booking_ids"].append(bk_id)
    used_sub_id = bk_res.json()["subscription_id"]

    # Trainer time-slot conflict (BR13) -> 409
    assert (
        client.post(
            "/pt-schedules",
            headers=auth_h(tok_peer),
            json={"trainer_id": t1_id, "booking_date": future_day, "start_time": "15:00"},
        ).status_code
        == 409
    )

    # Member personal time-slot conflict with another trainer at same hour (BR14) -> 409
    assert (
        client.post(
            "/pt-schedules",
            headers=auth_h(tokens["MEMBER"]),
            json={"trainer_id": t2_id, "booking_date": future_day, "start_time": "15:00"},
        ).status_code
        == 409
    )

    # RBAC: MEMBER cannot CONFIRMED -> 403; wrong trainer (TRAINER2) cannot CONFIRMED -> 403
    assert client.patch(f"/pt-schedules/{bk_id}/confirm", headers=auth_h(tokens["MEMBER"])).status_code == 403
    assert client.patch(f"/pt-schedules/{bk_id}/confirm", headers=auth_h(tokens["TRAINER2"])).status_code == 403

    # Trainer 1 confirms -> completes (deducts 1 PT session) & terminal state blocks further cancel
    conf = client.patch(f"/pt-schedules/{bk_id}/confirm", headers=auth_h(tokens["TRAINER"]))
    assert conf.status_code == 200
    assert conf.json()["status"] == "CONFIRMED"
    before_rem = conf.json()["sessions_remaining"]

    comp = client.patch(f"/pt-schedules/{bk_id}/complete", headers=auth_h(tokens["TRAINER"]))
    assert comp.status_code == 200
    assert comp.json()["status"] == "COMPLETED"
    assert comp.json()["sessions_remaining"] == before_rem - 1

    # Restore seeded member's session quota after verifying deduction
    db = SessionLocal()
    try:
        sub_row = db.get(Subscription, used_sub_id)
        if sub_row:
            sub_row.sessions_remaining += 1
            db.commit()
    finally:
        db.close()

    # Terminal COMPLETED cannot transition to CANCELLED -> 400
    assert (
        client.patch(
            f"/pt-schedules/{bk_id}/cancel",
            headers=auth_h(tokens["ADMIN"]),
            json={"reason": "Invalid after complete"},
        ).status_code
        == 400
    )


def test_tc_past_01_reject_past_hour_today_br15(client: TestClient, tokens: dict):
    """[Mục 4.4 & 7.3 - TC_PAST_01] Đặt lịch vào giờ đã qua trong ngày hôm nay -> 400 Bad Request."""
    t1_id = client.get("/users/trainers").json()[0]["user_id"]
    res = client.post(
        "/pt-schedules",
        headers=auth_h(tokens["MEMBER"]),
        json={
            "trainer_id": t1_id,
            "booking_date": today_vn().isoformat(),
            "start_time": "00:05",
        },
    )
    assert res.status_code == 400
    assert "BR15" in res.json()["message"]


def test_tc_quota_01_reject_exhausted_pt_sessions_br16(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    """[Mục 4.4 & 7.3 - TC_QUOTA_01] Hội viên hết số buổi tập PT (sessions_remaining=0) cố đặt -> 403 Forbidden."""
    # Tạo gói chỉ tập Gym (pt_sessions = 0)
    pname = f"Gym Only No PT {int(time.time() * 1000) % 100000}"
    p_res = client.post(
        "/gym-plans",
        headers=auth_h(tokens["ADMIN"]),
        json={"plan_name": pname, "category": "Gym Cơ Bản", "duration_days": 30, "pt_sessions": 0, "price": 350000},
    )
    assert p_res.status_code == 201
    pid = p_res.json()["plan_id"]
    cleanup_registry["plan_ids"].append(pid)

    suffix = str(int(time.time() * 1000))[-7:]
    email = f"noquota_{suffix}@duckygym.vn"
    phone = f"095{suffix}"
    reg = client.post(
        "/auth/register",
        json={"name": "HV Không Có PT", "email": email, "phone": phone, "password": "Password123"},
    )
    cleanup_registry["user_ids"].append(reg.json()["user_id"])
    tok = client.post("/auth/login", json={"username": email, "password": "Password123"}).json()["token"]["access_token"]

    # Mua gói Gym Only (sessions_remaining = 0)
    sub_res = client.post("/subscriptions", headers=auth_h(tok), json={"plan_id": pid})
    assert sub_res.status_code == 201
    assert sub_res.json()["sessions_remaining"] == 0

    t1_id = client.get("/users/trainers").json()[0]["user_id"]
    bk_res = client.post(
        "/pt-schedules",
        headers=auth_h(tok),
        json={"trainer_id": t1_id, "booking_date": (today_vn() + timedelta(days=10)).isoformat(), "start_time": "09:00"},
    )
    assert bk_res.status_code == 403
    assert "BR16" in bk_res.json()["message"]


def test_tc_cancel_late_01_reject_within_2_hours_br17(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    """[Mục 4.4 & 7.3 - TC_CANCEL_LATE] Hội viên huỷ ca sát giờ (< 2 tiếng trước start_time) -> 400 Bad Request."""
    t1_id = client.get("/users/trainers").json()[0]["user_id"]
    near_start = (now_vn() + timedelta(minutes=65)).replace(second=0, microsecond=0)
    near_end = near_start + timedelta(hours=1)
    is_overnight = near_end.date() > near_start.date()

    slot_res = client.post(
        "/pt-schedules/work-slots",
        headers=auth_h(tokens["ADMIN"]),
        json={
            "trainer_id": t1_id,
            "work_date": near_start.date().isoformat(),
            "start_time": near_start.strftime("%H:%M"),
            "end_time": near_end.strftime("%H:%M"),
            "overnight": is_overnight,
        },
    )
    assert slot_res.status_code == 201
    cleanup_registry["schedule_ids"].append(slot_res.json()["schedule_id"])

    bk_res = client.post(
        "/pt-schedules",
        headers=auth_h(tokens["MEMBER"]),
        json={
            "trainer_id": t1_id,
            "booking_date": near_start.date().isoformat(),
            "start_time": near_start.strftime("%H:%M"),
            "end_time": near_end.strftime("%H:%M"),
            "overnight": is_overnight,
        },
    )
    assert bk_res.status_code == 201
    bk_id = bk_res.json()["booking_id"]
    cleanup_registry["booking_ids"].append(bk_id)

    late_cancel = client.patch(
        f"/pt-schedules/{bk_id}/cancel",
        headers=auth_h(tokens["MEMBER"]),
        json={"reason": "Bận đột xuất sát giờ"},
    )
    assert late_cancel.status_code == 400
    assert "BR17" in late_cancel.json()["message"]


def test_tc_adjacent_and_noshow_and_auto_expire(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    """
    Kiểm tra:
    - TC_ADJACENT_01: Đặt 2 khung giờ liền kề (08:00-09:00 và 09:00-10:00) -> Cả 2 đều 201.
    - Mục 4.5 & 5.6: CONFIRMED -> NO_SHOW trừ 1 buổi sessions_remaining.
    - Mục 4.5: PENDING quá 2 giờ tự động chuyển sang EXPIRED & giải phóng slot cho người khác đặt.
    """
    t1_id = client.get("/users/trainers").json()[0]["user_id"]
    day_adj = (today_vn() + timedelta(days=48)).isoformat()

    # Pre-clean any leftover bookings on day_adj from interrupted runs
    db = SessionLocal()
    try:
        db.query(TrainingBooking).filter(
            TrainingBooking.booking_date == date.fromisoformat(day_adj)
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    # Create a dedicated temporary second member with active PT sessions
    suffix_adj = str(int(time.time() * 1000))[-7:]
    email_adj = f"adj_peer_{suffix_adj}@duckygym.vn"
    reg_adj = client.post(
        "/auth/register",
        json={"name": "HV Liền Kề PT", "email": email_adj, "phone": f"092{suffix_adj}", "password": "Password123"},
    )
    assert reg_adj.status_code == 201
    cleanup_registry["user_ids"].append(reg_adj.json()["user_id"])
    tok_adj = client.post("/auth/login", json={"username": email_adj, "password": "Password123"}).json()["token"]["access_token"]
    assert client.post("/subscriptions", headers=auth_h(tok_adj), json={"plan_id": 1}).status_code == 201

    b1 = client.post(
        "/pt-schedules",
        headers=auth_h(tokens["MEMBER"]),
        json={"trainer_id": t1_id, "booking_date": day_adj, "start_time": "08:00", "end_time": "09:00"},
    )
    assert b1.status_code == 201, b1.text
    b1_id = b1.json()["booking_id"]
    b1_sub_id = b1.json()["subscription_id"]
    cleanup_registry["booking_ids"].append(b1_id)

    b2 = client.post(
        "/pt-schedules",
        headers=auth_h(tok_adj),
        json={"trainer_id": t1_id, "booking_date": day_adj, "start_time": "09:00", "end_time": "10:00"},
    )
    assert b2.status_code == 201, b2.text
    b2_id = b2.json()["booking_id"]
    cleanup_registry["booking_ids"].append(b2_id)

    # b1: CONFIRMED -> NO_SHOW (deducts 1 session)
    c1 = client.patch(f"/pt-schedules/{b1_id}/confirm", headers=auth_h(tokens["TRAINER"]))
    rem_before = c1.json()["sessions_remaining"]
    ns = client.patch(
        f"/pt-schedules/{b1_id}/no-show",
        headers=auth_h(tokens["TRAINER"]),
        json={"reason": "Học viên không tới"},
    )
    assert ns.status_code == 200
    assert ns.json()["status"] == "NO_SHOW"
    assert ns.json()["sessions_remaining"] == rem_before - 1

    # Restore seeded member's session quota after verifying NO_SHOW deduction
    db = SessionLocal()
    try:
        sub_row = db.get(Subscription, b1_sub_id)
        if sub_row:
            sub_row.sessions_remaining += 1
            db.commit()
    finally:
        db.close()

    # b2: Giả lập ca PENDING đã tạo cách đây 3 giờ -> tự động EXPIRED và giải phóng slot 09:00-10:00
    db = SessionLocal()
    try:
        bk_row = db.get(TrainingBooking, b2_id)
        bk_row.created_at = now_vn() - timedelta(hours=3)
        db.commit()
    finally:
        db.close()

    # Khi MEMBER đặt vào đúng slot 09:00-10:00 đó, b2 tự chuyển sang EXPIRED và đặt mới thành công 201!
    b3 = client.post(
        "/pt-schedules",
        headers=auth_h(tokens["MEMBER"]),
        json={"trainer_id": t1_id, "booking_date": day_adj, "start_time": "09:00", "end_time": "10:00"},
    )
    assert b3.status_code == 201
    cleanup_registry["booking_ids"].append(b3.json()["booking_id"])

    db = SessionLocal()
    try:
        assert db.get(TrainingBooking, b2_id).status.value == "EXPIRED"
    finally:
        db.close()


def test_tc_workslot_strict_and_overnight_and_delete_week53(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    """
    Kiểm tra:
    - Mục 5.3: Đặt ngoài ca trực mở TrainerSchedule bị chặn 400 (không tự tạo ca trực cho PT).
    - Mục 5.2: Mở ca trực xuyên đêm 23:00 -> 01:00 và đặt ca xuyên đêm thành công 201.
    - Mục 1.4 & 5.6: DELETE /pt-schedules/{id} bị chặn 403 Forbidden.
    - Mục 5.5: GET /pt-schedules?week=53&year=2025 trả 400 Bad Request thay vì lỗi 500.
    """
    t1_id = client.get("/users/trainers").json()[0]["user_id"]
    unseeded_day = (today_vn() + timedelta(days=95)).isoformat()

    # Chưa mở ca trực -> 400
    outside = client.post(
        "/pt-schedules",
        headers=auth_h(tokens["MEMBER"]),
        json={"trainer_id": t1_id, "booking_date": unseeded_day, "start_time": "08:00"},
    )
    assert outside.status_code == 400

    # PT mở ca trực xuyên đêm 23:00 -> 01:00 hôm sau
    night_slot = client.post(
        "/pt-schedules/work-slots",
        headers=auth_h(tokens["TRAINER"]),
        json={
            "trainer_id": t1_id,
            "work_date": unseeded_day,
            "start_time": "23:00",
            "end_time": "01:00",
            "overnight": True,
        },
    )
    assert night_slot.status_code == 201
    cleanup_registry["schedule_ids"].append(night_slot.json()["schedule_id"])

    # Đặt ca xuyên đêm 23:00 -> 01:00 thành công!
    night_bk = client.post(
        "/pt-schedules",
        headers=auth_h(tokens["MEMBER"]),
        json={
            "trainer_id": t1_id,
            "booking_date": unseeded_day,
            "start_time": "23:00",
            "end_time": "01:00",
            "overnight": True,
        },
    )
    assert night_bk.status_code == 201
    night_bk_id = night_bk.json()["booking_id"]
    cleanup_registry["booking_ids"].append(night_bk_id)

    # Cấm xoá vật lý ca tập (DELETE) -> 403 Forbidden
    assert client.delete(f"/pt-schedules/{night_bk_id}", headers=auth_h(tokens["TRAINER"])).status_code == 403
    assert client.delete(f"/pt-schedules/{night_bk_id}", headers=auth_h(tokens["ADMIN"])).status_code == 403

    # Tràn tuần ISO week=53 vào năm chỉ có 52 tuần (2025) -> 400 Bad Request
    assert client.get("/pt-schedules?week=53&year=2025", headers=auth_h(tokens["MEMBER"])).status_code == 400
    assert client.get("/pt-schedules?week=48&year=2026", headers=auth_h(tokens["MEMBER"])).status_code == 200


def test_tc_race_condition_and_fk_restrict_on_mysql(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    """
    [Mục 5.2, 6.1 & 7.2]
    1. Bắn đồng thời 2 luồng (ThreadPoolExecutor) đặt cùng 1 slot PT trên MySQL InnoDB thật:
       Khoá bi quan with_for_update() đảm bảo đúng 1 luồng thành công và 1 luồng bị chặn ConflictException.
    2. Cố xoá vật lý Member đang có TrainingBooking: Khoá ngoại ON DELETE RESTRICT chặn cứng bằng IntegrityError.
    """
    t1_id = client.get("/users/trainers").json()[0]["user_id"]
    race_day = today_vn() + timedelta(days=52)

    db_setup = SessionLocal()
    try:
        u1 = db_setup.query(User).filter(User.email == "member@duckygym.vn").first()
        u2 = db_setup.query(User).filter(User.email == "member02@duckygym.vn").first()
        u1_id, u2_id = u1.user_id, u2.user_id
    finally:
        db_setup.close()

    def concurrent_book(uid: int) -> str:
        s = SessionLocal()
        try:
            usr = s.get(User, uid)
            bk = pt_schedule_service.create_pt_booking(
                db=s,
                current_user=usr,
                trainer_id=t1_id,
                booking_date=race_day,
                start_time=dt_time(16, 0),
                end_time=dt_time(17, 0),
            )
            cleanup_registry["booking_ids"].append(bk["booking_id"])
            return "CREATED"
        except ConflictException:
            s.rollback()
            return "CONFLICT"
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(concurrent_book, [u1_id, u2_id]))

    assert sorted(outcomes) == ["CONFLICT", "CREATED"]

    # Kiểm chứng ON DELETE RESTRICT ngăn chặn xoá vật lý Member đang có ca tập
    db_fk = SessionLocal()
    try:
        booked_member = db_fk.query(Member).filter(Member.user_id.in_([u1_id, u2_id])).first()
        db_fk.delete(booked_member)
        with pytest.raises(IntegrityError):
            db_fk.commit()
        db_fk.rollback()
    finally:
        db_fk.close()


# ==============================================================================
# MODULE 09: POS RECEPTION & ACID CHECKOUT (TC-POS-01 .. TC-POS-06)
# ==============================================================================
def test_tc_pos_01_to_06_pos_lookup_acid_checkout_and_rollback(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    # Lookup existing & non-existing phone
    f_yes = client.get("/pos/member-lookup?phone=0901000001", headers=auth_h(tokens["STAFF"]))
    f_no = client.get("/pos/member-lookup?phone=0999000111", headers=auth_h(tokens["STAFF"]))
    assert f_yes.status_code == 200 and f_yes.json()["found"] is True
    assert f_no.status_code == 200 and f_no.json()["found"] is False

    # Walk-in new phone without full_name -> 422
    suffix = str(int(time.time() * 1000))[-7:]
    walkin_phone = f"091{suffix}"
    assert (
        client.post(
            "/pos/checkout",
            headers=auth_h(tokens["STAFF"]),
            json={"phone": walkin_phone, "plan_id": 1, "payment_method": "CASH"},
        ).status_code
        == 422
    )

    # Walk-in with expired voucher -> 422 AND transaction rolled back (member NOT persisted!)
    bad_co = client.post(
        "/pos/checkout",
        headers=auth_h(tokens["STAFF"]),
        json={
            "phone": walkin_phone,
            "full_name": "Khách Rollback",
            "plan_id": 1,
            "discount_code": "EXPIRED10",
            "payment_method": "CASH",
        },
    )
    assert bad_co.status_code == 422
    lookup_after_rollback = client.get(
        f"/pos/member-lookup?phone={walkin_phone}",
        headers=auth_h(tokens["STAFF"]),
    )
    assert lookup_after_rollback.json()["found"] is False

    # Valid walk-in POS checkout with WELCOME20
    good_co = client.post(
        "/pos/checkout",
        headers=auth_h(tokens["STAFF"]),
        json={
            "phone": walkin_phone,
            "full_name": "Khách Vãng Lai POS",
            "plan_id": 1,
            "discount_code": "WELCOME20",
            "payment_method": "CASH",
        },
    )
    assert good_co.status_code == 201
    co_data = good_co.json()
    assert float(co_data["billing"]["final_amount"]) == 399200.0
    assert co_data["invoice_code"].startswith("INV-")

    # Register walk-in user_id for teardown cleanup
    lookup_created = client.get(
        f"/pos/member-lookup?phone={walkin_phone}",
        headers=auth_h(tokens["STAFF"]),
    ).json()
    if lookup_created.get("user_id"):
        cleanup_registry["user_ids"].append(lookup_created["user_id"])

    # List POS invoices
    inv_res = client.get(f"/pos/invoices?keyword={walkin_phone}", headers=auth_h(tokens["STAFF"]))
    assert inv_res.status_code == 200
    assert inv_res.json()["total"] == 1


# ==============================================================================
# MODULE 10: DISCOUNTS / VOUCHERS CRUD & VALIDATION (TC-DISC-01 .. TC-DISC-06)
# ==============================================================================
def test_tc_disc_01_to_06_discounts_validation_and_crud(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    assert client.get("/discounts").status_code == 200

    # Validate WELCOME20 (20%) & SUMMER100K (-100k)
    v_pct = client.post(
        "/discounts/validate",
        headers=auth_h(tokens["MEMBER"]),
        json={"code": "WELCOME20", "order_amount": 499000},
    )
    assert v_pct.status_code == 200
    assert float(v_pct.json()["discount_amount"]) == 99800.0

    v_fix = client.post(
        "/discounts/validate",
        headers=auth_h(tokens["MEMBER"]),
        json={"code": "SUMMER100K", "order_amount": 499000},
    )
    assert v_fix.status_code == 200
    assert float(v_fix.json()["discount_amount"]) == 100000.0

    # Expired, min_order not met, and not found
    assert (
        client.post(
            "/discounts/validate",
            headers=auth_h(tokens["MEMBER"]),
            json={"code": "EXPIRED10", "order_amount": 499000},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/discounts/validate",
            headers=auth_h(tokens["MEMBER"]),
            json={"code": "DUCKYVIP", "order_amount": 499000},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/discounts/validate",
            headers=auth_h(tokens["MEMBER"]),
            json={"code": "NOTEXIST999", "order_amount": 499000},
        ).status_code
        == 404
    )

    # Admin create -> reject >100% -> update -> reject >100% on update (BUG-05) -> delete
    assert (
        client.post(
            "/discounts",
            headers=auth_h(tokens["ADMIN"]),
            json={
                "code": "OVER100PCT",
                "discount_type": "PERCENT",
                "discount_value": 120,
                "expiry_date": (date.today() + timedelta(days=10)).isoformat(),
            },
        ).status_code
        == 422
    )

    v_code = f"PYTEST{int(time.time() * 1000) % 100000}"
    c_res = client.post(
        "/discounts",
        headers=auth_h(tokens["ADMIN"]),
        json={
            "code": v_code,
            "description": "Pytest Voucher",
            "discount_type": "PERCENT",
            "discount_value": 25,
            "min_order_amount": 200000,
            "expiry_date": (date.today() + timedelta(days=30)).isoformat(),
            "usage_limit": 10,
        },
    )
    assert c_res.status_code == 201
    did = c_res.json()["discount_id"]
    cleanup_registry["discount_ids"].append(did)

    # BUG-05 regression: updating PERCENT discount_value > 100 must return 422
    assert (
        client.put(
            f"/discounts/{did}",
            headers=auth_h(tokens["ADMIN"]),
            json={"discount_value": 150},
        ).status_code
        == 422
    )

    u_res = client.put(
        f"/discounts/{did}",
        headers=auth_h(tokens["ADMIN"]),
        json={"discount_value": 30},
    )
    assert u_res.status_code == 200
    assert float(u_res.json()["discount_value"]) == 30.0

    # STAFF cannot delete voucher -> 403; ADMIN deletes -> 200
    assert client.delete(f"/discounts/{did}", headers=auth_h(tokens["STAFF"])).status_code == 403
    assert client.delete(f"/discounts/{did}", headers=auth_h(tokens["ADMIN"])).status_code == 200
    cleanup_registry["discount_ids"].remove(did)


# ==============================================================================
# MODULE 11: DASHBOARD KPI SQL VIEWS & GROUP CLASSES (TC-DASH-01..03, TC-CLASS-01..06)
# ==============================================================================
def test_tc_dash_01_to_03_dashboard_sql_views_and_csv(client: TestClient, tokens: dict):
    s_res = client.get("/dashboard/summary", headers=auth_h(tokens["ADMIN"]))
    assert s_res.status_code == 200
    data = s_res.json()
    assert data["kpis"]["total_members"] >= 20
    assert len(data["plan_breakdown_chart"]) >= 5

    # Filtered date summary
    f_res = client.get(
        "/dashboard/summary?from_date=2026-01-01&to_date=2026-12-31",
        headers=auth_h(tokens["STAFF"]),
    )
    assert f_res.status_code == 200

    # Export CSV (ADMIN only, starts with UTF-8 BOM)
    csv_res = client.get("/dashboard/export-csv", headers=auth_h(tokens["ADMIN"]))
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert csv_res.text.startswith("\ufeff")
    assert "BÁO CÁO DOANH THU THEO NGÀY" in csv_res.text


def test_tc_class_01_to_06_group_classes_capacity_and_attendance(
    client: TestClient, tokens: dict, cleanup_registry: dict
):
    assert client.get("/group-classes", headers=auth_h(tokens["MEMBER"])).status_code == 200

    # Invalid start/end time -> 422 & MEMBER cannot create class -> 403
    assert (
        client.post(
            "/group-classes",
            headers=auth_h(tokens["MEMBER"]),
            json={
                "class_name": "Forbidden Class",
                "room": "Studio A",
                "schedule_date": (date.today() + timedelta(days=3)).isoformat(),
                "start_time": "08:00",
                "end_time": "09:00",
            },
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/group-classes",
            headers=auth_h(tokens["STAFF"]),
            json={
                "class_name": "Invalid Hours Class",
                "room": "Studio A",
                "schedule_date": (date.today() + timedelta(days=3)).isoformat(),
                "start_time": "10:00",
                "end_time": "09:00",
            },
        ).status_code
        == 422
    )

    # Create class with max_capacity = 1 to test capacity limit!
    c_res = client.post(
        "/group-classes",
        headers=auth_h(tokens["STAFF"]),
        json={
            "class_name": f"HIIT Capacity Test {int(time.time()) % 10000}",
            "category": "HIIT",
            "room": "Studio Test",
            "schedule_date": (date.today() + timedelta(days=7)).isoformat(),
            "start_time": "17:00",
            "end_time": "18:00",
            "max_capacity": 1,
        },
    )
    assert c_res.status_code == 201
    cid = c_res.json()["class_id"]
    cleanup_registry["class_ids"].append(cid)

    # Member 1 enrolls -> 200 OK
    enr1 = client.post(f"/group-classes/{cid}/enroll", headers=auth_h(tokens["MEMBER"]))
    assert enr1.status_code == 200
    assert enr1.json()["is_full"] is True

    # Duplicate enrollment by Member 1 -> 409 Conflict
    assert client.post(f"/group-classes/{cid}/enroll", headers=auth_h(tokens["MEMBER"])).status_code == 409

    # Second member tries to enroll when class is full (max_capacity=1) -> 422 BusinessRuleException
    assert client.post(f"/group-classes/{cid}/enroll", headers=auth_h(tokens["MEMBER_EXP"])).status_code == 422

    # STAFF lists enrollments & marks attendance ATTENDED
    enr_list = client.get(f"/group-classes/{cid}/enrollments", headers=auth_h(tokens["STAFF"])).json()
    enrollment_id = enr_list["students"][0]["enrollment_id"]

    # Invalid attendance status -> 422
    assert (
        client.put(
            f"/group-classes/{cid}/attendance/{enrollment_id}",
            headers=auth_h(tokens["STAFF"]),
            json={"status": "INVALID_ST"},
        ).status_code
        == 422
    )

    att_ok = client.put(
        f"/group-classes/{cid}/attendance/{enrollment_id}",
        headers=auth_h(tokens["STAFF"]),
        json={"status": "ATTENDED"},
    )
    assert att_ok.status_code == 200
    assert att_ok.json()["status"] == "ATTENDED"

    # Member cancels enrollment -> 200; cancelling again -> 404
    assert client.delete(f"/group-classes/{cid}/enroll", headers=auth_h(tokens["MEMBER"])).status_code == 200
    assert client.delete(f"/group-classes/{cid}/enroll", headers=auth_h(tokens["MEMBER"])).status_code == 404
