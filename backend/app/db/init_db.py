import secrets

from sqlalchemy import Index, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.database import engine
from app.db.subscription_routines import install_subscription_database_objects
from app.models.enums import UserRole, UserStatus
from app.models.member import Member
from app.models.user import User


def create_tables(target_engine: Engine | None = None) -> None:
    target_engine = target_engine or engine
    inspector = inspect(target_engine)
    if inspector.has_table("members") and "card_code" not in {
        column["name"] for column in inspector.get_columns("members")
    }:
        with target_engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE members ADD COLUMN card_code VARCHAR(32) NULL"
            )

    Base.metadata.create_all(bind=target_engine)

    with Session(bind=target_engine) as db:
        existing_card_codes = set(
            db.scalars(
                select(Member.card_code).where(Member.card_code.is_not(None))
            )
        )
        members_without_card = db.scalars(
            select(Member).where(Member.card_code.is_(None))
        )
        for member in members_without_card:
            card_code = f"DG-{secrets.token_hex(8).upper()}"
            while card_code in existing_card_codes:
                card_code = f"DG-{secrets.token_hex(8).upper()}"
            member.card_code = card_code
            existing_card_codes.add(card_code)
        db.commit()

    Index("ix_members_card_code", Member.card_code, unique=True).create(
        bind=target_engine, checkfirst=True
    )
    install_subscription_database_objects(target_engine)


def drop_tables() -> None:
    Base.metadata.drop_all(bind=engine)


def create_default_admin(db: Session, password_hash: str) -> User:
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        return admin
    admin = User(
        username="admin",
        password_hash=password_hash,
        full_name="System Administrator",
        email="admin@duckygym.local",
        phone="0900000000",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def init_db() -> None:
    create_tables()


if __name__ == "__main__":
    init_db()
    print("Database tables created")
