from typing import Any, Optional
from fastapi import status


class AppException(Exception):
    """Base Exception cho toàn bộ dự án DuckyGym"""
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
    def __init__(self, message: str = "Không có quyền truy cập hoặc phiên đăng nhập hết hạn") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Không tìm thấy dữ liệu yêu cầu") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
        )


class ConflictException(AppException):
    """Dùng cho lỗi trùng Email/SĐT (BR03) hoặc trùng lịch PT (BR12)"""
    def __init__(self, message: str = "Dữ liệu đã tồn tại hoặc xung đột") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
        )


class BusinessRuleException(AppException):
    """Dùng cho các vi phạm quy tắc nghiệp vụ BR01 -> BR15"""
    def __init__(self, message: str, rule_code: str = "BUSINESS_RULE_VIOLATION") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=rule_code,
        )