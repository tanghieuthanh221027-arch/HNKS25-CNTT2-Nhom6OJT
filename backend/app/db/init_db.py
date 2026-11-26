from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.db.schema_upgrade import upgrade_mysql_schema
from app.db.seed import seed_all
from app.models.enums import UserRole, UserStatus
from app.models.user import User


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        upgrade_mysql_schema(db)
    finally:
        db.close()


def drop_tables() -> None:
    Base.metadata.drop_all(bind=engine)


def create_default_admin(db: Session, password_hash: str) -> User:
    try:
        seed_all(db)
    except Exception:
        db.rollback()

    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        return admin
    admin = User(
        username="admin",
        password_hash=password_hash,
        full_name="System Administrator",
        email="admin@duckygym.vn",
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
