from app.db.database import Base
from app.models import (
    attendance_record,  # pyright: ignore[reportUnusedImport]
    audit_log,# pyright: ignore[reportUnusedImport]
    feedback,# pyright: ignore[reportUnusedImport]
    invoice,# pyright: ignore[reportUnusedImport]
    member,# pyright: ignore[reportUnusedImport]
    membership_plan,# pyright: ignore[reportUnusedImport]
    notification,# pyright: ignore[reportUnusedImport]
    payment,# pyright: ignore[reportUnusedImport]
    subscription,# pyright: ignore[reportUnusedImport]
    trainer_member,# pyright: ignore[reportUnusedImport]
    trainer_schedule,# pyright: ignore[reportUnusedImport]
    training_booking,# pyright: ignore[reportUnusedImport]
    user,# pyright: ignore[reportUnusedImport]
)

__all__ = ["Base"]