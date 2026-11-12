from decimal import Decimal

from models.enums import MemberStatus, PlanStatus, UserRole
from schemas.common import ORMModel


class UserSummary(ORMModel):
    user_id: int
    full_name: str
    role: UserRole


class MemberSummary(ORMModel):
    member_id: int
    full_name: str
    phone: str
    status: MemberStatus


class PlanSummary(ORMModel):
    plan_id: int
    plan_name: str
    category: str
    duration_days: int
    price: Decimal
    status: PlanStatus
