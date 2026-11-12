from typing import Any, Optional
from fastapi import status


class AppException(Exception):
    """Lớp lỗi cơ sở cho toàn bộ hệ thống DuckyGym"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "BAD_REQUEST",
        details: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class UnauthorizedException(AppException):
    """Lỗi 401: Chưa đăng nhập hoặc token không hợp lệ (UC01, NFR01)"""
    def __init__(self, message: str = "Thông tin xác thực không hợp lệ hoặc đã hết hạn") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    """Lỗi 403: Tài khoản bị khóa (BR02) hoặc không đủ quyền (BR01)"""
    def __init__(self, message: str = "Bạn không có quyền thực hiện chức năng này") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
        )


class NotFoundException(AppException):
    """Lỗi 404: Không tìm thấy bản ghi (Hội viên, Gói tập, Hóa đơn...)"""
    def __init__(self, message: str = "Không tìm thấy dữ liệu yêu cầu") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
        )


class ConflictException(AppException):
    """Lỗi 409: Trùng Email, SĐT (BR03) hoặc trùng ca làm việc/lịch đặt PT (BR12)"""
    def __init__(self, message: str = "Dữ liệu bị trùng lặp hoặc xung đột") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
        )


class BusinessRuleException(AppException):
    """Lỗi 422/400: Vi phạm các quy tắc nghiệp vụ BR01 -> BR15 trong SRS"""
    def __init__(self, message: str, error_code: str = "BUSINESS_RULE_VIOLATION") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
        )