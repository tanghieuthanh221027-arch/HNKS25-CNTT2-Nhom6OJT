from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.database import engine
from app.models.enums import UserRole, UserStatus
from app.models.user import User


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


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
