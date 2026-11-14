from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exception import BusinessRuleException, ConflictException, NotFoundException
from app.models.enums import PlanStatus
from app.models.membership_plan import MembershipPlan
from app.schemas.common import PageParams
from app.schemas.membership_plan import PlanCreate, PlanFilter, PlanUpdate


def get_membership_plans(
    db: Session,
    filters: PlanFilter,
    page_params: PageParams,
) -> tuple[list[MembershipPlan], int]:
    """Lấy danh sách gói đang kinh doanh, hỗ trợ tìm kiếm, lọc và phân trang."""
    query = db.query(MembershipPlan).filter(
        MembershipPlan.status == PlanStatus.ACTIVE
    )

    if filters.keyword:
        keyword = filters.keyword.strip()
        query = query.filter(MembershipPlan.plan_name.ilike(f"%{keyword}%"))

    if filters.category:
        query = query.filter(MembershipPlan.category == filters.category.strip())

    if filters.min_price is not None:
        query = query.filter(MembershipPlan.price >= filters.min_price)

    if filters.max_price is not None:
        query = query.filter(MembershipPlan.price <= filters.max_price)

    total = query.count()
    items = (
        query.order_by(MembershipPlan.plan_id.desc())
        .offset(page_params.offset)
        .limit(page_params.size)
        .all()
    )
    return items, total


def get_membership_plan_by_id(db: Session, plan_id: int) -> MembershipPlan:
    """Lấy chi tiết theo ID; vẫn cho phép xem gói đã ngừng kinh doanh."""
    plan = db.query(MembershipPlan).filter(
        MembershipPlan.plan_id == plan_id
    ).first()

    if plan is None:
        raise NotFoundException(message=f"Không tìm thấy gói tập có ID {plan_id}.")

    return plan


def create_membership_plan(db: Session, plan_data: PlanCreate) -> MembershipPlan:
    """Tạo gói tập mới."""
    existing_plan = db.query(MembershipPlan).filter(
        MembershipPlan.plan_name == plan_data.plan_name
    ).first()

    if existing_plan:
        raise ConflictException(message="Tên gói tập đã tồn tại.")

    new_plan = MembershipPlan(**plan_data.model_dump())
    db.add(new_plan)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException(message="Tên gói tập đã tồn tại hoặc dữ liệu bị xung đột.")

    db.refresh(new_plan)
    return new_plan


def update_membership_plan(
    db: Session,
    plan_id: int,
    plan_data: PlanUpdate,
) -> MembershipPlan:
    """Cập nhật các trường được gửi lên; không cập nhật status tại API này."""
    plan = get_membership_plan_by_id(db, plan_id)
    update_data = plan_data.model_dump(exclude_unset=True)

    # Các cột này không nullable trong Model của nhóm.
    for field in ("plan_name", "category", "duration_days", "price"):
        if field in update_data and update_data[field] is None:
            raise BusinessRuleException(
                message=f"Trường {field} không được để trống.",
                rule_code="INVALID_PLAN_FIELD",
            )

    if "plan_name" in update_data:
        duplicated_plan = (
            db.query(MembershipPlan)
            .filter(
                MembershipPlan.plan_name == update_data["plan_name"],
                MembershipPlan.plan_id != plan_id,
            )
            .first()
        )
        if duplicated_plan:
            raise ConflictException(message="Tên gói tập đã được sử dụng.")

    for field, value in update_data.items():
        setattr(plan, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException(message="Tên gói tập đã tồn tại hoặc dữ liệu bị xung đột.")

    db.refresh(plan)
    return plan


def discontinue_membership_plan(db: Session, plan_id: int) -> MembershipPlan:
    """Ngừng kinh doanh gói tập (soft delete), không xóa bản ghi khỏi CSDL."""
    plan = get_membership_plan_by_id(db, plan_id)

    if plan.status == PlanStatus.DISCONTINUED:
        return plan

    plan.status = PlanStatus.DISCONTINUED

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException(message="Không thể ngừng kinh doanh gói tập này.")

    db.refresh(plan)
    return plan
