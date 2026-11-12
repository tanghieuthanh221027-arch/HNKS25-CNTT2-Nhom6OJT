from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.handler import register_exception_handlers
from router.subscription import router as subscription_router
from router.user import router as user_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(user_router)
    app.include_router(subscription_router)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, Any]:
        return {"success": True, "message": "OK"}

    return app


app = create_app()