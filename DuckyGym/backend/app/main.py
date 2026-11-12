
from fastapi import FastAPI

from app.core.config import settings
from app.router.membership_plan import router as membership_plan_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API hệ thống quản lý phòng Gym và hội viên",
)

app.include_router(membership_plan_router)


@app.get("/")
def root():
    return {"message": "DuckyGym Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
