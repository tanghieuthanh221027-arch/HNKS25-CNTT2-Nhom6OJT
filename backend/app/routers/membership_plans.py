from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import require_admin
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


@router.get("", response_model=Page[PlanResponse], summary="Danh sách gói tập đang mở (hoặc tất cả cho Admin)")
def list_gym_plans(
    keyword: Optional[str] = Query(default=None, max_length=100),
    category: Optional[str] = Query(default=None, max_length=100),
    include_all: bool = Query(default=False, description="Hiển thị cả gói đã ẩn (DISCONTINUED)"),
    min_price: Optional[Decimal] = Query(default=None, ge=0),
    max_price: Optional[Decimal] = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    page_params = PageParams(page=page, size=size)
    filters = PlanFilter(
        keyword=keyword,
        category=category,
        status=None,
        include_all=include_all,
        min_price=min_price,
        max_price=max_price,
    )

    items, total = get_membership_plans(db, filters, page_params)
    return Page[PlanResponse].create(items, total, page_params)


@router.get("/{plan_id}", response_model=PlanResponse, summary="Xem chi tiết gói tập")
def get_gym_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    return get_membership_plan_by_id(db, plan_id)


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Thêm gói tập mới (giá > 0, tên không trùng)",
)
def create_gym_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return create_membership_plan(db, plan_data)


@router.put("/{plan_id}", response_model=PlanResponse, summary="[ADMIN] Cập nhật gói tập hoặc ẩn/hiện")
def update_gym_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return update_membership_plan(db, plan_id, plan_data)


@router.delete("/{plan_id}", response_model=PlanResponse, summary="[ADMIN] Ẩn / Ngừng kinh doanh gói tập")
def delete_gym_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return discontinue_membership_plan(db, plan_id)
