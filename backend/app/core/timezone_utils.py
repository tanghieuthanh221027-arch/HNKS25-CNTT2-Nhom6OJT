from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.exception import BadRequestException

try:
    VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except ZoneInfoNotFoundError:
    # Fallback chuẩn UTC+7 cho Windows khi môi trường chưa cài gói tzdata
    VN_TZ = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")


def now_vn() -> datetime:
    """Trả về datetime hiện tại theo múi giờ Việt Nam (Asia/Ho_Chi_Minh, UTC+7) dạng naive để tương thích đồng nhất với MySQL DATETIME."""
    return datetime.now(VN_TZ).replace(tzinfo=None)


def today_vn() -> date:
    """Trả về ngày hiện tại theo múi giờ Việt Nam (Asia/Ho_Chi_Minh, UTC+7), khắc phục lỗi lệch ngày từ 00:00 - 07:00 sáng."""
    return datetime.now(VN_TZ).date()


def resolve_iso_week_range(week: int, year: Optional[int] = None) -> tuple[date, date]:
    """
    Tính Thứ Hai đầu tuần và Chủ Nhật cuối tuần theo chuẩn ISO 8601.
    Bắt lỗi ValueError khi truyền week=53 vào năm chỉ có 52 tuần để trả HTTP 400 thay vì sập 500.
    """
    selected_year = year or today_vn().isocalendar().year
    if week < 1 or week > 53:
        raise BadRequestException(f"Số tuần ISO không hợp lệ ({week}). Phải nằm trong khoảng 1 đến 53.")
    try:
        week_start = date.fromisocalendar(selected_year, week, 1)
        week_end = date.fromisocalendar(selected_year, week, 7)
        return week_start, week_end
    except ValueError as exc:
        raise BadRequestException(
            f"Năm {selected_year} không có tuần ISO thứ {week} (chỉ có 52 tuần)."
        ) from exc
