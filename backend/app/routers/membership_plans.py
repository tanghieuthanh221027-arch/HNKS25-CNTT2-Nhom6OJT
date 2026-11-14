from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.membership_plan import (
    PlanCreate,
    PlanFilter,
    PlanResponse,
    PlanUpdate,
)
from app.services.membership_plan_service import (
    create_membership_plan,
    discontinue_membership_plan,
    get_membership_plan_by_id,
    get_membership_plans,
    update_membership_plan,
)

router = APIRouter(prefix="/gym-plans", tags=["Gym Plans"])


@router.get("", response_model=Page[PlanResponse])
def list_gym_plans(
    keyword: Optional[str] = Query(default=None, max_length=100),
    category: Optional[str] = Query(default=None, max_length=100),
    min_price: Optional[Decimal] = Query(default=None, ge=0),
    max_price: Optional[Decimal] = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Danh sách gói ACTIVE; hỗ trợ keyword, category, khoảng giá và phân trang."""
    page_params = PageParams(page=page, size=size)
    filters = PlanFilter(
        keyword=keyword,
        category=category,
        status=None,
        min_price=min_price,
        max_price=max_price,
    )

    items, total = get_membership_plans(db, filters, page_params)
    return Page[PlanResponse].create(items, total, page_params)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_gym_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    """Chi tiết gói tập; bao gồm cả gói ACTIVE và DISCONTINUED."""
    return get_membership_plan_by_id(db, plan_id)


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_gym_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return create_membership_plan(db, plan_data)


@router.put("/{plan_id}", response_model=PlanResponse)
def update_gym_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return update_membership_plan(db, plan_id, plan_data)


@router.delete("/{plan_id}", response_model=PlanResponse)
def delete_gym_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    """Soft delete: chuyển trạng thái sang DISCONTINUED."""
    return discontinue_membership_plan(db, plan_id)
