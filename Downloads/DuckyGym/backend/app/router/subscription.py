from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db
from dependencies.auth import require_roles
from models.enums import UserRole
from models.user import User
from schemas.subscription import (
    SubscriptionDetailResponse,
    SubscriptionSelfCreate,
)
from service.subscription import (
    create_my_subscription,
    get_my_current_subscription,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

# Cho phép MEMBER (và ADMIN/STAFF khi test) gọi API đăng ký & xem thẻ
allow_member_subscription = require_roles(
    UserRole.MEMBER,
    UserRole.ADMIN,
    UserRole.STAFF,
)


@router.post(
    "",
    response_model=SubscriptionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hội viên đăng ký hoặc gia hạn gói tập",
)
def register_subscription(
    payload: SubscriptionSelfCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_member_subscription),
) -> SubscriptionDetailResponse:
    return create_my_subscription(db=db, current_user=current_user, payload=payload)


@router.get(
    "/me",
    response_model=SubscriptionDetailResponse,
    summary="Xem thẻ tập hiện tại kèm mã QR (Base64)",
)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_member_subscription),
) -> SubscriptionDetailResponse:
    return get_my_current_subscription(db=db, current_user=current_user)