from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exception import BusinessRuleException, ConflictException, NotFoundException
from app.db.database import get_db
from app.dependencies.auth import require_admin, require_staff_or_admin
from app.models.equipment import Equipment
from app.models.user import User

router = APIRouter(prefix="/equipment", tags=["Equipment & Maintenance"])

VALID_EQUIPMENT_STATUSES = {
    "HOAT_DONG": "HOẠT ĐỘNG",
    "HOẠT ĐỘNG": "HOAT_DONG",
    "BAO_TRI": "BẢO TRÌ",
    "BẢO TRÌ": "BAO_TRI",
    "HONG": "HỎNG",
    "HỎNG": "HONG",
}


def normalize_equipment_status(raw: str) -> str:
    val = raw.strip().upper()
    if val in ("HOAT_DONG", "HOẠT ĐỘNG", "ACTIVE"):
        return "HOAT_DONG"
    if val in ("BAO_TRI", "BẢO TRÌ", "MAINTENANCE"):
        return "BAO_TRI"
    if val in ("HONG", "HỎNG", "BROKEN"):
        return "HONG"
    raise BusinessRuleException(
        "Trạng thái thiết bị không hợp lệ (chỉ chấp nhận HOẠT ĐỘNG, BẢO TRÌ, HỎNG)."
    )


def serialize_equipment(eq: Equipment) -> dict[str, Any]:
    today = date.today()
    days_until_due = (
        (eq.next_maintenance_date - today).days if eq.next_maintenance_date else None
    )
    status_label = {
        "HOAT_DONG": "HOẠT ĐỘNG",
        "BAO_TRI": "BẢO TRÌ",
        "HONG": "HỎNG",
    }.get(eq.status, eq.status)
    return {
        "equipment_id": eq.equipment_id,
        "name": eq.name,
        "zone": eq.zone,
        "status": eq.status,
        "status_label": status_label,
        "purchase_date": eq.purchase_date,
        "last_maintained_at": eq.last_maintained_at,
        "maintenance_interval_days": eq.maintenance_interval_days,
        "next_maintenance_date": eq.next_maintenance_date,
        "days_until_maintenance": days_until_due,
        "is_maintenance_due": days_until_due is not None and days_until_due <= 7,
        "is_overdue": days_until_due is not None and days_until_due < 0,
        "notes": eq.notes,
        "created_at": eq.created_at,
        "updated_at": eq.updated_at,
    }


class EquipmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    zone: str = Field(min_length=2, max_length=100)
    status: str = Field(default="HOAT_DONG")
    purchase_date: Optional[date] = None
    last_maintained_at: Optional[date] = None
    maintenance_interval_days: int = Field(default=30, gt=0, le=365)
    next_maintenance_date: Optional[date] = None
    notes: Optional[str] = None


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    zone: Optional[str] = Field(default=None, min_length=2, max_length=100)
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    last_maintained_at: Optional[date] = None
    maintenance_interval_days: Optional[int] = Field(default=None, gt=0, le=365)
    next_maintenance_date: Optional[date] = None
    notes: Optional[str] = None


@router.get("", summary="Danh sách thiết bị phòng gym & trạng thái bảo trì")
def list_equipment(
    zone: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    due_within_days: Optional[int] = Query(default=None, ge=0, le=90),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    query = db.query(Equipment)
    if zone and zone.strip():
        query = query.filter(Equipment.zone.ilike(f"%{zone.strip()}%"))
    if status_filter and status_filter.strip():
        norm_st = normalize_equipment_status(status_filter)
        query = query.filter(Equipment.status == norm_st)

    items = query.order_by(Equipment.equipment_id.asc()).all()
    serialized = [serialize_equipment(eq) for eq in items]
    if due_within_days is not None:
        serialized = [
            item
            for item in serialized
            if item["days_until_maintenance"] is not None
            and item["days_until_maintenance"] <= due_within_days
        ]

    due_7_days = [
        item
        for item in [serialize_equipment(eq) for eq in items]
        if item["is_maintenance_due"]
    ]
    return {
        "items": serialized,
        "total": len(serialized),
        "maintenance_due_count": len(due_7_days),
    }


@router.get(
    "/maintenance-due",
    summary="[Bonus T3CD423] Danh sách thiết bị đến hạn bảo trì trong 7 ngày tới",
)
def get_maintenance_due_equipment(
    days: int = Query(default=7, ge=1, le=60),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    cutoff = date.today() + timedelta(days=days)
    items = (
        db.query(Equipment)
        .filter(
            Equipment.next_maintenance_date.isnot(None),
            Equipment.next_maintenance_date <= cutoff,
        )
        .order_by(Equipment.next_maintenance_date.asc())
        .all()
    )
    serialized = [serialize_equipment(eq) for eq in items]
    return {
        "due_count": len(serialized),
        "days_window": days,
        "items": serialized,
    }


@router.get("/{equipment_id}", summary="Xem chi tiết thiết bị")
def get_equipment(equipment_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    eq = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if not eq:
        raise NotFoundException(f"Không tìm thấy thiết bị có ID {equipment_id}.")
    return serialize_equipment(eq)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Thêm thiết bị mới (tên không trùng)",
)
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    clean_name = payload.name.strip()
    existing = db.query(Equipment).filter(Equipment.name == clean_name).first()
    if existing:
        raise ConflictException("Tên thiết bị đã tồn tại trong hệ thống.")

    norm_status = normalize_equipment_status(payload.status)
    today = date.today()
    last_maint = payload.last_maintained_at or today
    next_maint = payload.next_maintenance_date or (
        last_maint + timedelta(days=payload.maintenance_interval_days)
    )

    eq = Equipment(
        name=clean_name,
        zone=payload.zone.strip(),
        status=norm_status,
        purchase_date=payload.purchase_date or today,
        last_maintained_at=last_maint,
        maintenance_interval_days=payload.maintenance_interval_days,
        next_maintenance_date=next_maint,
        notes=payload.notes,
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return serialize_equipment(eq)


@router.put("/{equipment_id}", summary="[ADMIN] Cập nhật thiết bị & chu kỳ bảo trì")
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    eq = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if not eq:
        raise NotFoundException(f"Không tìm thấy thiết bị có ID {equipment_id}.")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        clean_name = data["name"].strip()
        dup = (
            db.query(Equipment)
            .filter(
                Equipment.name == clean_name,
                Equipment.equipment_id != equipment_id,
            )
            .first()
        )
        if dup:
            raise ConflictException("Tên thiết bị đã được sử dụng.")
        eq.name = clean_name

    if "zone" in data and data["zone"]:
        eq.zone = data["zone"].strip()
    if "status" in data and data["status"]:
        eq.status = normalize_equipment_status(data["status"])
    if "purchase_date" in data:
        eq.purchase_date = data["purchase_date"]
    if "last_maintained_at" in data and data["last_maintained_at"]:
        eq.last_maintained_at = data["last_maintained_at"]
    if "maintenance_interval_days" in data and data["maintenance_interval_days"]:
        eq.maintenance_interval_days = data["maintenance_interval_days"]
    if "next_maintenance_date" in data and data["next_maintenance_date"]:
        eq.next_maintenance_date = data["next_maintenance_date"]
    elif "last_maintained_at" in data or "maintenance_interval_days" in data:
        base_dt = eq.last_maintained_at or date.today()
        eq.next_maintenance_date = base_dt + timedelta(days=eq.maintenance_interval_days)
    if "notes" in data:
        eq.notes = data["notes"]

    db.commit()
    db.refresh(eq)
    return serialize_equipment(eq)


@router.post(
    "/{equipment_id}/maintain",
    summary="[Bonus T3CD423] Ghi nhận hoàn thành bảo trì định kỳ hôm nay",
)
def mark_equipment_maintained(
    equipment_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    eq = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if not eq:
        raise NotFoundException(f"Không tìm thấy thiết bị có ID {equipment_id}.")

    today = date.today()
    eq.last_maintained_at = today
    eq.next_maintenance_date = today + timedelta(days=eq.maintenance_interval_days)
    eq.status = "HOAT_DONG"
    db.commit()
    db.refresh(eq)
    return serialize_equipment(eq)


@router.delete("/{equipment_id}", summary="[ADMIN] Xóa thiết bị")
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    eq = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if not eq:
        raise NotFoundException(f"Không tìm thấy thiết bị có ID {equipment_id}.")
    db.delete(eq)
    db.commit()
    return {"message": f"Đã xóa thiết bị {eq.name} thành công.", "equipment_id": equipment_id}
