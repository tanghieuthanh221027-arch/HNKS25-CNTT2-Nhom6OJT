from contextlib import asynccontextmanager

from typing import Any, AsyncGenerator

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.core.handler import register_exception_handlers

from app.core.security import hash_password

from app.db.database import SessionLocal

from app.db.init_db import create_default_admin, create_tables

# Khi bạn tạo xong thư mục app/routers (hoặc app/api), chỉ cần bỏ comment dòng dưới:

# from app.routers import api_router

@asynccontextmanager

async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:

    """

    Quản lý vòng đời ứng dụng (Startup & Shutdown):

    - Khi khởi động: Tự động tạo 13 bảng MySQL (nếu chưa có) và tạo tài khoản Admin mặc định.

    """

    create_tables()

    db = SessionLocal()

    try:

        create_default_admin(

            db, password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD)

        )

    finally:

        db.close()

    yield

def create_app() -> FastAPI:

    app = FastAPI(

        title=settings.APP_NAME,

        version=settings.APP_VERSION,

        description="Hệ thống quản lý phòng tập thể hình DuckyGym (GYMHUB MVP)",

        openapi_url="/api/v1/openapi.json",

        docs_url="/docs",

        redoc_url="/redoc",

        lifespan=lifespan,

    )

    # Cấu hình CORS cho phép Frontend (ReactJS + Vite) gọi API

    app.add_middleware(

        CORSMiddleware,

        allow_origins=[

            "http://localhost:5173",

            "http://127.0.0.1:5173",

            "http://localhost:3000",

        ],

        allow_credentials=True,

        allow_methods=["*"],

        allow_headers=["*"],

    )

    # Đăng ký bộ bắt lỗi toàn cục (AppException, ValidationError, IntegrityError...)

    register_exception_handlers(app)

    # Gắn toàn bộ các router nghiệp vụ (UC01 -> UC06) vào prefix /api/v1

    # app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["System"])

    def root() -> dict[str, Any]:

        return {

            "success": True,

            "message": f"Welcome to {settings.APP_NAME}",

            "version": settings.APP_VERSION,

            "docs": "/docs",

        }

    @app.get("/health", tags=["System"])

    def health_check() -> dict[str, Any]:

        return {"success": True, "message": "OK"}

    return app

app = create_app()
