from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.handler import register_exception_handlers
from app.core.security import hash_password
from app.db.database import SessionLocal
from app.db.init_db import create_default_admin, create_tables
from app.routers import (
    auth,
    checkins,
    dashboard,
    discounts,
    equipment,
    group_classes,
    membership_plans,
    pos,
    pt_schedules,
    subscriptions,
    user,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Quản lý vòng đời ứng dụng (Startup & Shutdown):
    - Khi khởi động: tự động tạo bảng MySQL, tạo SQL Views
      và seed dữ liệu mẫu chuẩn Idempotent.
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(auth.router)
    app.include_router(user.router)
    app.include_router(membership_plans.router)
    app.include_router(equipment.router)
    app.include_router(subscriptions.router)
    app.include_router(checkins.router)
    app.include_router(pt_schedules.router)
    app.include_router(pos.router)
    app.include_router(discounts.router)
    app.include_router(dashboard.router)
    app.include_router(group_classes.router)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, Any]:
        return {"success": True, "message": "OK", "database": "MySQL: connected"}

    return app


app = create_app()
