import csv
import io
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.seed import ensure_sql_views
from app.dependencies.auth import require_admin, require_staff_or_admin
from app.models.attendance_record import AttendanceRecord
from app.models.enums import (
    AttendanceStatus,
    InvoiceStatus,
    SubscriptionStatus,
    SubscriptionType,
)
from app.models.equipment import Equipment
from app.models.invoice import Invoice
from app.models.member import Member
from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard KPI & Reports"])


@router.get(
    "/summary",
    summary="[Task T067E76 & T067D16] Thống kê KPI Dashboard, doanh thu tháng & cơ cấu gói tập (từ SQL View)",
)
def get_dashboard_summary(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff_or_admin),
) -> dict[str, Any]:
    ensure_sql_views(db)
    today = date.today()
    current_month_str = today.strftime("%Y-%m")

    # 1. Truy vấn từ SQL Views của TV1 (Task T067D16)
    monthly_revenue_rows = db.execute(
        text("SELECT revenue_month, invoice_count, gross_revenue, total_discount, net_revenue FROM vw_monthly_revenue ORDER BY revenue_month ASC LIMIT 12")
    ).mappings().all()

    daily_revenue_rows = db.execute(
        text("SELECT revenue_date, invoice_count, gross_revenue, total_discount, net_revenue FROM vw_daily_revenue ORDER BY revenue_date DESC LIMIT 30")
    ).mappings().all()

    top_plans_rows = db.execute(
        text("SELECT plan_id, plan_name, category, duration_days, price, total_subscriptions, active_subscriptions, total_revenue FROM vw_top_gym_plans ORDER BY total_subscriptions DESC, total_revenue DESC, plan_id ASC")
    ).mappings().all()

    monthly_members_rows = db.execute(
        text("SELECT join_month, new_members_count FROM vw_monthly_new_members ORDER BY join_month ASC LIMIT 12")
    ).mappings().all()

    # 2. Tính KPI tổng hợp (có hỗ trợ bộ lọc khoảng ngày from_date / to_date)
    inv_query = db.query(Invoice).filter(Invoice.status == InvoiceStatus.PAID)
    if from_date:
        inv_query = inv_query.filter(
            Invoice.created_at >= datetime.combine(from_date, datetime.min.time())
        )
    if to_date:
        inv_query = inv_query.filter(
            Invoice.created_at <= datetime.combine(to_date, datetime.max.time())
        )

    filtered_revenue = sum((float(i.final_amount) for i in inv_query.all()), 0.0)

    # Doanh thu tháng hiện tại
    current_month_revenue = 0.0
    for r in monthly_revenue_rows:
        if r["revenue_month"] == current_month_str:
            current_month_revenue = float(r["net_revenue"] or 0)

    if current_month_revenue == 0.0 and filtered_revenue > 0:
        current_month_revenue = filtered_revenue

    # Hội viên mới trong tháng & tổng hội viên
    total_members = db.query(func.count(Member.member_id)).scalar() or 0
    month_start = today.replace(day=1)
    new_members_this_month = (
        db.query(func.count(Member.member_id))
        .filter(Member.join_date >= month_start)
        .scalar()
        or 0
    )

    # Tỷ lệ gia hạn (Renewal Rate)
    total_subs = db.query(func.count(Subscription.subscription_id)).scalar() or 0
    renew_subs = (
        db.query(func.count(Subscription.subscription_id))
        .filter(Subscription.subscription_type == SubscriptionType.RENEW)
        .scalar()
        or 0
    )
    active_subs_count = (
        db.query(func.count(Subscription.subscription_id))
        .filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date >= today,
        )
        .scalar()
        or 0
    )
    renewal_rate = round((renew_subs / total_subs) * 100, 1) if total_subs > 0 else 0.0

    # Số hội viên đang tập tại phòng & thiết bị đến hạn bảo trì trong 7 ngày
    active_in_gym = (
        db.query(func.count(AttendanceRecord.attendance_id))
        .filter(
            AttendanceRecord.status == AttendanceStatus.CHECKED_IN,
            AttendanceRecord.check_out.is_(None),
        )
        .scalar()
        or 0
    )
    maintenance_due_7d = (
        db.query(func.count(Equipment.equipment_id))
        .filter(
            Equipment.next_maintenance_date.isnot(None),
            Equipment.next_maintenance_date <= today + timedelta(days=7),
        )
        .scalar()
        or 0
    )

    return {
        "kpis": {
            "monthly_revenue": current_month_revenue,
            "filtered_revenue": filtered_revenue,
            "total_members": total_members,
            "new_members_this_month": new_members_this_month,
            "active_subscriptions": active_subs_count,
            "renewal_rate_pct": renewal_rate,
            "active_in_gym_count": active_in_gym,
            "maintenance_due_count": maintenance_due_7d,
        },
        "monthly_revenue_chart": [
            {
                "month": r["revenue_month"],
                "invoice_count": int(r["invoice_count"] or 0),
                "gross_revenue": float(r["gross_revenue"] or 0),
                "total_discount": float(r["total_discount"] or 0),
                "net_revenue": float(r["net_revenue"] or 0),
            }
            for r in monthly_revenue_rows
        ],
        "daily_revenue": [
            {
                "date": str(r["revenue_date"]),
                "invoice_count": int(r["invoice_count"] or 0),
                "net_revenue": float(r["net_revenue"] or 0),
            }
            for r in daily_revenue_rows
        ],
        "plan_breakdown_chart": [
            {
                "plan_id": int(r["plan_id"]),
                "plan_name": r["plan_name"],
                "category": r["category"],
                "price": float(r["price"] or 0),
                "total_subscriptions": int(r["total_subscriptions"] or 0),
                "active_subscriptions": int(r["active_subscriptions"] or 0),
                "total_revenue": float(r["total_revenue"] or 0),
            }
            for r in top_plans_rows
        ],
        "monthly_new_members": [
            {
                "month": r["join_month"],
                "new_members": int(r["new_members_count"] or 0),
            }
            for r in monthly_members_rows
        ],
    }


@router.get(
    "/export-csv",
    summary="[Bonus T3CD54C - ADMIN] Xuất báo cáo doanh thu theo ngày & danh sách hóa đơn ra file CSV",
)
def export_revenue_and_invoices_csv(
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> StreamingResponse:
    ensure_sql_views(db)

    output = io.StringIO()
    # Ghi BOM UTF-8 để mở bằng Microsoft Excel không bị lỗi font tiếng Việt
    output.write("\ufeff")
    writer = csv.writer(output)

    # Phần 1: Doanh thu theo ngày
    writer.writerow(["=== BÁO CÁO DOANH THU THEO NGÀY (DUCKY GYM) ==="])
    writer.writerow(["Ngày", "Số hóa đơn", "Tổng tiền gốc (VNĐ)", "Giảm giá (VNĐ)", "Doanh thu thực thu (VNĐ)"])

    daily_rows = db.execute(
        text("SELECT revenue_date, invoice_count, gross_revenue, total_discount, net_revenue FROM vw_daily_revenue ORDER BY revenue_date DESC")
    ).mappings().all()

    for dr in daily_rows:
        r_date = dr["revenue_date"]
        if from_date and r_date < from_date:
            continue
        if to_date and r_date > to_date:
            continue
        writer.writerow([
            str(r_date),
            int(dr["invoice_count"] or 0),
            int(float(dr["gross_revenue"] or 0)),
            int(float(dr["total_discount"] or 0)),
            int(float(dr["net_revenue"] or 0)),
        ])

    writer.writerow([])
    # Phần 2: Danh sách hóa đơn chi tiết
    writer.writerow(["=== DANH SÁCH HÓA ĐƠN CHI TIẾT ==="])
    writer.writerow([
        "Mã Hóa Đơn",
        "Ngày Tạo",
        "Hội Viên",
        "Số Điện Thoại",
        "Gói Tập",
        "Loại Đăng Ký",
        "Tổng Tiền (VNĐ)",
        "Giảm Giá (VNĐ)",
        "Thực Thu (VNĐ)",
        "Phương Thức",
        "Trạng Thái",
    ])

    inv_query = (
        db.query(Invoice, Member, Subscription, MembershipPlan)
        .join(Member, Member.member_id == Invoice.member_id)
        .join(Subscription, Subscription.subscription_id == Invoice.subscription_id)
        .join(MembershipPlan, MembershipPlan.plan_id == Subscription.plan_id)
    )
    if from_date:
        inv_query = inv_query.filter(
            Invoice.created_at >= datetime.combine(from_date, datetime.min.time())
        )
    if to_date:
        inv_query = inv_query.filter(
            Invoice.created_at <= datetime.combine(to_date, datetime.max.time())
        )

    for inv, mem, sub, plan in inv_query.order_by(Invoice.created_at.desc()).all():
        pay = db.query(Payment).filter(Payment.invoice_id == inv.invoice_id).first()
        writer.writerow([
            f"INV-{inv.invoice_id:06d}",
            inv.created_at.strftime("%Y-%m-%d %H:%M"),
            mem.full_name,
            mem.phone,
            plan.plan_name,
            sub.subscription_type.value,
            int(float(inv.total_amount)),
            int(float(inv.discount_amount)),
            int(float(inv.final_amount)),
            pay.payment_method.value if pay else "CASH",
            inv.status.value,
        ])

    output.seek(0)
    filename = f"duckygym_baocao_doanhthu_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
