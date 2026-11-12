
from sqlalchemy.orm import Session

from app.models.membership_plan import MembershipPlan
from app.schemas.membership_plan import PlanFilter,PlanStatus
from fastapi import HTTPException


def get_all_membership_plans(db: Session,filters: PlanFilter,):
    query = db.query(MembershipPlan)
    # Chỉ lấy gói tập đang hoạt động nếu có truyền status
    if filters.status:
        query = query.filter(MembershipPlan.status == filters.status)
    # Tìm kiếm theo tên gói tập
    if filters.keyword:
        query = query.filter(MembershipPlan.plan_name.ilike(f"%{filters.keyword.strip()}%"))
    # Lọc theo danh mục
    if filters.category:
        query = query.filter(MembershipPlan.category == filters.category)
    # Lọc theo giá hấp nhất
    if filters.min_price is not None:
        query = query.filter(MembershipPlan.price >= filters.min_price)
    # Lọc theo giá cao nhất
    if filters.max_price is not None:
        query = query.filter(MembershipPlan.price <= filters.max_price)
    return (
        query.order_by(MembershipPlan.plan_id.desc()).all())

def get_membership_plan_by_id(db, plan_id: int):
    return (db.query(MembershipPlan).filter(MembershipPlan.plan_id == plan_id).first())
def create_membership_plan(db, plan_data):
    #kiểm tra tên gói tập đã tồn tại chưa
    existing_plan = (
        db.query(MembershipPlan).filter(MembershipPlan.plan_name == plan_data.plan_name).first())
    if existing_plan is not None:
        raise HTTPException(
            status_code=409,
            detail="Membership plan name already exists"
        )
    #kiểm tra giá phải lớn hơn 0
    if plan_data.price <= 0:
        raise HTTPException(
            status_code=422,
            detail="Price must be greater than 0"
        )
    #lấy dữ liệu từ request
    data = plan_data.model_dump()
    #tạo đối tượng MembershipPlan
    new_plan = MembershipPlan(
        plan_name=data["plan_name"],
        category=data["category"],
        duration_days=data["duration_days"],
        price=data["price"],
        description=data["description"],
        status=data["status"]
    )
    #lưu vào database
    db.add(new_plan)
    db.commit()
    #lấy dữ liệu vừa lưu
    db.refresh(new_plan)
    return new_plan

def update_membership_plan(db, plan_id: int, plan_data):
    #tìm gói tập theo ID
    existing_plan = (db.query(MembershipPlan).filter(MembershipPlan.plan_id == plan_id).first())
    #kiểm tra gói tập có tồn tại không
    if existing_plan is None:
        raise HTTPException(
            status_code=404,
            detail="Membership plan not found"
        )
    #lấy dữ liệu được gửi lên
    data = plan_data.model_dump(exclude_unset=True)
    #kiểm tra tên mới có bị trùng không
    if "plan_name" in data:
        duplicated_plan = (
            db.query(MembershipPlan).filter(MembershipPlan.plan_name == data["plan_name"],MembershipPlan.plan_id != plan_id).first())
        if duplicated_plan is not None:
            raise HTTPException(
                status_code=409,
                detail="Membership plan name already exists"
            )
    #kiểm tra giá
    if "price" in data and data["price"] <= 0:
        raise HTTPException(
            status_code=422,
            detail="Price must be greater than 0"
        )
    #cập nhật từng trường
    if "plan_name" in data:
        existing_plan.plan_name = data["plan_name"]
    if "category" in data:
        existing_plan.category = data["category"]
    if "duration_days" in data:
        existing_plan.duration_days = data["duration_days"]
    if "price" in data:
        existing_plan.price = data["price"]
    if "description" in data:
        existing_plan.description = data["description"]
    #lưu thay đổi
    db.commit()
    db.refresh(existing_plan)
    return existing_plan

def discontinue_membership_plan(db, plan_id: int):
    #tìm gói tập theo ID
    existing_plan = (db.query(MembershipPlan).filter(MembershipPlan.plan_id == plan_id).first())
    #kiểm tra gói tập có tồn tại không
    if existing_plan is None:
        raise HTTPException(
            status_code=404,
            detail="Membership plan not found"
        )
    #chuyển trạng thái gói tập
    existing_plan.status = PlanStatus.DISCONTINUED
    #lưu thay đổi vào database
    db.commit()
    #làm mới dữ liệu
    db.refresh(existing_plan)
    return existing_plan
