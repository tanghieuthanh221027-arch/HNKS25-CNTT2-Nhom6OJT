from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.handler import register_exception_handlers
from app.core.security import hash_password
from app.db.database import SessionLocal
from app.db.init_db import create_default_admin, create_tables
from app.routers import auth, users


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Quản lý vòng đời ứng dụng (Startup & Shutdown):
    - Khi khởi động: Tự động tạo bảng MySQL (nếu chưa có) và tạo tài khoản Admin mặc định.
    """
    create_tables()
    db = SessionLocal()
    try:
        create_default_admin(db, password_hash=hash_password("Admin123"))
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    
    # Sử dụng cấu hình CORS chuẩn của nhóm từ file config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # Đăng ký các router Đăng ký, Đăng nhập, và Users của bạn
    app.include_router(auth.router)
    app.include_router(users.router)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, Any]:
        return {"success": True, "message": "OK"}

    return app


app = create_app()