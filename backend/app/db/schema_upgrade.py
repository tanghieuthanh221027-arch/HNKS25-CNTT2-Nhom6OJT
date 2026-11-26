"""
Tự động nâng cấp cấu trúc bảng MySQL hiện hữu (Idempotent Live Schema Migration):
1. Bổ sung pt_sessions cho membership_plans & total_sessions / sessions_remaining cho subscriptions (Mục 3.2.4, BR16).
2. Bổ sung subscription_id, start_at, end_at, cancel_reason và 6 trạng thái BookingStatus cho training_bookings (Mục 3.2.6, 4.5, 5.2).
3. Bổ sung start_at, end_at và gỡ ràng buộc chặn ca đêm trên trainer_schedules & training_bookings (Mục 5.2).
4. Chuẩn hoá 3NF bảng members: xoá cột dư thừa full_name, phone, email, đặt user_id NOT NULL UNIQUE (Mục 3.2.1 & 3.2.2).
5. Đổi toàn bộ khoá ngoại nguy hiểm ondelete=CASCADE sang ON DELETE RESTRICT (Mục 6.1, BR04).
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def _has_column(db: Session, table_name: str, column_name: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :tname
              AND COLUMN_NAME = :cname
            """
        ),
        {"tname": table_name, "cname": column_name},
    ).scalar()
    return bool(row and int(row) > 0)


def _has_check_constraint(db: Session, table_name: str, constraint_name: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :tname
              AND CONSTRAINT_NAME = :cname
              AND CONSTRAINT_TYPE = 'CHECK'
            """
        ),
        {"tname": table_name, "cname": constraint_name},
    ).scalar()
    return bool(row and int(row) > 0)


def _has_index(db: Session, table_name: str, index_name: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :tname
              AND INDEX_NAME = :iname
            """
        ),
        {"tname": table_name, "iname": index_name},
    ).scalar()
    return bool(row and int(row) > 0)


def upgrade_mysql_schema(db: Session) -> None:
    dialect = db.bind.dialect.name if db.bind else ""
    if dialect != "mysql":
        return

    # 1. membership_plans.pt_sessions
    if not _has_column(db, "membership_plans", "pt_sessions"):
        db.execute(
            text("ALTER TABLE membership_plans ADD COLUMN pt_sessions INT NOT NULL DEFAULT 0 AFTER duration_days")
        )
        db.commit()

    # Cập nhật số buổi PT mặc định cho 5 gói tập gốc nếu đang = 0
    default_plan_sessions = [
        ("Starter 1 Tháng", 3),
        ("Pro Fitness 3 Tháng", 5),
        ("Pro Fitness 6 Tháng", 7),
        ("VIP Elite 12 Tháng", 12),
        ("Coaching PT 1-1 (10 Buổi)", 10),
    ]
    for pname, sess in default_plan_sessions:
        db.execute(
            text(
                "UPDATE membership_plans SET pt_sessions = :sess WHERE plan_name = :pname AND pt_sessions = 0"
            ),
            {"sess": sess, "pname": pname},
        )
    db.commit()

    # 2. subscriptions.total_sessions & sessions_remaining (Mục 3.2.4)
    if not _has_column(db, "subscriptions", "total_sessions"):
        db.execute(
            text("ALTER TABLE subscriptions ADD COLUMN total_sessions INT NOT NULL DEFAULT 0 AFTER end_date")
        )
        db.commit()
    if not _has_column(db, "subscriptions", "sessions_remaining"):
        db.execute(
            text("ALTER TABLE subscriptions ADD COLUMN sessions_remaining INT NOT NULL DEFAULT 0 AFTER total_sessions")
        )
        db.commit()

    db.execute(
        text(
            """
            UPDATE subscriptions s
            JOIN membership_plans mp ON mp.plan_id = s.plan_id
            SET s.total_sessions = mp.pt_sessions,
                s.sessions_remaining = mp.pt_sessions
            WHERE s.total_sessions = 0 AND mp.pt_sessions > 0
            """
        )
    )
    db.commit()

    # 3. trainer_schedules: start_at, end_at & gỡ ck_trainer_schedules_time_range hỗ trợ ca đêm (Mục 5.2)
    if _has_check_constraint(db, "trainer_schedules", "ck_trainer_schedules_time_range"):
        db.execute(text("ALTER TABLE trainer_schedules DROP CHECK ck_trainer_schedules_time_range"))
        db.commit()

    if not _has_column(db, "trainer_schedules", "start_at"):
        db.execute(text("ALTER TABLE trainer_schedules ADD COLUMN start_at DATETIME NULL AFTER end_time"))
        db.commit()
    if not _has_column(db, "trainer_schedules", "end_at"):
        db.execute(text("ALTER TABLE trainer_schedules ADD COLUMN end_at DATETIME NULL AFTER start_at"))
        db.commit()

    db.execute(
        text(
            """
            UPDATE trainer_schedules
            SET start_at = TIMESTAMP(work_date, start_time),
                end_at = TIMESTAMP(
                    IF(end_time > start_time, work_date, DATE_ADD(work_date, INTERVAL 1 DAY)),
                    end_time
                )
            WHERE start_at IS NULL OR end_at IS NULL
            """
        )
    )
    db.commit()

    # 4. training_bookings: subscription_id, start_at, end_at, cancel_reason & gỡ check cũ (Mục 3.2.6, 5.2)
    if _has_check_constraint(db, "training_bookings", "ck_training_bookings_time_range"):
        db.execute(text("ALTER TABLE training_bookings DROP CHECK ck_training_bookings_time_range"))
        db.commit()

    if not _has_column(db, "training_bookings", "subscription_id"):
        db.execute(text("ALTER TABLE training_bookings ADD COLUMN subscription_id INT NULL AFTER trainer_id"))
        db.commit()
    if not _has_column(db, "training_bookings", "start_at"):
        db.execute(text("ALTER TABLE training_bookings ADD COLUMN start_at DATETIME NULL AFTER end_time"))
        db.commit()
    if not _has_column(db, "training_bookings", "end_at"):
        db.execute(text("ALTER TABLE training_bookings ADD COLUMN end_at DATETIME NULL AFTER start_at"))
        db.commit()
    if not _has_column(db, "training_bookings", "cancel_reason"):
        db.execute(text("ALTER TABLE training_bookings ADD COLUMN cancel_reason VARCHAR(255) NULL AFTER status"))
        db.commit()

    # Đảm bảo cột status đủ rộng cho NO_SHOW & EXPIRED
    db.execute(
        text("ALTER TABLE training_bookings MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'PENDING'")
    )
    db.commit()

    db.execute(
        text(
            """
            UPDATE training_bookings
            SET start_at = TIMESTAMP(booking_date, start_time),
                end_at = TIMESTAMP(
                    IF(end_time > start_time, booking_date, DATE_ADD(booking_date, INTERVAL 1 DAY)),
                    end_time
                )
            WHERE start_at IS NULL OR end_at IS NULL
            """
        )
    )
    db.commit()

    # Backfill subscription_id cho các bản ghi training_bookings cũ
    db.execute(
        text(
            """
            UPDATE training_bookings tb
            SET tb.subscription_id = (
                SELECT s.subscription_id
                FROM subscriptions s
                WHERE s.member_id = tb.member_id
                ORDER BY (s.status = 'ACTIVE') DESC, s.end_date DESC
                LIMIT 1
            )
            WHERE tb.subscription_id IS NULL
            """
        )
    )
    db.commit()

    # Xoá các booking mồ côi nếu member chưa từng có bất kỳ subscription nào trước khi đặt NOT NULL
    db.execute(text("DELETE FROM training_bookings WHERE subscription_id IS NULL"))
    db.commit()

    db.execute(
        text(
            """
            ALTER TABLE training_bookings
                MODIFY COLUMN subscription_id INT NOT NULL,
                MODIFY COLUMN start_at DATETIME NOT NULL,
                MODIFY COLUMN end_at DATETIME NOT NULL
            """
        )
    )
    db.commit()

    if not _has_check_constraint(db, "training_bookings", "ck_training_bookings_datetime_range"):
        db.execute(
            text(
                "ALTER TABLE training_bookings ADD CONSTRAINT ck_training_bookings_datetime_range CHECK (end_at > start_at)"
            )
        )
        db.commit()

    # 5. Chuẩn hoá 3NF bảng members: xoá full_name, phone, email dư thừa & đặt user_id NOT NULL (Mục 3.2.1 & 3.2.2)
    if _has_column(db, "members", "email"):
        db.execute(
            text(
                """
                UPDATE members m
                JOIN users u ON (u.email = m.email OR u.phone = m.phone)
                SET m.user_id = u.user_id
                WHERE m.user_id IS NULL
                """
            )
        )
        db.commit()

    if _has_index(db, "members", "ix_members_full_name"):
        db.execute(text("ALTER TABLE members DROP INDEX ix_members_full_name"))
        db.commit()

    for redundant_col in ("full_name", "phone", "email"):
        if _has_column(db, "members", redundant_col):
            db.execute(text(f"ALTER TABLE members DROP COLUMN {redundant_col}"))
            db.commit()

    # 6. Chuyển toàn bộ khoá ngoại nguy hiểm sang ON DELETE RESTRICT (Mục 6.1, BR04)
    fk_rows = db.execute(
        text(
            """
            SELECT
                kcu.TABLE_NAME AS table_name,
                kcu.CONSTRAINT_NAME AS constraint_name,
                kcu.COLUMN_NAME AS column_name,
                kcu.REFERENCED_TABLE_NAME AS ref_table,
                kcu.REFERENCED_COLUMN_NAME AS ref_column,
                rc.DELETE_RULE AS delete_rule
            FROM information_schema.KEY_COLUMN_USAGE kcu
            JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
              ON rc.CONSTRAINT_SCHEMA = kcu.TABLE_SCHEMA
             AND rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE kcu.TABLE_SCHEMA = DATABASE()
              AND kcu.TABLE_NAME IN (
                  'training_bookings',
                  'trainer_schedules',
                  'attendance_records',
                  'trainer_members',
                  'feedbacks',
                  'members',
                  'member_cards'
              )
              AND kcu.COLUMN_NAME IN ('member_id', 'trainer_id', 'user_id', 'subscription_id', 'schedule_id')
              AND rc.DELETE_RULE <> 'RESTRICT'
            """
        )
    ).mappings().all()

    for fk in fk_rows:
        tname = fk["table_name"]
        cname = fk["constraint_name"]
        col = fk["column_name"]
        ref_t = fk["ref_table"]
        ref_c = fk["ref_column"]
        db.execute(text(f"ALTER TABLE {tname} DROP FOREIGN KEY {cname}"))
        if tname == "members" and col == "user_id":
            db.execute(text("ALTER TABLE members MODIFY COLUMN user_id INT NOT NULL"))
        db.execute(
            text(
                f"ALTER TABLE {tname} ADD CONSTRAINT {cname} "
                f"FOREIGN KEY ({col}) REFERENCES {ref_t}({ref_c}) "
                f"ON DELETE RESTRICT ON UPDATE CASCADE"
            )
        )
        db.commit()

    # Bổ sung FK cho training_bookings.subscription_id nếu chưa tồn tại
    has_sub_fk = db.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'training_bookings'
              AND COLUMN_NAME = 'subscription_id'
              AND REFERENCED_TABLE_NAME = 'subscriptions'
            """
        )
    ).scalar()
    if not has_sub_fk:
        db.execute(
            text(
                "ALTER TABLE training_bookings ADD CONSTRAINT fk_training_bookings_subscription_id "
                "FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) "
                "ON DELETE RESTRICT ON UPDATE CASCADE"
            )
        )
        db.commit()
