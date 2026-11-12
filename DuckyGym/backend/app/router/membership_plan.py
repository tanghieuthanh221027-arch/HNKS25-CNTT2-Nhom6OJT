
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.core.dependencies import require_role
from app.models.enums import UserRole
from app.models.user import User
from app.db.database import get_db
from app.models.enums import PlanStatus
from app.schemas.membership_plan import PlanFilter, PlanResponse,PlanCreate,PlanUpdate
from app.service import membership_plan_service
from fastapi import HTTPException

router = APIRouter(
    prefix="/gym-plans",
    tags=["Gym Plans"],
)

@router.get("", response_model=list[PlanResponse])
def get_gym_plans(
    keyword: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = Query(None, max_length=100),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    filters = PlanFilter(
        keyword=keyword,
        category=category,
        status=PlanStatus.ACTIVE,
        min_price=min_price,
        max_price=max_price,
    )
    return membership_plan_service.get_all_membership_plans(db, filters)
@router.get("/{plan_id}", response_model=PlanResponse)
def get_membership_plan_detail(
    plan_id: int,
    db: Session = Depends(get_db)
):
    plan = membership_plan_service.get_membership_plan_by_id(db, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Membership plan not found"
        )
    return plan

@router.post("/", response_model=PlanResponse, status_code=201)
def create_membership_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    new_plan = membership_plan_service.create_membership_plan(db, plan_data)
    return new_plan

@router.put("/{plan_id}", response_model=PlanResponse)
def update_membership_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    updated_plan = membership_plan_service.update_membership_plan(db, plan_id, plan_data)
    return updated_plan

@router.delete("/{plan_id}", response_model=PlanResponse)
def discontinue_membership_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    discontinued_plan = membership_plan_service.discontinue_membership_plan(db, plan_id)
    return discontinued_plan