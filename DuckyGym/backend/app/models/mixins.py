"""Các cột thời gian được dùng chung bởi nhiều bảng."""

from datetime import datetime

from sqlalchemy import DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column


class CreatedAtMixin:
    """Tự ghi thời điểm tạo bản ghi mới."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
    )


class TimestampMixin(CreatedAtMixin):
    """Tự cập nhật updated_at khi bản ghi thay đổi."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        onupdate=func.now(),
    )
