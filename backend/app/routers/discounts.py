from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exception import BusinessRuleException, ConflictException, NotFoundException
from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.discount import Discount
from app.models.user import User

router = APIRouter(prefix="/discounts", tags=["Discounts & Vouchers"])


class DiscountCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    description: Optional[str] = None
    discount_type: str = Field(default="PERCENT", description="PERCENT hoặc FIXED")
    discount_value: Decimal = Field(gt=0)
    min_order_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_discount_amount: Optional[Decimal] = Field(default=None, gt=0)
    start_date: Optional[date] = None
    expiry_date: date
    usage_limit: int = Field(default=100, gt=0)
    is_active: bool = True


class DiscountUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = Field(default=None, gt=0)
    min_order_amount: Optional[Decimal] = Field(default=None, ge=0)
    max_discount_amount: Optional[Decimal] = None
    expiry_date: Optional[date] = None
    usage_limit: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


class DiscountValidateRequest(BaseModel):
    code: str
    order_amount: Decimal = Field(ge=0)


def _serialize_discount(d: Discount) -> dict[str, Any]:
    today = date.today()
    is_expired = d.expiry_date < today
    is_exhausted = d.used_count >= d.usage_limit
    return {
        "discount_id": d.discount_id,
        "code": d.code,
        "description": d.description,
        "discount_type": d.discount_type,
        "discount_value": d.discount_value,
        "min_order_amount": d.min_order_amount,
        "max_discount_amount": d.max_discount_amount,
        "start_date": d.start_date,
        "expiry_date": d.expiry_date,
        "usage_limit": d.usage_limit,
        "used_count": d.used_count,
        "remaining_uses": max(0, d.usage_limit - d.used_count),
        "is_active": d.is_active and not is_expired and not is_exhausted,
        "status_label": (
            "ĐANG HOẠT ĐỘNG"
            if (d.is_active and not is_expired and not is_exhausted)
            else ("HẾT HẠN" if is_expired else ("HẾT LƯỢT" if is_exhausted else "TẠM NGƯNG"))
        ),
        "created_at": d.created_at,
    }


@router.get("", summary="[Task T067E76] Danh sách mã giảm giá / Voucher")
def list_discounts(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    items = db.query(Discount).order_by(Discount.discount_id.desc()).all()
    return [_serialize_discount(d) for d in items]


@router.post(
    "/validate",
    summary="[Task T067E76] Kiểm tra mã giảm giá và tính số tiền được giảm cho POS",
)
def validate_discount_code(
    payload: DiscountValidateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    clean_code = payload.code.strip().upper()
    disc = db.query(Discount).filter(Discount.code == clean_code).first()
    if not disc:
        raise NotFoundException(f"Mã voucher '{clean_code}' không tồn tại.")

    today = date.today()
    if not disc.is_active:
        raise BusinessRuleException(f"Mã voucher '{clean_code}' đang tạm ngưng áp dụng.")
    if disc.expiry_date < today:
        raise BusinessRuleException(
            f"Mã voucher '{clean_code}' đã hết hạn từ ngày {disc.expiry_date.strftime('%d/%m/%Y')}."
        )
    if disc.used_count >= disc.usage_limit:
        raise BusinessRuleException(f"Mã voucher '{clean_code}' đã hết lượt sử dụng.")
    if payload.order_amount < disc.min_order_amount:
        raise BusinessRuleException(
            f"Đơn hàng cần tối thiểu {int(disc.min_order_amount):,} đ để áp dụng mã '{clean_code}'."
        )

    if disc.discount_type == "PERCENT":
        discount_amount = (payload.order_amount * disc.discount_value) / Decimal("100")
        if disc.max_discount_amount and discount_amount > disc.max_discount_amount:
            discount_amount = disc.max_discount_amount
    else:
        discount_amount = min(payload.order_amount, disc.discount_value)

    discount_amount = round(discount_amount, 2)
    final_amount = max(Decimal("0.00"), payload.order_amount - discount_amount)

    return {
        "valid": True,
        "code": disc.code,
        "description": disc.description,
        "discount_type": disc.discount_type,
        "discount_value": disc.discount_value,
        "order_amount": payload.order_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "message": f"Áp dụng mã {disc.code} thành công! Giảm {int(discount_amount):,} đ.",
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Tạo mã giảm giá / Voucher mới",
)
def create_discount(
    payload: DiscountCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    clean_code = payload.code.strip().upper()
    existing = db.query(Discount).filter(Discount.code == clean_code).first()
    if existing:
        raise ConflictException(f"Mã voucher '{clean_code}' đã tồn tại.")

    dtype = payload.discount_type.strip().upper()
    if dtype not in ("PERCENT", "FIXED"):
        raise BusinessRuleException("Loại giảm giá chỉ nhận PERCENT hoặc FIXED.")
    if dtype == "PERCENT" and payload.discount_value > 100:
        raise BusinessRuleException("Mức giảm theo % không được vượt quá 100%.")

    disc = Discount(
        code=clean_code,
        description=payload.description,
        discount_type=dtype,
        discount_value=payload.discount_value,
        min_order_amount=payload.min_order_amount,
        max_discount_amount=payload.max_discount_amount,
        start_date=payload.start_date or date.today(),
        expiry_date=payload.expiry_date,
        usage_limit=payload.usage_limit,
        used_count=0,
        is_active=payload.is_active,
    )
    db.add(disc)
    db.commit()
    db.refresh(disc)
    return _serialize_discount(disc)


@router.put("/{discount_id}", summary="[ADMIN] Cập nhật mã giảm giá")
def update_discount(
    discount_id: int,
    payload: DiscountUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    disc = db.query(Discount).filter(Discount.discount_id == discount_id).first()
    if not disc:
        raise NotFoundException(f"Không tìm thấy voucher #{discount_id}.")

    data = payload.model_dump(exclude_unset=True)
    effective_type = disc.discount_type
    if "discount_type" in data and data["discount_type"]:
        dtype = data["discount_type"].strip().upper()
        if dtype not in ("PERCENT", "FIXED"):
            raise BusinessRuleException("Loại giảm giá chỉ nhận PERCENT hoặc FIXED.")
        effective_type = dtype
        disc.discount_type = dtype

    effective_val = data.get("discount_value", disc.discount_value)
    if effective_type == "PERCENT" and effective_val is not None and effective_val > 100:
        raise BusinessRuleException("Mức giảm theo % không được vượt quá 100%.")
    for field in (
        "description",
        "discount_value",
        "min_order_amount",
        "max_discount_amount",
        "expiry_date",
        "usage_limit",
        "is_active",
    ):
        if field in data:
            setattr(disc, field, data[field])

    db.commit()
    db.refresh(disc)
    return _serialize_discount(disc)


@router.delete("/{discount_id}", summary="[ADMIN] Xóa / Vô hiệu hóa mã giảm giá")
def delete_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    disc = db.query(Discount).filter(Discount.discount_id == discount_id).first()
    if not disc:
        raise NotFoundException(f"Không tìm thấy voucher #{discount_id}.")
    db.delete(disc)
    db.commit()
    return {"message": f"Đã xóa voucher {disc.code} thành công.", "discount_id": discount_id}
