from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exception import AppException


def register_exception_handlers(app: FastAPI) -> None:
    """Đăng ký các bộ bắt lỗi toàn cục cho ứng dụng FastAPI."""

    # 1. Bắt các lỗi nghiệp vụ tự định nghĩa (AppException, Unauthorized, Forbidden...)
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    # 2. Bắt lỗi HTTPException mặc định của FastAPI/Starlette
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": None,
            },
        )

    # 3. Bắt lỗi Validate dữ liệu đầu vào từ Pydantic Schemas (422 Unprocessable Entity)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors: list[dict[str, str]] = []
        for err in exc.errors():
            # Lấy tên trường bị lỗi (bỏ qua phần tử đầu như 'body', 'query')
            loc = err.get("loc", ())
            field_name = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else str(loc[0])
            errors.append({
                "field": field_name,
                "message": err.get("msg", "Giá trị không hợp lệ"),
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": errors[0]["message"] if errors else "Dữ liệu đầu vào không hợp lệ",
                "details": errors,
            },
        )

    # 4. Bắt lỗi Ràng buộc CSDL từ MySQL (BR03: trùng Email/SĐT/Username, khóa ngoại...)
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
        orig_msg = str(exc.orig).lower() if exc.orig else ""
        message = "Dữ liệu vi phạm ràng buộc toàn vẹn cơ sở dữ liệu (NFR04)."

        if "duplicate entry" in orig_msg:
            if "email" in orig_msg:
                message = "Email này đã được sử dụng (BR03)."
            elif "phone" in orig_msg:
                message = "Số điện thoại này đã được sử dụng (BR03)."
            elif "username" in orig_msg:
                message = "Tên đăng nhập đã tồn tại."
            else:
                message = "Dữ liệu bị trùng lặp trong hệ thống."
        elif "foreign key constraint" in orig_msg:
            message = "Không thể thực hiện do dữ liệu đang được liên kết với bản ghi khác (BR04)."

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error_code": "DATABASE_INTEGRITY_ERROR",
                "message": message,
                "details": None,
            },
        )

    # 5. Bắt các lỗi truy vấn SQLAlchemy chung khác (NFR05: không làm lộ cấu trúc bảng)
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(_request: Request, _exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_code": "DATABASE_ERROR",
                "message": "Đã xảy ra lỗi trong quá trình xử lý cơ sở dữ liệu. Giao dịch đã được hoàn tác (NFR05).",
                "details": None,
            },
        )