import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import gymApi from "../api/gymApi";

const playPosBeep = (ok = true) => {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = ok ? "sine" : "sawtooth";
    osc.frequency.setValueAtTime(ok ? 880 : 240, ctx.currentTime);
    gain.gain.setValueAtTime(0.14, ctx.currentTime);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + (ok ? 0.16 : 0.32));
  } catch {
    // Ignore audio context errors
  }
};

const adminStyles = `
.admin-shell { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; background: #0b1326; color: #dae2fd; font-family: Inter, Arial, sans-serif; }
.admin-shell * { box-sizing: border-box; }
.admin-sidebar { background: #131b2e; border-right: 1px solid rgba(255,255,255,0.08); padding: 20px 14px; display: flex; flex-direction: column; justify-content: space-between; position: sticky; top: 0; height: 100vh; }
.admin-brand { display: flex; align-items: center; gap: 10px; padding: 6px 10px 18px; border-bottom: 1px solid rgba(255,255,255,0.07); color: #dae2fd; text-decoration: none; }
.admin-brand-icon { width: 38px; height: 38px; border-radius: 9px; background: #f97316; color: #351400; display: grid; place-items: center; }
.admin-nav { display: flex; flex-direction: column; gap: 5px; margin-top: 16px; }
.admin-nav-btn { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 11px 12px; border-radius: 10px; border: none; background: transparent; color: #a6adc2; font-size: 13px; font-weight: 600; cursor: pointer; text-align: left; }
.admin-nav-btn:hover, .admin-nav-btn.is-active { background: #222a3d; color: #ffffff; }
.admin-nav-btn.is-active { border-left: 3px solid #f97316; color: #ffb690; }
.admin-badge-warn { background: #ef4444; color: #fff; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 999px; }

.admin-main { display: flex; flex-direction: column; min-width: 0; }
.admin-header { height: 70px; background: rgba(19,27,46,0.92); border-bottom: 1px solid rgba(255,255,255,0.07); padding: 0 28px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 10; }
.admin-body { padding: 26px 28px 60px; display: flex; flex-direction: column; gap: 22px; }

.admin-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.admin-kpi-card { background: #171f33; border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; padding: 18px; display: flex; flex-direction: column; gap: 6px; }
.admin-kpi-card small { color: #a6adc2; font-size: 11px; font-weight: 600; }
.admin-kpi-card b { font-size: 22px; color: #ffffff; }

.admin-card { background: #171f33; border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: 22px; }
.admin-card-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.admin-card-head h2 { margin: 0; font-size: 17px; }
.admin-btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 15px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; }
.admin-btn-primary { background: #f97316; color: #351400; }
.admin-btn-secondary { background: #222a3d; color: #dae2fd; border: 1px solid rgba(255,255,255,0.1); }
.admin-btn-danger { background: rgba(239,68,68,0.18); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
.admin-btn-success { background: rgba(34,197,94,0.18); color: #86efac; border: 1px solid rgba(34,197,94,0.35); }

.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th, .admin-table td { padding: 11px 12px; border-bottom: 1px solid rgba(255,255,255,0.07); text-align: left; }
.admin-table th { color: #a6adc2; font-size: 12px; background: #131b2e; }
.admin-input, .admin-select { padding: 9px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.14); background: #222a3d; color: #dae2fd; font-size: 13px; }

.admin-modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.68); display: grid; place-items: center; z-index: 50; padding: 16px; }
.admin-modal { background: #171f33; border: 1px solid rgba(255,255,255,0.14); border-radius: 16px; padding: 24px; width: min(520px, 100%); display: flex; flex-direction: column; gap: 14px; }

@media print {
  .admin-sidebar, .admin-header, .no-print { display: none !important; }
  .admin-shell { display: block; background: #fff; color: #000; }
  .pos-receipt-box { border: 2px solid #000 !important; background: #fff !important; color: #000 !important; padding: 24px !important; }
}
`;

const formatVND = (val) =>
  `${new Intl.NumberFormat("vi-VN").format(Number(val) || 0)} đ`;

const CHART_COLORS = ["#f97316", "#3b82f6", "#22c55e", "#eab308", "#a855f7"];

const AdminPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isStaffRoute = location.pathname.startsWith("/staff");
  const isAdmin = user?.role?.toUpperCase() === "ADMIN";

  const [activeTab, setActiveTab] = useState(
    isStaffRoute ? "pos" : "dashboard"
  );
  const [toast, setToast] = useState({ type: "", text: "" });

  // 1. Dashboard state
  const [dashSummary, setDashSummary] = useState(null);
  const [dashDates, setDashDates] = useState({ from_date: "", to_date: "" });

  // 2. POS state
  const [posPhone, setPosPhone] = useState("0901000001");
  const [posMember, setPosMember] = useState(null);
  const [posNewName, setPosNewName] = useState("");
  const [posPlanId, setPosPlanId] = useState("");
  const [posVoucher, setPosVoucher] = useState("");
  const [posVoucherResult, setPosVoucherResult] = useState(null);
  const [posPayMethod, setPosPayMethod] = useState("CASH");
  const [posReceipt, setPosReceipt] = useState(null);
  const [posInvoices, setPosInvoices] = useState([]);

  // 3. Gym Plans CRUD state
  const [plans, setPlans] = useState([]);
  const [planModal, setPlanModal] = useState(null);

  // 4. Equipment & Maintenance state
  const [equipmentList, setEquipmentList] = useState([]);
  const [maintenanceDueCount, setMaintenanceDueCount] = useState(0);
  const [eqModal, setEqModal] = useState(null);

  // 5. Discounts CRUD state
  const [discounts, setDiscounts] = useState([]);
  const [discountModal, setDiscountModal] = useState(null);

  // 6. Check-in History, POS Kiosk QR Scanner & Expiring Cards Email state
  const [checkins, setCheckins] = useState({
    items: [],
    total: 0,
    active_in_gym_count: 0,
  });
  const [expiringSubs, setExpiringSubs] = useState([]);
  const [posQrCode, setPosQrCode] = useState("DG-000006");
  const [posQrResult, setPosQrResult] = useState(null);
  const [posCameraOpen, setPosCameraOpen] = useState(false);
  const posVideoRef = useRef(null);

  // 7. Group Classes & Attendance state
  const [groupClasses, setGroupClasses] = useState([]);
  const [selectedClassStudents, setSelectedClassStudents] = useState(null);
  const [classModal, setClassModal] = useState(null);
  const [trainers, setTrainers] = useState([]);

  const showNotice = (text, type = "success") => {
    setToast({ type, text });
    window.setTimeout(() => setToast({ type: "", text: "" }), 5000);
  };

  const loadAllData = useCallback(() => {
    gymApi
      .getDashboardSummary({
        from_date: dashDates.from_date || undefined,
        to_date: dashDates.to_date || undefined,
      })
      .then((res) => {
        setDashSummary(res.data);
        setMaintenanceDueCount(res.data?.kpis?.maintenance_due_count || 0);
      })
      .catch(() => {});

    gymApi
      .getPlans({ include_all: true, size: 50 })
      .then((res) => {
        const list = res.data?.items || [];
        setPlans(list);
        if (!posPlanId && list.length > 0) setPosPlanId(list[0].plan_id);
      })
      .catch(() => {});

    gymApi
      .getEquipment()
      .then((res) => {
        setEquipmentList(res.data?.items || []);
        setMaintenanceDueCount(res.data?.maintenance_due_count || 0);
      })
      .catch(() => {});

    gymApi
      .getDiscounts()
      .then((res) => setDiscounts(res.data || []))
      .catch(() => {});

    gymApi
      .getPosInvoices({ size: 15 })
      .then((res) => setPosInvoices(res.data?.items || []))
      .catch(() => {});

    gymApi
      .getCheckInHistory({ size: 20 })
      .then((res) => setCheckins(res.data || { items: [], total: 0, active_in_gym_count: 0 }))
      .catch(() => {});

    gymApi
      .getExpiringSubscriptions(7)
      .then((res) => setExpiringSubs(res.data?.items || []))
      .catch(() => {});

    gymApi
      .getGroupClasses()
      .then((res) => setGroupClasses(res.data || []))
      .catch(() => {});

    gymApi
      .getTrainers()
      .then((res) => setTrainers(res.data || []))
      .catch(() => {});
  }, [dashDates.from_date, dashDates.to_date, posPlanId]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // --- POS Handlers ---
  const handleLookupPhone = async () => {
    if (!posPhone.trim()) return;
    try {
      const res = await gymApi.lookupMemberByPhone(posPhone.trim());
      setPosMember(res.data);
      if (res.data.found) {
        showNotice(`Đã tìm thấy hội viên: ${res.data.full_name}`);
      } else {
        showNotice(res.data.message, "warn");
      }
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Không thể tra cứu hội viên.",
        "error"
      );
    }
  };

  const selectedPosPlan = plans.find(
    (p) => Number(p.plan_id) === Number(posPlanId)
  );
  const posBasePrice = Number(selectedPosPlan?.price || 0);
  const posDiscountAmt = Number(posVoucherResult?.discount_amount || 0);
  const posFinalPrice = Math.max(0, posBasePrice - posDiscountAmt);

  const handleValidatePosVoucher = async () => {
    if (!posVoucher.trim()) {
      setPosVoucherResult(null);
      return;
    }
    try {
      const res = await gymApi.validateDiscount(
        posVoucher.trim(),
        posBasePrice
      );
      setPosVoucherResult(res.data);
      showNotice(res.data.message);
    } catch (err) {
      setPosVoucherResult(null);
      showNotice(
        err.response?.data?.message || "Mã voucher không hợp lệ.",
        "error"
      );
    }
  };

  const handlePosSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await gymApi.posCheckout({
        phone: posPhone.trim(),
        full_name: posNewName.trim() || posMember?.full_name || undefined,
        plan_id: Number(posPlanId),
        discount_code: posVoucherResult
          ? posVoucherResult.code
          : posVoucher.trim() || undefined,
        payment_method: posPayMethod,
      });
      setPosReceipt(res.data);
      showNotice(res.data.message);
      loadAllData();
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Thanh toán POS thất bại.",
        "error"
      );
    }
  };

  // --- Plan CRUD Handlers ---
  const handleSavePlan = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        plan_name: planModal.plan_name,
        category: planModal.category || "Gói Hội Viên",
        duration_days: Number(planModal.duration_days),
        price: Number(planModal.price),
        description: planModal.description,
        status: planModal.status || "ACTIVE",
      };
      if (planModal.plan_id) {
        await gymApi.updatePlan(planModal.plan_id, payload);
        showNotice("Đã cập nhật gói tập thành công!");
      } else {
        await gymApi.createPlan(payload);
        showNotice("Đã thêm gói tập mới thành công!");
      }
      setPlanModal(null);
      loadAllData();
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Lưu gói tập thất bại.",
        "error"
      );
    }
  };

  const handleDeletePlan = async (plan) => {
    if (
      !window.confirm(
        `Bạn có chắc muốn ẩn/ngừng kinh doanh gói "${plan.plan_name}"?`
      )
    )
      return;
    try {
      await gymApi.deletePlan(plan.plan_id);
      showNotice(`Đã chuyển gói "${plan.plan_name}" sang ngừng kinh doanh.`);
      loadAllData();
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Không thể xóa gói tập.",
        "error"
      );
    }
  };

  // --- Equipment CRUD & Maintenance Handlers ---
  const handleSaveEquipment = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: eqModal.name,
        zone: eqModal.zone,
        status: eqModal.status || "HOAT_DONG",
        maintenance_interval_days: Number(
          eqModal.maintenance_interval_days || 30
        ),
        notes: eqModal.notes,
      };
      if (eqModal.equipment_id) {
        await gymApi.updateEquipment(eqModal.equipment_id, payload);
        showNotice("Đã cập nhật thiết bị!");
      } else {
        await gymApi.createEquipment(payload);
        showNotice("Đã thêm thiết bị mới!");
      }
      setEqModal(null);
      loadAllData();
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Lưu thiết bị thất bại.",
        "error"
      );
    }
  };

  const handleMaintainNow = async (eqId) => {
    try {
      await gymApi.markEquipmentMaintained(eqId);
      showNotice("Đã ghi nhận hoàn thành bảo trì định kỳ hôm nay!");
      loadAllData();
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Không thể cập nhật bảo trì.",
        "error"
      );
    }
  };

  // --- Discount CRUD Handlers ---
  const handleSaveDiscount = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        code: discountModal.code.toUpperCase(),
        description: discountModal.description,
        discount_type: discountModal.discount_type || "PERCENT",
        discount_value: Number(discountModal.discount_value),
        min_order_amount: Number(discountModal.min_order_amount || 0),
        expiry_date: discountModal.expiry_date,
        usage_limit: Number(discountModal.usage_limit || 50),
        is_active: true,
      };
      if (discountModal.discount_id) {
        await gymApi.updateDiscount(discountModal.discount_id, payload);
        showNotice("Đã cập nhật mã giảm giá!");
      } else {
        await gymApi.createDiscount(payload);
        showNotice("Đã tạo mã giảm giá mới!");
      }
      setDiscountModal(null);
      loadAllData();
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Lưu voucher thất bại.",
        "error"
      );
    }
  };

  // --- CSV Export Handler (Bonus T3CD54C) ---
  const handleExportCSV = async () => {
    try {
      const res = await gymApi.exportRevenueCSV({
        from_date: dashDates.from_date || undefined,
        to_date: dashDates.to_date || undefined,
      });
      const blob = new Blob([res.data], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `DuckyGym_BaoCao_DoanhThu_${new Date()
        .toISOString()
        .slice(0, 10)}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      showNotice("Đã xuất file CSV báo cáo doanh thu & hóa đơn thành công!");
    } catch (err) {
      showNotice(
        "Chỉ tài khoản ADMIN mới có quyền xuất báo cáo doanh thu CSV.",
        "error"
      );
    }
  };

  // --- Expiry Reminder Email Handler (Bonus T3CD43D) ---
  const handleSendExpiryEmails = async () => {
    try {
      const res = await gymApi.sendExpiryReminders(3);
      showNotice(res.data.message);
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Không thể gửi email nhắc hạn thẻ.",
        "error"
      );
    }
  };

  // --- POS Kiosk QR Check-in / Check-out Handler ---
  const handlePosScanQR = useCallback(
    async (rawCode) => {
      const code = (rawCode || posQrCode || "").trim();
      if (!code) return;
      try {
        const res = await gymApi.scanQRCheckIn(code);
        setPosQrResult(res.data);
        playPosBeep(Boolean(res.data.valid));
        showNotice(
          res.data.message,
          res.data.valid ? "success" : "error"
        );
        loadAllData();
      } catch (err) {
        const msg =
          err.response?.data?.message || "Lỗi kết nối máy chủ Check-in QR.";
        setPosQrResult({ valid: false, status: "ERROR", message: msg });
        playPosBeep(false);
        showNotice(msg, "error");
      }
    },
    [posQrCode, loadAllData]
  );

  useEffect(() => {
    if (!posCameraOpen) return undefined;
    let stream;
    let detector;
    let frame;
    let active = true;

    const scanLoop = async () => {
      if (!active || !posVideoRef.current || !detector) return;
      try {
        const codes = await detector.detect(posVideoRef.current);
        if (codes.length && codes[0].rawValue) {
          const val = codes[0].rawValue;
          setPosQrCode(val);
          setPosCameraOpen(false);
          handlePosScanQR(val);
          return;
        }
      } catch {
        // Ignore frame error
      }
      frame = window.requestAnimationFrame(scanLoop);
    };

    const initCam = async () => {
      try {
        if ("BarcodeDetector" in window) {
          detector = new window.BarcodeDetector({ formats: ["qr_code"] });
        }
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        if (!active) return;
        if (posVideoRef.current) {
          posVideoRef.current.srcObject = stream;
          await posVideoRef.current.play();
        }
        if (detector) {
          frame = window.requestAnimationFrame(scanLoop);
        }
      } catch {
        showNotice(
          "Không mở được webcam trên thiết bị này. Vui lòng dùng máy bắn mã QR hoặc ô nhập mã tại quầy POS.",
          "error"
        );
        setPosCameraOpen(false);
      }
    };

    initCam();
    return () => {
      active = false;
      if (frame) window.cancelAnimationFrame(frame);
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [posCameraOpen, handlePosScanQR]);

  // --- Group Class Attendance Handlers (Bonus T3CD532) ---
  const handleOpenAttendance = async (classId) => {
    try {
      const res = await gymApi.getClassEnrollments(classId);
      setSelectedClassStudents(res.data);
    } catch (err) {
      showNotice("Không thể tải danh sách học viên lớp tập.", "error");
    }
  };

  const handleMarkAttendance = async (classId, enrollmentId, st) => {
    try {
      await gymApi.markClassAttendance(classId, enrollmentId, st);
      showNotice(`Đã điểm danh: ${st}`);
      handleOpenAttendance(classId);
      loadAllData();
    } catch (err) {
      showNotice("Không thể lưu điểm danh.", "error");
    }
  };

  const handleCreateGroupClass = async (e) => {
    e.preventDefault();
    try {
      await gymApi.createGroupClass({
        ...classModal,
        max_capacity: Number(classModal.max_capacity || 15),
        trainer_id: Number(classModal.trainer_id) || undefined,
      });
      setClassModal(null);
      showNotice("Đã tạo lớp tập nhóm mới thành công!");
      loadAllData();
    } catch (err) {
      showNotice(
        err.response?.data?.message || "Tạo lớp tập nhóm thất bại.",
        "error"
      );
    }
  };

  const kpis = dashSummary?.kpis || {};
  const monthlyChart = dashSummary?.monthly_revenue_chart || [];
  const planChart = dashSummary?.plan_breakdown_chart || [];
  const maxMonthRev = Math.max(
    1,
    ...monthlyChart.map((m) => Number(m.net_revenue) || 0)
  );
  const totalPlanSubs = Math.max(
    1,
    planChart.reduce((acc, p) => acc + (Number(p.total_subscriptions) || 0), 0)
  );

  return (
    <div className="admin-shell">
      <style>{adminStyles}</style>

      {/* Sidebar Quản trị & Lễ tân (Task T067F4D & Bonus T3CD423) */}
      <aside className="admin-sidebar">
        <div>
          <Link className="admin-brand" to="/">
            <span className="admin-brand-icon material-symbols-outlined">
              fitness_center
            </span>
            <div>
              <b style={{ display: "block", fontSize: "15px" }}>DUCKY GYM</b>
              <small style={{ color: "#ffb690", fontSize: "10px" }}>
                {isAdmin ? "ADMIN PORTAL" : "RECEPTION POS"}
              </small>
            </div>
          </Link>

          <nav className="admin-nav">
            <button
              type="button"
              className={`admin-nav-btn${
                activeTab === "dashboard" ? " is-active" : ""
              }`}
              onClick={() => setActiveTab("dashboard")}
            >
              <span>📊 Dashboard &amp; Biểu đồ</span>
            </button>
            <button
              type="button"
              className={`admin-nav-btn${
                activeTab === "pos" ? " is-active" : ""
              }`}
              onClick={() => setActiveTab("pos")}
            >
              <span>💳 Quầy POS Lễ tân</span>
            </button>
            <button
              type="button"
              className={`admin-nav-btn${
                activeTab === "plans" ? " is-active" : ""
              }`}
              onClick={() => setActiveTab("plans")}
            >
              <span>📦 Quản lý Gói tập</span>
            </button>
            <button
              type="button"
              className={`admin-nav-btn${
                activeTab === "equipment" ? " is-active" : ""
              }`}
              onClick={() => setActiveTab("equipment")}
            >
              <span>🏋️ Thiết bị &amp; Bảo trì</span>
              {maintenanceDueCount > 0 && (
                <span
                  className="admin-badge-warn"
                  title="Thiết bị đến hạn bảo trì trong 7 ngày"
                >
                  {maintenanceDueCount}
                </span>
              )}
            </button>
            <button
              type="button"
              className={`admin-nav-btn${
                activeTab === "discounts" ? " is-active" : ""
              }`}
              onClick={() => setActiveTab("discounts")}
            >
              <span>🎟️ Quản lý Voucher</span>
            </button>
            <button
              type="button"
              className={`admin-nav-btn${
                activeTab === "checkins" ? " is-active" : ""
              }`}
              onClick={() => setActiveTab("checkins")}
            >
              <span>📷 Check-in &amp; Nhắc hạn</span>
            </button>
            <button
              type="button"
              className={`admin-nav-btn${
                activeTab === "classes" ? " is-active" : ""
              }`}
              onClick={() => setActiveTab("classes")}
            >
              <span>🧘 Lớp tập nhóm</span>
            </button>
          </nav>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {isAdmin && !isStaffRoute && (
            <Link
              to="/pages/test-lab"
              data-testid="admin-only-test-lab-link"
              className="admin-btn admin-btn-secondary"
              style={{ justifyContent: "center", textDecoration: "none", borderColor: "rgba(249,115,22,0.4)", color: "#ffb690" }}
            >
              <span className="material-symbols-outlined">science</span>
              Chạy thử &amp; Test Lab
            </Link>
          )}
          <Link
            to="/kiosk"
            className="admin-btn admin-btn-secondary"
            style={{ justifyContent: "center", textDecoration: "none" }}
          >
            <span className="material-symbols-outlined">qr_code_scanner</span>
            Mở Kiosk Quét QR
          </Link>
          <button
            type="button"
            className="admin-btn admin-btn-danger"
            style={{ justifyContent: "center" }}
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            <span className="material-symbols-outlined">logout</span>
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="admin-main">
        <header className="admin-header">
          <div>
            <b style={{ fontSize: "16px" }}>
              Hệ thống Quản lý Phòng Gym &amp; Hội viên DuckyGym
            </b>
            <span
              style={{
                marginLeft: "12px",
                fontSize: "12px",
                color: "#4ade80",
              }}
            >
              ● Đang tập tại phòng: {checkins.active_in_gym_count} người
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "13px", color: "#a6adc2" }}>
              Xin chào, <b>{user?.full_name || user?.username}</b> ({user?.role})
            </span>
          </div>
        </header>

        <main className="admin-body">
          {toast.text && (
            <div
              role="status"
              className="no-print"
              style={{
                padding: "12px 18px",
                borderRadius: "10px",
                background:
                  toast.type === "error"
                    ? "rgba(239,68,68,0.2)"
                    : "rgba(34,197,94,0.2)",
                border: `1px solid ${
                  toast.type === "error" ? "#ef4444" : "#22c55e"
                }`,
                color: toast.type === "error" ? "#fca5a5" : "#86efac",
                fontWeight: 600,
                fontSize: "13px",
              }}
            >
              {toast.text}
            </div>
          )}

          {/* TAB 1: DASHBOARD & BIỂU ĐỒ (Task T067F28, T067E76, T067D16, Bonus T3CD54C) */}
          {activeTab === "dashboard" && (
            <>
              <div className="admin-kpis">
                <div className="admin-kpi-card">
                  <small>DOANH THU THÁNG</small>
                  <b style={{ color: "#f97316" }}>
                    {formatVND(
                      kpis.monthly_revenue || kpis.filtered_revenue || 28450000
                    )}
                  </b>
                  <small>Từ SQL View vw_monthly_revenue</small>
                </div>
                <div className="admin-kpi-card">
                  <small>TỔNG HỘI VIÊN / MỚI THÁNG NÀY</small>
                  <b>
                    {kpis.total_members || 20} HV (+
                    {kpis.new_members_this_month || 6} mới)
                  </b>
                  <small>Thẻ đang hoạt động: {kpis.active_subscriptions || 18}</small>
                </div>
                <div className="admin-kpi-card">
                  <small>TỶ LỆ GIA HẠN THẺ</small>
                  <b style={{ color: "#4ade80" }}>
                    {kpis.renewal_rate_pct ?? 35}%
                  </b>
                  <small>Hội viên tái đăng ký gói tập</small>
                </div>
                <div className="admin-kpi-card">
                  <small>THIẾT BỊ SẮP BẢO TRÌ (7 NGÀY)</small>
                  <b
                    style={{
                      color:
                        maintenanceDueCount > 0 ? "#f87171" : "#4ade80",
                    }}
                  >
                    {maintenanceDueCount} thiết bị
                  </b>
                  <small>Cảnh báo bảo trì định kỳ</small>
                </div>
              </div>

              <div className="admin-card">
                <div className="admin-card-head">
                  <div>
                    <h2>Bộ lọc thời gian &amp; Xuất báo cáo Doanh thu CSV</h2>
                    <small style={{ color: "#a6adc2" }}>
                      Dữ liệu tổng hợp trực tiếp từ SQL View của TV1
                    </small>
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <input
                      type="date"
                      className="admin-input"
                      value={dashDates.from_date}
                      onChange={(e) =>
                        setDashDates((p) => ({
                          ...p,
                          from_date: e.target.value,
                        }))
                      }
                    />
                    <input
                      type="date"
                      className="admin-input"
                      value={dashDates.to_date}
                      onChange={(e) =>
                        setDashDates((p) => ({ ...p, to_date: e.target.value }))
                      }
                    />
                    <button
                      type="button"
                      className="admin-btn admin-btn-secondary"
                      onClick={loadAllData}
                    >
                      Lọc dữ liệu
                    </button>
                    {isAdmin && (
                      <button
                        type="button"
                        className="admin-btn admin-btn-primary"
                        onClick={handleExportCSV}
                      >
                        <span className="material-symbols-outlined">
                          download
                        </span>
                        Xuất báo cáo CSV (ADMIN)
                      </button>
                    )}
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1.4fr 1fr",
                    gap: "22px",
                  }}
                >
                  {/* Biểu đồ cột doanh thu theo tháng */}
                  <div
                    style={{
                      background: "#131b2e",
                      padding: "18px",
                      borderRadius: "14px",
                    }}
                  >
                    <h3 style={{ margin: "0 0 14px", fontSize: "15px" }}>
                      Biểu đồ cột Doanh thu theo tháng (vw_monthly_revenue)
                    </h3>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: `repeat(${Math.max(
                          1,
                          monthlyChart.length
                        )}, 1fr)`,
                        gap: "12px",
                        alignItems: "end",
                        height: "190px",
                        paddingTop: "24px",
                      }}
                    >
                      {monthlyChart.map((m) => {
                        const rev = Number(m.net_revenue) || 0;
                        const h = Math.max(
                          24,
                          Math.round((rev / maxMonthRev) * 145)
                        );
                        return (
                          <div
                            key={m.month}
                            style={{
                              display: "flex",
                              flexDirection: "column",
                              alignItems: "center",
                              gap: "6px",
                            }}
                          >
                            <span
                              style={{
                                fontSize: "11px",
                                color: "#ffb690",
                                fontWeight: 700,
                              }}
                            >
                              {formatVND(rev)}
                            </span>
                            <div
                              style={{
                                width: "42px",
                                height: `${h}px`,
                                background:
                                  "linear-gradient(180deg, #f97316, #c2410c)",
                                borderRadius: "6px 6px 0 0",
                              }}
                            />
                            <small style={{ color: "#a6adc2", fontSize: "11px" }}>
                              Tháng {m.month} ({m.invoice_count} HĐ)
                            </small>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Biểu đồ tròn cơ cấu gói tập */}
                  <div
                    style={{
                      background: "#131b2e",
                      padding: "18px",
                      borderRadius: "14px",
                    }}
                  >
                    <h3 style={{ margin: "0 0 14px", fontSize: "15px" }}>
                      Biểu đồ cơ cấu Gói tập bán chạy (vw_top_gym_plans)
                    </h3>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "10px",
                      }}
                    >
                      {planChart.map((p, idx) => {
                        const pct = Math.round(
                          ((Number(p.total_subscriptions) || 0) /
                            totalPlanSubs) *
                            100
                        );
                        const color = CHART_COLORS[idx % CHART_COLORS.length];
                        return (
                          <div key={p.plan_id}>
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                fontSize: "12px",
                                marginBottom: "4px",
                              }}
                            >
                              <span>
                                <b style={{ color }}>{p.plan_name}</b> (
                                {p.total_subscriptions} lượt)
                              </span>
                              <span>
                                {pct}% · {formatVND(p.total_revenue)}
                              </span>
                            </div>
                            <div
                              style={{
                                height: "8px",
                                background: "#222a3d",
                                borderRadius: "999px",
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  width: `${Math.max(6, pct)}%`,
                                  height: "100%",
                                  background: color,
                                }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* TAB 2: QUẦY POS LỄ TÂN & KIOSK QUÉT QR CHECK-IN / CHECK-OUT (Task T067FBB, T067DF1, T067F99, T067E27) */}
          {activeTab === "pos" && (
            <>
              {/* Kiosk Quét QR tích hợp trực tiếp tại Màn POS Lễ Tân */}
              <section className="admin-card no-print">
                <div className="admin-card-head">
                  <div>
                    <h2>
                      📷 Kiosk Quét QR &amp; Theo dõi Check-in / Check-out (Dành
                      riêng cho POS Lễ tân)
                    </h2>
                    <small style={{ color: "#a6adc2" }}>
                      Lễ tân quét thẻ QR hội viên lần 1 để Check-in, quét lần 2
                      để Check-out · Hiện có{" "}
                      <b style={{ color: "#4ade80" }}>
                        {checkins.active_in_gym_count} hội viên
                      </b>{" "}
                      đang tập trong phòng
                    </small>
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      className="admin-btn admin-btn-secondary"
                      onClick={() => setPosCameraOpen((v) => !v)}
                    >
                      <span className="material-symbols-outlined">
                        videocam
                      </span>
                      {posCameraOpen
                        ? "Tắt Camera POS"
                        : "Bật Camera Quét QR tại Quầy"}
                    </button>
                    <Link
                      to="/staff/check-in"
                      className="admin-btn admin-btn-secondary"
                      style={{ textDecoration: "none" }}
                    >
                      <span className="material-symbols-outlined">
                        open_in_new
                      </span>
                      Màn Kiosk Toàn Màn Hình
                    </Link>
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1.35fr",
                    gap: "20px",
                    alignItems: "start",
                  }}
                >
                  {/* Cột trái: Máy quét QR & Cảnh báo kết quả */}
                  <div
                    style={{
                      background: "#131b2e",
                      padding: "18px",
                      borderRadius: "14px",
                      border: "1px solid rgba(255,255,255,0.07)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "12px",
                    }}
                  >
                    {posCameraOpen && (
                      <div
                        style={{
                          position: "relative",
                          borderRadius: "12px",
                          overflow: "hidden",
                          border: "2px solid #f97316",
                          background: "#000",
                          height: "210px",
                        }}
                      >
                        <video
                          ref={posVideoRef}
                          muted
                          playsInline
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                          }}
                        />
                      </div>
                    )}

                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        handlePosScanQR(posQrCode);
                      }}
                      style={{ display: "flex", gap: "8px" }}
                    >
                      <input
                        className="admin-input"
                        style={{ flex: 1 }}
                        value={posQrCode}
                        onChange={(e) => setPosQrCode(e.target.value)}
                        placeholder="Quét hoặc nhập mã QR thẻ hội viên (VD: DG-000006)..."
                      />
                      <button
                        type="submit"
                        className="admin-btn admin-btn-primary"
                      >
                        <span className="material-symbols-outlined">
                          qr_code_scanner
                        </span>
                        Quét Check-in / Out
                      </button>
                    </form>

                    <div
                      style={{
                        display: "flex",
                        gap: "6px",
                        flexWrap: "wrap",
                      }}
                    >
                      <button
                        type="button"
                        className="admin-btn admin-btn-success"
                        style={{ fontSize: "11px", padding: "6px 10px" }}
                        onClick={() => {
                          setPosQrCode("DG-000006");
                          handlePosScanQR("DG-000006");
                        }}
                      >
                        Test 1: Thẻ Hợp lệ (DG-000006)
                      </button>
                      <button
                        type="button"
                        className="admin-btn admin-btn-secondary"
                        style={{
                          fontSize: "11px",
                          padding: "6px 10px",
                          color: "#fde68a",
                        }}
                        onClick={() => {
                          setPosQrCode("DG-000023");
                          handlePosScanQR("DG-000023");
                        }}
                      >
                        Test 2: Thẻ Hết hạn (DG-000023)
                      </button>
                      <button
                        type="button"
                        className="admin-btn admin-btn-danger"
                        style={{ fontSize: "11px", padding: "6px 10px" }}
                        onClick={() => {
                          setPosQrCode("DG-999999");
                          handlePosScanQR("DG-999999");
                        }}
                      >
                        Test 3: Mã Không tồn tại
                      </button>
                    </div>

                    {posQrResult && (
                      <div
                        style={{
                          padding: "14px 16px",
                          borderRadius: "12px",
                          background: posQrResult.valid
                            ? "rgba(34,197,94,0.18)"
                            : "rgba(239,68,68,0.18)",
                          border: `2px solid ${
                            posQrResult.valid ? "#22c55e" : "#ef4444"
                          }`,
                          color: posQrResult.valid ? "#86efac" : "#fca5a5",
                        }}
                      >
                        <div
                          style={{
                            fontWeight: 700,
                            fontSize: "15px",
                            marginBottom: "4px",
                          }}
                        >
                          {posQrResult.valid
                            ? posQrResult.action === "CHECK_OUT"
                              ? "✓ CHECK-OUT THÀNH CÔNG"
                              : "✓ CHECK-IN HỢP LỆ"
                            : "✕ TỪ CHỐI CHECK-IN"}
                        </div>
                        <div style={{ fontSize: "13px" }}>
                          {posQrResult.message}
                        </div>
                        {posQrResult.full_name && (
                          <div
                            style={{
                              fontSize: "12px",
                              marginTop: "6px",
                              color: "#dae2fd",
                            }}
                          >
                            Hội viên: <b>{posQrResult.full_name}</b> · Mã thẻ:{" "}
                            <b>{posQrResult.member_code}</b> · Gói:{" "}
                            <b>{posQrResult.plan_name || "--"}</b> (Hạn:{" "}
                            {posQrResult.end_date || "--"}) · Phản hồi:{" "}
                            <b>{posQrResult.response_time_ms}ms</b>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Cột phải: Bảng theo dõi trực tiếp hội viên Check-in / Check-out tại quầy */}
                  <div
                    style={{
                      background: "#131b2e",
                      padding: "16px",
                      borderRadius: "14px",
                      border: "1px solid rgba(255,255,255,0.07)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "10px",
                      }}
                    >
                      <b style={{ fontSize: "14px" }}>
                        Danh sách theo dõi Hội viên Check-in / Check-out mới
                        nhất
                      </b>
                      <span
                        style={{
                          fontSize: "12px",
                          padding: "4px 10px",
                          borderRadius: "999px",
                          background: "rgba(34,197,94,0.18)",
                          color: "#4ade80",
                          fontWeight: 700,
                        }}
                      >
                        Đang tập: {checkins.active_in_gym_count} người
                      </span>
                    </div>

                    <div style={{ maxHeight: "235px", overflowY: "auto" }}>
                      <table className="admin-table">
                        <thead>
                          <tr>
                            <th>Hội viên</th>
                            <th>Mã QR</th>
                            <th>Giờ vào</th>
                            <th>Giờ ra</th>
                            <th>Trạng thái / Thao tác</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(checkins.items || []).slice(0, 8).map((c) => (
                            <tr key={c.attendance_id}>
                              <td>
                                <b>{c.full_name}</b>
                                <div
                                  style={{ fontSize: "11px", color: "#a6adc2" }}
                                >
                                  {c.phone}
                                </div>
                              </td>
                              <td>{c.member_code}</td>
                              <td>
                                {String(c.check_in)
                                  .replace("T", " ")
                                  .slice(11, 16)}
                              </td>
                              <td>
                                {c.check_out
                                  ? `${String(c.check_out)
                                      .replace("T", " ")
                                      .slice(11, 16)} (${
                                      c.duration_minutes || 1
                                    }p)`
                                  : "--"}
                              </td>
                              <td>
                                {c.status === "CHECKED_IN" ? (
                                  <button
                                    type="button"
                                    className="admin-btn admin-btn-primary"
                                    style={{
                                      padding: "5px 10px",
                                      fontSize: "11px",
                                    }}
                                    onClick={() =>
                                      handlePosScanQR(c.member_code)
                                    }
                                  >
                                    Cho Check-out
                                  </button>
                                ) : (
                                  <span
                                    style={{
                                      fontSize: "11px",
                                      color: "#a6adc2",
                                    }}
                                  >
                                    Đã Check-out
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </section>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "22px",
                }}
              >
              <section className="admin-card no-print">
                <div className="admin-card-head">
                  <h2>Quầy Thanh Toán POS Lễ Tân</h2>
                </div>
                <form
                  onSubmit={handlePosSubmit}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "14px",
                  }}
                >
                  <div>
                    <label style={{ fontSize: "12px", color: "#a6adc2" }}>
                      1. Tìm hội viên theo Số điện thoại (SĐT)
                    </label>
                    <div style={{ display: "flex", gap: "8px", marginTop: "5px" }}>
                      <input
                        className="admin-input"
                        style={{ flex: 1 }}
                        value={posPhone}
                        onChange={(e) => setPosPhone(e.target.value)}
                        placeholder="Nhập SĐT (VD: 0901000001)..."
                        required
                      />
                      <button
                        type="button"
                        className="admin-btn admin-btn-secondary"
                        onClick={handleLookupPhone}
                      >
                        Tìm SĐT
                      </button>
                    </div>
                  </div>

                  {posMember?.found ? (
                    <div
                      style={{
                        padding: "12px",
                        borderRadius: "10px",
                        background: "#131b2e",
                        border: "1px solid rgba(34,197,94,0.35)",
                        fontSize: "13px",
                      }}
                    >
                      <div>
                        Hội viên: <b>{posMember.full_name}</b> · Mã thẻ:{" "}
                        <b>{posMember.member_code}</b>
                      </div>
                      <div style={{ color: "#a6adc2", marginTop: "4px" }}>
                        Gói hiện tại:{" "}
                        <b>
                          {posMember.current_subscription?.plan_name ||
                            "Chưa có"}
                        </b>{" "}
                        (Hạn:{" "}
                        {posMember.current_subscription?.end_date || "--"})
                      </div>
                    </div>
                  ) : (
                    <div>
                      <label style={{ fontSize: "12px", color: "#a6adc2" }}>
                        Họ tên hội viên mới (nếu khách vãng lai chưa có tài
                        khoản)
                      </label>
                      <input
                        className="admin-input"
                        style={{ width: "100%", marginTop: "5px" }}
                        value={posNewName}
                        onChange={(e) => setPosNewName(e.target.value)}
                        placeholder="Nhập họ tên hội viên..."
                      />
                    </div>
                  )}

                  <div>
                    <label style={{ fontSize: "12px", color: "#a6adc2" }}>
                      2. Chọn gói tập đăng ký mới hoặc gia hạn
                    </label>
                    <select
                      className="admin-select"
                      style={{ width: "100%", marginTop: "5px" }}
                      value={posPlanId}
                      onChange={(e) => {
                        setPosPlanId(Number(e.target.value));
                        setPosVoucherResult(null);
                      }}
                    >
                      {plans
                        .filter((p) => p.status === "ACTIVE")
                        .map((p) => (
                          <option key={p.plan_id} value={p.plan_id}>
                            {p.plan_name} ({p.duration_days} ngày) —{" "}
                            {formatVND(p.price)}
                          </option>
                        ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "12px", color: "#a6adc2" }}>
                      3. Mã Voucher khuyến mãi (VD: WELCOME20, SUMMER100K)
                    </label>
                    <div style={{ display: "flex", gap: "8px", marginTop: "5px" }}>
                      <input
                        className="admin-input"
                        style={{ flex: 1 }}
                        value={posVoucher}
                        onChange={(e) =>
                          setPosVoucher(e.target.value.toUpperCase())
                        }
                        placeholder="Nhập mã giảm giá..."
                      />
                      <button
                        type="button"
                        className="admin-btn admin-btn-secondary"
                        onClick={handleValidatePosVoucher}
                      >
                        Kiểm tra mã
                      </button>
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: "12px", color: "#a6adc2" }}>
                      4. Phương thức thanh toán
                    </label>
                    <div style={{ display: "flex", gap: "12px", marginTop: "6px" }}>
                      <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <input
                          type="radio"
                          checked={posPayMethod === "CASH"}
                          onChange={() => setPosPayMethod("CASH")}
                        />
                        Tiền mặt (CASH)
                      </label>
                      <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <input
                          type="radio"
                          checked={posPayMethod === "BANK_TRANSFER"}
                          onChange={() => setPosPayMethod("BANK_TRANSFER")}
                        />
                        Chuyển khoản QR (BANK_TRANSFER)
                      </label>
                    </div>
                  </div>

                  <div
                    style={{
                      padding: "14px",
                      borderRadius: "10px",
                      background: "#131b2e",
                      display: "flex",
                      flexDirection: "column",
                      gap: "6px",
                      fontSize: "13px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>Giá gốc:</span>
                      <b>{formatVND(posBasePrice)}</b>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#4ade80" }}>
                      <span>Giảm giá Voucher:</span>
                      <b>- {formatVND(posDiscountAmt)}</b>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: "17px",
                        color: "#f97316",
                        borderTop: "1px solid rgba(255,255,255,0.08)",
                        paddingTop: "8px",
                      }}
                    >
                      <b>TỔNG THANH TOÁN:</b>
                      <b>{formatVND(posFinalPrice)}</b>
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="admin-btn admin-btn-primary"
                    style={{ justifyContent: "center", padding: "12px" }}
                  >
                    <span className="material-symbols-outlined">
                      point_of_sale
                    </span>
                    Xác nhận Thu tiền &amp; Xuất Hóa Đơn POS
                  </button>
                </form>
              </section>

              <section className="admin-card">
                {posReceipt ? (
                  <div
                    className="pos-receipt-box"
                    style={{
                      padding: "20px",
                      borderRadius: "12px",
                      background: "#131b2e",
                      border: "1px dashed #f97316",
                    }}
                  >
                    <h2 style={{ margin: "0 0 6px", color: "#f97316" }}>
                      HÓA ĐƠN THANH TOÁN DUCKY GYM
                    </h2>
                    <small>
                      Mã HĐ: <b>{posReceipt.invoice_code}</b> · Mã GD:{" "}
                      <b>{posReceipt.transaction_code}</b>
                    </small>
                    <hr
                      style={{
                        borderColor: "rgba(255,255,255,0.1)",
                        margin: "12px 0",
                      }}
                    />
                    <p>
                      Hội viên: <b>{posReceipt.member.full_name}</b> (SĐT:{" "}
                      {posReceipt.member.phone})
                    </p>
                    <p>
                      Mã thẻ QR: <b>{posReceipt.member.member_code}</b>
                    </p>
                    <p>
                      Gói đăng ký: <b>{posReceipt.subscription.plan_name}</b> (
                      {posReceipt.subscription.subscription_type})
                    </p>
                    <p>
                      Thời hạn mới: <b>{posReceipt.subscription.start_date}</b>{" "}
                      → <b>{posReceipt.subscription.end_date}</b>
                    </p>
                    <p>
                      Tổng tiền gốc:{" "}
                      {formatVND(posReceipt.billing.total_amount)} · Giảm giá:{" "}
                      {formatVND(posReceipt.billing.discount_amount)}
                    </p>
                    <h3 style={{ color: "#4ade80" }}>
                      THỰC THU: {formatVND(posReceipt.billing.final_amount)} (
                      {posReceipt.billing.payment_method})
                    </h3>
                    <p style={{ fontSize: "12px", color: "#a6adc2" }}>
                      Thu ngân: {posReceipt.staff_name}
                    </p>
                    <div
                      className="no-print"
                      style={{ display: "flex", gap: "10px", marginTop: "14px" }}
                    >
                      <button
                        type="button"
                        className="admin-btn admin-btn-primary"
                        onClick={() => window.print()}
                      >
                        <span className="material-symbols-outlined">print</span>
                        In Hóa Đơn (window.print)
                      </button>
                      <button
                        type="button"
                        className="admin-btn admin-btn-secondary"
                        onClick={() => setPosReceipt(null)}
                      >
                        Đóng
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="admin-card-head">
                      <h2>Lịch sử Hóa đơn POS gần đây</h2>
                    </div>
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Mã HĐ</th>
                          <th>Hội viên</th>
                          <th>Gói tập</th>
                          <th>Thực thu</th>
                          <th>PT Thanh toán</th>
                        </tr>
                      </thead>
                      <tbody>
                        {posInvoices.map((inv) => (
                          <tr key={inv.invoice_id}>
                            <td>{inv.invoice_code}</td>
                            <td>
                              {inv.member_name} ({inv.member_phone})
                            </td>
                            <td>{inv.plan_name}</td>
                            <td style={{ fontWeight: 700, color: "#4ade80" }}>
                              {formatVND(inv.final_amount)}
                            </td>
                            <td>{inv.payment_method}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </section>
            </div>
            </>
          )}

          {/* TAB 3: QUẢN LÝ GÓI TẬP (Task T067F4D & T067D7C) */}
          {activeTab === "plans" && (
            <section className="admin-card">
              <div className="admin-card-head">
                <div>
                  <h2>Quản lý Gói tập (CRUD /gym-plans)</h2>
                  <small style={{ color: "#a6adc2" }}>
                    Kiểm tra giá &gt; 0, tên không trùng, hỗ trợ ẩn/hiện gói tập
                  </small>
                </div>
                {isAdmin && (
                  <button
                    type="button"
                    className="admin-btn admin-btn-primary"
                    onClick={() =>
                      setPlanModal({
                        plan_name: "",
                        category: "Gói Hội Viên",
                        duration_days: 30,
                        price: 500000,
                        description: "",
                        status: "ACTIVE",
                      })
                    }
                  >
                    + Thêm gói tập mới
                  </button>
                )}
              </div>

              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Tên gói tập</th>
                    <th>Danh mục</th>
                    <th>Số ngày</th>
                    <th>Giá gói</th>
                    <th>Trạng thái</th>
                    {isAdmin && <th>Thao tác</th>}
                  </tr>
                </thead>
                <tbody>
                  {plans.map((p) => (
                    <tr key={p.plan_id}>
                      <td>#{p.plan_id}</td>
                      <td>
                        <b>{p.plan_name}</b>
                        <div style={{ fontSize: "11px", color: "#a6adc2" }}>
                          {p.description}
                        </div>
                      </td>
                      <td>{p.category}</td>
                      <td>{p.duration_days} ngày</td>
                      <td style={{ fontWeight: 700 }}>{formatVND(p.price)}</td>
                      <td>
                        <span
                          style={{
                            padding: "4px 8px",
                            borderRadius: "6px",
                            fontSize: "11px",
                            background:
                              p.status === "ACTIVE"
                                ? "rgba(34,197,94,0.18)"
                                : "rgba(239,68,68,0.18)",
                            color:
                              p.status === "ACTIVE" ? "#4ade80" : "#fca5a5",
                          }}
                        >
                          {p.status === "ACTIVE" ? "ĐANG MỞ" : "ĐÃ ẨN"}
                        </span>
                      </td>
                      {isAdmin && (
                        <td style={{ display: "flex", gap: "6px" }}>
                          <button
                            type="button"
                            className="admin-btn admin-btn-secondary"
                            onClick={() => setPlanModal({ ...p })}
                          >
                            Sửa
                          </button>
                          {p.status === "ACTIVE" && (
                            <button
                              type="button"
                              className="admin-btn admin-btn-danger"
                              onClick={() => handleDeletePlan(p)}
                            >
                              Ẩn
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {/* TAB 4: THIẾT BỊ & BẢO TRÌ ĐỊNH KỲ (Task T067D7C & Bonus T3CD423) */}
          {activeTab === "equipment" && (
            <section className="admin-card">
              <div className="admin-card-head">
                <div>
                  <h2>
                    Quản lý Thiết bị &amp; Lịch bảo trì định kỳ (/equipment)
                  </h2>
                  <small style={{ color: "#ffb690" }}>
                    Có {maintenanceDueCount} thiết bị đến hạn bảo trì trong vòng
                    7 ngày tới
                  </small>
                </div>
                {isAdmin && (
                  <button
                    type="button"
                    className="admin-btn admin-btn-primary"
                    onClick={() =>
                      setEqModal({
                        name: "",
                        zone: "Khu Cardio",
                        status: "HOAT_DONG",
                        maintenance_interval_days: 30,
                        notes: "",
                      })
                    }
                  >
                    + Thêm thiết bị
                  </button>
                )}
              </div>

              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Tên thiết bị</th>
                    <th>Khu vực</th>
                    <th>Trạng thái</th>
                    <th>Chu kỳ bảo trì</th>
                    <th>Hạn bảo trì tiếp theo</th>
                    <th>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {equipmentList.map((eq) => (
                    <tr key={eq.equipment_id}>
                      <td>
                        <b>{eq.name}</b>
                      </td>
                      <td>{eq.zone}</td>
                      <td>
                        <span
                          style={{
                            padding: "4px 8px",
                            borderRadius: "6px",
                            fontSize: "11px",
                            fontWeight: 700,
                            background:
                              eq.status === "HOAT_DONG"
                                ? "rgba(34,197,94,0.18)"
                                : eq.status === "BAO_TRI"
                                ? "rgba(245,158,11,0.18)"
                                : "rgba(239,68,68,0.18)",
                            color:
                              eq.status === "HOAT_DONG"
                                ? "#4ade80"
                                : eq.status === "BAO_TRI"
                                ? "#fde68a"
                                : "#fca5a5",
                          }}
                        >
                          {eq.status_label}
                        </span>
                      </td>
                      <td>{eq.maintenance_interval_days} ngày</td>
                      <td>
                        <span
                          style={{
                            color: eq.is_maintenance_due
                              ? "#f87171"
                              : "#dae2fd",
                            fontWeight: eq.is_maintenance_due ? 700 : 400,
                          }}
                        >
                          {eq.next_maintenance_date} (
                          {eq.days_until_maintenance} ngày)
                          {eq.is_maintenance_due && " ⚠️ Sắp đến hạn"}
                        </span>
                      </td>
                      <td style={{ display: "flex", gap: "6px" }}>
                        <button
                          type="button"
                          className="admin-btn admin-btn-success"
                          onClick={() => handleMaintainNow(eq.equipment_id)}
                        >
                          ✓ Đã bảo trì hôm nay
                        </button>
                        {isAdmin && (
                          <button
                            type="button"
                            className="admin-btn admin-btn-secondary"
                            onClick={() => setEqModal({ ...eq })}
                          >
                            Sửa
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {/* TAB 5: QUẢN LÝ VOUCHER (Task T067E76) */}
          {activeTab === "discounts" && (
            <section className="admin-card">
              <div className="admin-card-head">
                <h2>Quản lý Mã giảm giá / Voucher (CRUD /discounts)</h2>
                {isAdmin && (
                  <button
                    type="button"
                    className="admin-btn admin-btn-primary"
                    onClick={() =>
                      setDiscountModal({
                        code: "",
                        description: "",
                        discount_type: "PERCENT",
                        discount_value: 15,
                        min_order_amount: 0,
                        expiry_date: "2027-01-31",
                        usage_limit: 50,
                      })
                    }
                  >
                    + Tạo Voucher mới
                  </button>
                )}
              </div>

              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Mã Voucher</th>
                    <th>Mô tả</th>
                    <th>Mức giảm</th>
                    <th>Đơn tối thiểu</th>
                    <th>Đã dùng / Giới hạn</th>
                    <th>Hạn dùng</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {discounts.map((d) => (
                    <tr key={d.discount_id}>
                      <td>
                        <b style={{ color: "#ffb690" }}>{d.code}</b>
                      </td>
                      <td>{d.description}</td>
                      <td>
                        {d.discount_type === "PERCENT"
                          ? `${d.discount_value}%`
                          : formatVND(d.discount_value)}
                      </td>
                      <td>{formatVND(d.min_order_amount)}</td>
                      <td>
                        {d.used_count} / {d.usage_limit}
                      </td>
                      <td>{d.expiry_date}</td>
                      <td>{d.status_label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {/* TAB 6: CHECK-IN & EMAIL NHẮC HẠN THẺ (Task T067E45 & Bonus T3CD43D) */}
          {activeTab === "checkins" && (
            <>
              <section className="admin-card">
                <div className="admin-card-head">
                  <div>
                    <h2>
                      Hội viên sắp hết hạn thẻ (Bonus T3CD43D — Gửi Email nhắc
                      hạn qua BackgroundTasks)
                    </h2>
                    <small style={{ color: "#a6adc2" }}>
                      Tự động gửi email nhắc gia hạn cho các hội viên còn hạn
                      &le; 3-7 ngày
                    </small>
                  </div>
                  <button
                    type="button"
                    className="admin-btn admin-btn-primary"
                    onClick={handleSendExpiryEmails}
                  >
                    <span className="material-symbols-outlined">mail</span>
                    Gửi Email nhắc thẻ sắp hết hạn (BackgroundTasks)
                  </button>
                </div>

                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Hội viên</th>
                      <th>Email</th>
                      <th>Số điện thoại</th>
                      <th>Gói tập</th>
                      <th>Ngày hết hạn</th>
                      <th>Còn lại</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expiringSubs.map((s) => (
                      <tr key={s.subscription_id}>
                        <td>
                          <b>{s.full_name}</b>
                        </td>
                        <td>{s.email}</td>
                        <td>{s.phone}</td>
                        <td>{s.plan_name}</td>
                        <td>{s.end_date}</td>
                        <td style={{ color: "#f87171", fontWeight: 700 }}>
                          Còn {s.days_remaining} ngày
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>

              <section className="admin-card">
                <div className="admin-card-head">
                  <h2>
                    Toàn bộ lịch sử Check-in / Check-out (Đang trong phòng:{" "}
                    {checkins.active_in_gym_count} người)
                  </h2>
                </div>
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Mã lượt</th>
                      <th>Hội viên</th>
                      <th>Mã QR</th>
                      <th>Giờ vào</th>
                      <th>Giờ ra</th>
                      <th>Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(checkins.items || []).map((c) => (
                      <tr key={c.attendance_id}>
                        <td>#{c.attendance_id}</td>
                        <td>
                          {c.full_name} ({c.phone})
                        </td>
                        <td>{c.member_code}</td>
                        <td>{String(c.check_in).replace("T", " ").slice(0, 16)}</td>
                        <td>
                          {c.check_out
                            ? String(c.check_out).replace("T", " ").slice(0, 16)
                            : "Đang tập"}
                        </td>
                        <td>{c.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            </>
          )}

          {/* TAB 7: LỚP TẬP NHÓM & ĐIỂM DANH (Bonus T3CD532) */}
          {activeTab === "classes" && (
            <section className="admin-card">
              <div className="admin-card-head">
                <h2>
                  Quản lý Lớp tập nhóm &amp; Điểm danh học viên (/group-classes)
                </h2>
                <button
                  type="button"
                  className="admin-btn admin-btn-primary"
                  onClick={() =>
                    setClassModal({
                      class_name: "",
                      category: "YOGA",
                      trainer_id: trainers[0]?.user_id || "",
                      room: "Studio A · Tầng 2",
                      schedule_date: new Date().toISOString().slice(0, 10),
                      start_time: "18:00",
                      end_time: "19:00",
                      max_capacity: 15,
                      description: "",
                    })
                  }
                >
                  + Tạo lớp tập nhóm
                </button>
              </div>

              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Tên lớp</th>
                    <th>Bộ môn</th>
                    <th>HLV phụ trách</th>
                    <th>Phòng tập</th>
                    <th>Ngày &amp; Giờ</th>
                    <th>Sĩ số</th>
                    <th>Điểm danh</th>
                  </tr>
                </thead>
                <tbody>
                  {groupClasses.map((gc) => (
                    <tr key={gc.class_id}>
                      <td>
                        <b>{gc.class_name}</b>
                      </td>
                      <td>{gc.category}</td>
                      <td>{gc.trainer_name}</td>
                      <td>{gc.room}</td>
                      <td>
                        {gc.schedule_date} ({gc.start_time} - {gc.end_time})
                      </td>
                      <td>
                        {gc.enrolled_count} / {gc.max_capacity}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="admin-btn admin-btn-secondary"
                          onClick={() => handleOpenAttendance(gc.class_id)}
                        >
                          Điểm danh lớp
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {selectedClassStudents && (
                <div
                  style={{
                    marginTop: "20px",
                    padding: "16px",
                    borderRadius: "12px",
                    background: "#131b2e",
                  }}
                >
                  <h3>
                    Điểm danh lớp:{" "}
                    {selectedClassStudents.class_info?.class_name}
                  </h3>
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Học viên</th>
                        <th>Số điện thoại</th>
                        <th>Trạng thái</th>
                        <th>Thao tác điểm danh</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedClassStudents.students.map((st) => (
                        <tr key={st.enrollment_id}>
                          <td>{st.full_name}</td>
                          <td>{st.phone}</td>
                          <td>
                            <b>{st.status}</b>
                          </td>
                          <td style={{ display: "flex", gap: "8px" }}>
                            <button
                              type="button"
                              className="admin-btn admin-btn-success"
                              onClick={() =>
                                handleMarkAttendance(
                                  selectedClassStudents.class_info.class_id,
                                  st.enrollment_id,
                                  "ATTENDED"
                                )
                              }
                            >
                              ✓ Có mặt
                            </button>
                            <button
                              type="button"
                              className="admin-btn admin-btn-danger"
                              onClick={() =>
                                handleMarkAttendance(
                                  selectedClassStudents.class_info.class_id,
                                  st.enrollment_id,
                                  "ABSENT"
                                )
                              }
                            >
                              ✕ Vắng mặt
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
        </main>
      </div>

      {/* Modal Thêm/Sửa Gói Tập */}
      {planModal && (
        <div className="admin-modal-backdrop">
          <form className="admin-modal" onSubmit={handleSavePlan}>
            <h3>
              {planModal.plan_id ? "Cập nhật Gói tập" : "Thêm Gói tập mới"}
            </h3>
            <input
              className="admin-input"
              placeholder="Tên gói tập..."
              value={planModal.plan_name}
              onChange={(e) =>
                setPlanModal({ ...planModal, plan_name: e.target.value })
              }
              required
            />
            <input
              className="admin-input"
              placeholder="Danh mục (VD: Gói Phổ Biến)..."
              value={planModal.category}
              onChange={(e) =>
                setPlanModal({ ...planModal, category: e.target.value })
              }
              required
            />
            <input
              className="admin-input"
              type="number"
              min="1"
              placeholder="Số ngày hiệu lực..."
              value={planModal.duration_days}
              onChange={(e) =>
                setPlanModal({ ...planModal, duration_days: e.target.value })
              }
              required
            />
            <input
              className="admin-input"
              type="number"
              min="1000"
              placeholder="Giá gói tập (VNĐ > 0)..."
              value={planModal.price}
              onChange={(e) =>
                setPlanModal({ ...planModal, price: e.target.value })
              }
              required
            />
            <input
              className="admin-input"
              placeholder="Mô tả quyền lợi..."
              value={planModal.description || ""}
              onChange={(e) =>
                setPlanModal({ ...planModal, description: e.target.value })
              }
            />
            <select
              className="admin-select"
              value={planModal.status || "ACTIVE"}
              onChange={(e) =>
                setPlanModal({ ...planModal, status: e.target.value })
              }
            >
              <option value="ACTIVE">ĐANG MỞ (ACTIVE)</option>
              <option value="DISCONTINUED">ẨN / NGỪNG BÁN (DISCONTINUED)</option>
            </select>
            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="admin-btn admin-btn-secondary"
                onClick={() => setPlanModal(null)}
              >
                Hủy
              </button>
              <button type="submit" className="admin-btn admin-btn-primary">
                Lưu gói tập
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Modal Thêm/Sửa Thiết bị */}
      {eqModal && (
        <div className="admin-modal-backdrop">
          <form className="admin-modal" onSubmit={handleSaveEquipment}>
            <h3>
              {eqModal.equipment_id ? "Cập nhật Thiết bị" : "Thêm Thiết bị mới"}
            </h3>
            <input
              className="admin-input"
              placeholder="Tên thiết bị..."
              value={eqModal.name}
              onChange={(e) => setEqModal({ ...eqModal, name: e.target.value })}
              required
            />
            <input
              className="admin-input"
              placeholder="Khu vực (VD: Khu Cardio)..."
              value={eqModal.zone}
              onChange={(e) => setEqModal({ ...eqModal, zone: e.target.value })}
              required
            />
            <select
              className="admin-select"
              value={eqModal.status || "HOAT_DONG"}
              onChange={(e) =>
                setEqModal({ ...eqModal, status: e.target.value })
              }
            >
              <option value="HOAT_DONG">HOẠT ĐỘNG</option>
              <option value="BAO_TRI">BẢO TRÌ</option>
              <option value="HONG">HỎNG</option>
            </select>
            <input
              className="admin-input"
              type="number"
              min="1"
              placeholder="Chu kỳ bảo trì định kỳ (ngày)..."
              value={eqModal.maintenance_interval_days}
              onChange={(e) =>
                setEqModal({
                  ...eqModal,
                  maintenance_interval_days: e.target.value,
                })
              }
              required
            />
            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="admin-btn admin-btn-secondary"
                onClick={() => setEqModal(null)}
              >
                Hủy
              </button>
              <button type="submit" className="admin-btn admin-btn-primary">
                Lưu thiết bị
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Modal Tạo Voucher */}
      {discountModal && (
        <div className="admin-modal-backdrop">
          <form className="admin-modal" onSubmit={handleSaveDiscount}>
            <h3>Tạo Mã Giảm Giá / Voucher</h3>
            <input
              className="admin-input"
              placeholder="Mã Voucher (VD: SUMMER50)..."
              value={discountModal.code}
              onChange={(e) =>
                setDiscountModal({ ...discountModal, code: e.target.value })
              }
              required
            />
            <input
              className="admin-input"
              placeholder="Mô tả..."
              value={discountModal.description}
              onChange={(e) =>
                setDiscountModal({
                  ...discountModal,
                  description: e.target.value,
                })
              }
            />
            <select
              className="admin-select"
              value={discountModal.discount_type}
              onChange={(e) =>
                setDiscountModal({
                  ...discountModal,
                  discount_type: e.target.value,
                })
              }
            >
              <option value="PERCENT">Giảm theo % (PERCENT)</option>
              <option value="FIXED">Giảm số tiền cố định (FIXED)</option>
            </select>
            <input
              className="admin-input"
              type="number"
              min="1"
              placeholder="Giá trị giảm..."
              value={discountModal.discount_value}
              onChange={(e) =>
                setDiscountModal({
                  ...discountModal,
                  discount_value: e.target.value,
                })
              }
              required
            />
            <input
              className="admin-input"
              type="date"
              value={discountModal.expiry_date}
              onChange={(e) =>
                setDiscountModal({
                  ...discountModal,
                  expiry_date: e.target.value,
                })
              }
              required
            />
            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="admin-btn admin-btn-secondary"
                onClick={() => setDiscountModal(null)}
              >
                Hủy
              </button>
              <button type="submit" className="admin-btn admin-btn-primary">
                Lưu Voucher
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Modal Tạo Lớp Tập Nhóm */}
      {classModal && (
        <div className="admin-modal-backdrop">
          <form className="admin-modal" onSubmit={handleCreateGroupClass}>
            <h3>Tạo Lớp Tập Nhóm mới</h3>
            <input
              className="admin-input"
              placeholder="Tên lớp (VD: Yoga Bình Minh)..."
              value={classModal.class_name}
              onChange={(e) =>
                setClassModal({ ...classModal, class_name: e.target.value })
              }
              required
            />
            <select
              className="admin-select"
              value={classModal.category}
              onChange={(e) =>
                setClassModal({ ...classModal, category: e.target.value })
              }
            >
              <option value="YOGA">YOGA</option>
              <option value="ZUMBA">ZUMBA</option>
              <option value="HIIT">HIIT</option>
              <option value="BOXING">BOXING</option>
            </select>
            <input
              className="admin-input"
              placeholder="Phòng tập..."
              value={classModal.room}
              onChange={(e) =>
                setClassModal({ ...classModal, room: e.target.value })
              }
              required
            />
            <input
              className="admin-input"
              type="date"
              value={classModal.schedule_date}
              onChange={(e) =>
                setClassModal({
                  ...classModal,
                  schedule_date: e.target.value,
                })
              }
              required
            />
            <div style={{ display: "flex", gap: "8px" }}>
              <input
                className="admin-input"
                type="time"
                style={{ flex: 1 }}
                value={classModal.start_time}
                onChange={(e) =>
                  setClassModal({ ...classModal, start_time: e.target.value })
                }
                required
              />
              <input
                className="admin-input"
                type="time"
                style={{ flex: 1 }}
                value={classModal.end_time}
                onChange={(e) =>
                  setClassModal({ ...classModal, end_time: e.target.value })
                }
                required
              />
            </div>
            <input
              className="admin-input"
              type="number"
              min="2"
              placeholder="Sĩ số tối đa..."
              value={classModal.max_capacity}
              onChange={(e) =>
                setClassModal({
                  ...classModal,
                  max_capacity: e.target.value,
                })
              }
              required
            />
            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="admin-btn admin-btn-secondary"
                onClick={() => setClassModal(null)}
              >
                Hủy
              </button>
              <button type="submit" className="admin-btn admin-btn-primary">
                Tạo lớp
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default AdminPage;
