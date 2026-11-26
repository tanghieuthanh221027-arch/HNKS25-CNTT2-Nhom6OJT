import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const ROLE_PRESETS = [
  {
    key: "ADMIN",
    label: "Quản trị viên (ADMIN)",
    email: "admin@duckygym.vn",
    password: "Admin123",
    defaultRoute: "/admin",
    color: "#f97316",
  },
  {
    key: "STAFF",
    label: "Lễ tân POS (STAFF)",
    email: "staff@duckygym.vn",
    password: "Staff123",
    defaultRoute: "/staff",
    color: "#3b82f6",
  },
  {
    key: "MEMBER",
    label: "Hội viên (MEMBER)",
    email: "member@duckygym.vn",
    password: "Member123",
    defaultRoute: "/member",
    color: "#22c55e",
  },
  {
    key: "MEMBER_EXPIRING",
    label: "HV sắp hết hạn (<=7 ngày)",
    email: "member04@duckygym.vn",
    password: "Member123",
    defaultRoute: "/member",
    color: "#eab308",
  },
  {
    key: "TRAINER",
    label: "Huấn luyện viên (PT)",
    email: "pt@duckygym.vn",
    password: "Trainer123",
    defaultRoute: "/pt",
    color: "#a855f7",
  },
  {
    key: "GUEST",
    label: "Khách vãng lai (No Token)",
    email: "",
    password: "",
    defaultRoute: "/",
    color: "#94a3b8",
  },
];

const PLAYGROUND_PRESETS = [
  {
    id: "health",
    module: "01. System",
    title: "Kiểm tra Health & Kết nối MySQL",
    role: "GUEST",
    method: "GET",
    path: "/health",
    params: {},
    body: null,
    expectedStatus: 200,
    note: "Kiểm tra máy chủ FastAPI và kết nối MySQL 8.0.",
  },
  {
    id: "auth-login-member",
    module: "02. Auth & RBAC",
    title: "Đăng nhập Hội viên nhận JWT Token",
    role: "GUEST",
    method: "POST",
    path: "/auth/login",
    params: {},
    body: { username: "member@duckygym.vn", password: "Member123" },
    expectedStatus: 200,
    note: "Trả về JWT Bearer Token + thông tin thẻ QR, BMI, Streak & Huy hiệu.",
  },
  {
    id: "auth-dup-email",
    module: "02. Auth & RBAC",
    title: "Đăng ký trùng Email (BR03 -> 409)",
    role: "GUEST",
    method: "POST",
    path: "/auth/register",
    params: {},
    body: {
      name: "Kiểm Thử Trùng Email",
      email: "member@duckygym.vn",
      phone: "0988776655",
      password: "Password123",
    },
    expectedStatus: 409,
    note: "Kiểm tra ràng buộc BR03 chặn trùng địa chỉ email.",
  },
  {
    id: "auth-rbac-403",
    module: "02. Auth & RBAC",
    title: "Hội viên gọi API Xuất CSV Admin (403)",
    role: "MEMBER",
    method: "GET",
    path: "/dashboard/export-csv",
    params: {},
    body: null,
    expectedStatus: 403,
    note: "Chứng minh RBAC chặn vai trò MEMBER truy cập API của ADMIN.",
  },
  {
    id: "user-me-bmi",
    module: "03. Users & BMI",
    title: "Cập nhật Chiều cao/Cân nặng tự tính BMI",
    role: "MEMBER",
    method: "PUT",
    path: "/users/me",
    params: {},
    body: {
      height_cm: 175,
      weight_kg: 70.0,
      address: "Hà Đông, Hà Nội",
    },
    expectedStatus: 200,
    note: "Tự động tính BMI = 70 / (1.75^2) = 22.9 và lưu lịch sử BodyMetric.",
  },
  {
    id: "user-body-metrics",
    module: "03. Users & BMI",
    title: "Xem chuỗi lịch sử Cân nặng & BMI",
    role: "MEMBER",
    method: "GET",
    path: "/users/body-metrics",
    params: {},
    body: null,
    expectedStatus: 200,
    note: "Dữ liệu vẽ biểu đồ tiến độ hình thể theo thời gian.",
  },
  {
    id: "user-search-members",
    module: "03. Users & BMI",
    title: "Lễ tân tìm kiếm hội viên theo từ khóa",
    role: "STAFF",
    method: "GET",
    path: "/users/members",
    params: { keyword: "0901000001", limit: 10 },
    body: null,
    expectedStatus: 200,
    note: "Tìm theo SĐT, họ tên, email hoặc mã thẻ QR.",
  },
  {
    id: "plans-list",
    module: "04. Gym Plans",
    title: "Danh sách gói tập đang mở bán",
    role: "GUEST",
    method: "GET",
    path: "/gym-plans",
    params: { page: 1, size: 10 },
    body: null,
    expectedStatus: 200,
    note: "Trả về phân trang các gói tập có status=ACTIVE.",
  },
  {
    id: "eq-list",
    module: "05. Equipment",
    title: "Danh sách thiết bị & Cảnh báo bảo trì 7 ngày",
    role: "STAFF",
    method: "GET",
    path: "/equipment/maintenance-due",
    params: { days: 7 },
    body: null,
    expectedStatus: 200,
    note: "Lọc các thiết bị quá hạn hoặc sắp đến hạn bảo trì trong 7 ngày.",
  },
  {
    id: "sub-me",
    module: "06. Subscriptions",
    title: "Xem Thẻ hội viên điện tử QR & Huy hiệu",
    role: "MEMBER",
    method: "GET",
    path: "/subscriptions/me",
    params: {},
    body: null,
    expectedStatus: 200,
    note: "Trả về mã thẻ QR, ảnh SVG Base64, hạn thẻ, streak & 3 mốc huy hiệu.",
  },
  {
    id: "sub-expiring",
    module: "06. Subscriptions",
    title: "Danh sách hội viên sắp hết hạn thẻ (<= 7 ngày)",
    role: "STAFF",
    method: "GET",
    path: "/subscriptions/expiring-soon",
    params: { within_days: 7 },
    body: null,
    expectedStatus: 200,
    note: "Phục vụ Lễ tân chăm sóc khách hàng & gửi email nhắc gia hạn.",
  },
  {
    id: "sub-email-reminder",
    module: "06. Subscriptions",
    title: "Gửi Email nhắc hạn ngầm (BackgroundTasks)",
    role: "STAFF",
    method: "POST",
    path: "/subscriptions/send-expiry-reminders",
    params: { within_days: 7 },
    body: null,
    expectedStatus: 200,
    note: "Đẩy tác vụ gửi email vào hàng đợi ngầm và lưu Notification.",
  },
  {
    id: "qr-valid",
    module: "07. QR Check-in",
    title: "Quét mã QR hợp lệ (Check-in <-> Check-out)",
    role: "STAFF",
    method: "POST",
    path: "/checkins/qr",
    params: {},
    body: { qr_code: "DG-000008" },
    expectedStatus: 200,
    note: "Quét lần 1 = CHECK_IN, quét lần 2 = CHECK_OUT (< 25ms).",
  },
  {
    id: "qr-invalid",
    module: "07. QR Check-in",
    title: "Quét mã QR lạ không tồn tại (INVALID_CODE)",
    role: "STAFF",
    method: "POST",
    path: "/checkins/qr",
    params: {},
    body: { qr_code: "DG-999999" },
    expectedStatus: 200,
    note: "Từ chối check-in với valid=false, status=INVALID_CODE.",
  },
  {
    id: "qr-history",
    module: "07. QR Check-in",
    title: "Lịch sử Check-in & Số người đang tập tại phòng",
    role: "STAFF",
    method: "GET",
    path: "/checkins/history",
    params: { page: 1, size: 10 },
    body: null,
    expectedStatus: 200,
    note: "Kèm bộ đếm active_in_gym_count thời gian thực.",
  },
  {
    id: "pt-weekly",
    module: "08. PT 1-1 Schedule",
    title: "Xem lưới lịch đặt PT 1-1 trong tuần",
    role: "MEMBER",
    method: "GET",
    path: "/pt-schedules",
    params: {},
    body: null,
    expectedStatus: 200,
    note: "Trả về danh sách 3 Master Trainer, khung giờ chuẩn và các ca đã đặt.",
  },
  {
    id: "pos-lookup",
    module: "09. POS & Invoices",
    title: "Lễ tân tra cứu nhanh SĐT tại quầy POS",
    role: "STAFF",
    method: "GET",
    path: "/pos/member-lookup",
    params: { phone: "0901000002" },
    body: null,
    expectedStatus: 200,
    note: "Tra cứu SĐT < 1 giây sử dụng B-Tree Index.",
  },
  {
    id: "pos-invoices",
    module: "09. POS & Invoices",
    title: "Danh sách hóa đơn thu ngân POS",
    role: "STAFF",
    method: "GET",
    path: "/pos/invoices",
    params: { page: 1, size: 10 },
    body: null,
    expectedStatus: 200,
    note: "Hiển thị mã hóa đơn INV-XXXXXX, gói tập, giảm giá & phương thức thu.",
  },
  {
    id: "disc-validate-ok",
    module: "10. Discounts",
    title: "Áp mã giảm giá WELCOME20 hợp lệ (-20%)",
    role: "STAFF",
    method: "POST",
    path: "/discounts/validate",
    params: {},
    body: { code: "WELCOME20", order_amount: 499000 },
    expectedStatus: 200,
    note: "Giảm 20% của 499.000đ = 99.800đ -> Còn 399.200đ.",
  },
  {
    id: "disc-validate-exp",
    module: "10. Discounts",
    title: "Áp mã giảm giá EXPIRED10 hết hạn (422)",
    role: "STAFF",
    method: "POST",
    path: "/discounts/validate",
    params: {},
    body: { code: "EXPIRED10", order_amount: 499000 },
    expectedStatus: 422,
    note: "Hệ thống chặn mã hết hạn / tạm ngưng với HTTP 422.",
  },
  {
    id: "dash-summary",
    module: "11. Dashboard & Classes",
    title: "Dashboard KPI tổng hợp từ 4 SQL Views",
    role: "ADMIN",
    method: "GET",
    path: "/dashboard/summary",
    params: {},
    body: null,
    expectedStatus: 200,
    note: "Truy vấn trực tiếp vw_monthly_revenue, vw_daily_revenue, vw_top_gym_plans, vw_monthly_new_members.",
  },
  {
    id: "classes-list",
    module: "11. Dashboard & Classes",
    title: "Danh sách Lớp tập nhóm (Yoga, Zumba, HIIT, Boxing)",
    role: "MEMBER",
    method: "GET",
    path: "/group-classes",
    params: {},
    body: null,
    expectedStatus: 200,
    note: "Hiển thị sĩ số hiện tại enrolled_count / max_capacity.",
  },
];

const RBAC_ROUTE_POLICIES = [
  {
    route: "/pages/test-lab",
    component: "SystemTestLabPage (Màn hình Chạy thử & Test Lab độc lập)",
    guest: "Chặn -> /login",
    member: "Chặn 403 -> /unauthorized",
    staff: "Chặn 403 -> /unauthorized",
    trainer: "Chặn 403 -> /unauthorized",
    admin: "✓ ĐƯỢC PHÉP (Độc quyền Admin)",
  },
  {
    route: "/admin",
    component: "AdminPage (Dashboard SQL Views, Xuất CSV, CRUD Hệ thống)",
    guest: "Chặn -> /login",
    member: "Chặn 403 -> /unauthorized",
    staff: "Giới hạn POS",
    trainer: "Chặn 403 -> /unauthorized",
    admin: "✓ ĐƯỢC PHÉP (Hiển thị nút mở Test Lab)",
  },
  {
    route: "/staff & /kiosk",
    component: "Quầy Thu ngân POS Lễ tân & Kiosk Quét QR (Ẩn hoàn toàn Test Lab)",
    guest: "Chặn -> /login",
    member: "Chặn 403 -> /unauthorized",
    staff: "✓ ĐƯỢC PHÉP",
    trainer: "Chặn 403 -> /unauthorized",
    admin: "✓ ĐƯỢC PHÉP",
  },
  {
    route: "/pt",
    component: "PTPage (Quản lý ca dạy 1-1)",
    guest: "Chặn -> /login",
    member: "Chặn 403 -> /unauthorized",
    staff: "Chặn 403 -> /unauthorized",
    trainer: "✓ ĐƯỢC PHÉP",
    admin: "✓ ĐƯỢC PHÉP",
  },
  {
    route: "/member & /member/profile",
    component: "Cổng Hội viên, Thẻ QR & Hồ sơ BMI",
    guest: "Chặn -> /login",
    member: "✓ ĐƯỢC PHÉP",
    staff: "✓ ĐƯỢC PHÉP",
    trainer: "Chặn 403 -> /unauthorized",
    admin: "✓ ĐƯỢC PHÉP",
  },
];

const labStyles = `
.lab-shell { min-height: 100vh; background: #050811; color: #e2e8f0; font-family: "JetBrains Mono", Consolas, Inter, system-ui, sans-serif; padding-bottom: 64px; }
.lab-shell * { box-sizing: border-box; }
.lab-topbar { position: sticky; top: 0; z-index: 30; background: rgba(8, 13, 26, 0.96); backdrop-filter: blur(14px); border-bottom: 1px solid rgba(56, 189, 248, 0.22); padding: 14px 28px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px; }
.lab-brand { display: flex; align-items: center; gap: 12px; color: #f8fafc; text-decoration: none; }
.lab-brand-icon { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #0ea5e9, #2563eb); color: #ffffff; display: grid; place-items: center; font-weight: 800; font-size: 13px; letter-spacing: 0.04em; }
.lab-container { max-width: 1440px; margin: 0 auto; padding: 24px 28px 0; display: flex; flex-direction: column; gap: 20px; }
.lab-card { background: #0b1222; border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 14px; padding: 20px; }
.lab-role-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.lab-role-chip { padding: 7px 12px; border-radius: 8px; border: 1px solid rgba(148,163,184,0.2); background: #0f172a; color: #cbd5e1; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease; }
.lab-role-chip:hover { border-color: #38bdf8; color: #fff; }
.lab-role-chip.is-active { background: rgba(14, 165, 233, 0.2); border-color: #38bdf8; color: #7dd3fc; }
.lab-tabs { display: flex; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid rgba(148,163,184,0.14); padding-bottom: 12px; }
.lab-tab-btn { padding: 10px 18px; border-radius: 10px; border: 1px solid rgba(148,163,184,0.16); background: #0f172a; color: #94a3b8; font-size: 13px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }
.lab-tab-btn.is-active { background: #0ea5e9; color: #041322; border-color: #38bdf8; }
.lab-btn { display: inline-flex; align-items: center; gap: 7px; padding: 9px 16px; border-radius: 9px; border: none; font-size: 13px; font-weight: 700; cursor: pointer; }
.lab-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.lab-btn-primary { background: #0ea5e9; color: #041322; }
.lab-btn-success { background: rgba(34,197,94,0.18); color: #86efac; border: 1px solid rgba(34,197,94,0.4); }
.lab-btn-secondary { background: #162036; color: #e2e8f0; border: 1px solid rgba(148,163,184,0.2); }
.lab-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.lab-kpi { background: #0f172a; border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 14px 16px; }
.lab-kpi small { display: block; color: #94a3b8; font-size: 11px; font-weight: 600; margin-bottom: 4px; }
.lab-kpi b { font-size: 22px; color: #fff; }
.lab-playground-grid { display: grid; grid-template-columns: 350px 1fr; gap: 18px; align-items: start; }
.lab-preset-list { max-height: 700px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; padding-right: 4px; }
.lab-preset-item { text-align: left; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(148,163,184,0.1); background: #0f172a; color: #e2e8f0; cursor: pointer; }
.lab-preset-item:hover, .lab-preset-item.is-selected { border-color: #38bdf8; background: rgba(14,165,233,0.14); }
.lab-input, .lab-select, .lab-textarea { width: 100%; padding: 9px 12px; border-radius: 8px; border: 1px solid rgba(148,163,184,0.22); background: #070b16; color: #e2e8f0; font-size: 13px; font-family: inherit; }
.lab-textarea { font-family: Consolas, Monaco, monospace; font-size: 12px; line-height: 1.5; resize: vertical; }
.lab-code { background: #040710; border: 1px solid rgba(56,189,248,0.16); border-radius: 10px; padding: 14px; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #cbd5e1; overflow-x: auto; white-space: pre-wrap; word-break: break-word; max-height: 420px; overflow-y: auto; margin: 0; }
.lab-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.lab-table th, .lab-table td { padding: 10px 12px; border-bottom: 1px solid rgba(148,163,184,0.1); text-align: left; vertical-align: top; }
.lab-table th { background: #0f172a; color: #7dd3fc; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em; }
.lab-badge { display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.lab-badge-pass { background: rgba(34,197,94,0.18); color: #86efac; border: 1px solid rgba(34,197,94,0.35); }
.lab-badge-fail { background: rgba(239,68,68,0.18); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
.lab-badge-pending { background: rgba(148,163,184,0.16); color: #cbd5e1; }
.lab-badge-running { background: rgba(59,130,246,0.22); color: #93c5fd; }
@media (max-width: 1024px) {
  .lab-playground-grid { grid-template-columns: 1fr; }
}
`;

const formatLocalISO = (offsetDays = 0) => {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
};

const SystemTestLabPage = () => {
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState("runner");
  const [healthState, setHealthState] = useState({
    ok: null,
    latencyMs: null,
    db: "Đang kiểm tra...",
  });
  const [roleSwitchNotice, setRoleSwitchNotice] = useState("");
  const [tokenCache, setTokenCache] = useState({});

  // Playground state
  const [selectedPresetId, setSelectedPresetId] = useState(PLAYGROUND_PRESETS[0].id);
  const [reqRole, setReqRole] = useState("GUEST");
  const [reqMethod, setReqMethod] = useState("GET");
  const [reqPath, setReqPath] = useState("/health");
  const [reqParamsText, setReqParamsText] = useState("{}");
  const [reqBodyText, setReqBodyText] = useState("");
  const [playLoading, setPlayLoading] = useState(false);
  const [playResponse, setPlayResponse] = useState(null);
  const [playHistory, setPlayHistory] = useState([]);

  // Automated Test Runner state
  const [suiteRunning, setSuiteRunning] = useState(false);
  const [moduleFilter, setModuleFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [expandedTcId, setExpandedTcId] = useState(null);
  const [testResults, setTestResults] = useState({});

  const checkBackendHealth = useCallback(async () => {
    const t0 = performance.now();
    try {
      const res = await axios.get(`${API_BASE}/health`, { timeout: 5000 });
      const elapsed = Math.round(performance.now() - t0);
      setHealthState({
        ok: true,
        latencyMs: elapsed,
        db: res.data?.database || "MySQL: connected",
      });
    } catch {
      setHealthState({
        ok: false,
        latencyMs: null,
        db: "Mất kết nối tới Backend (http://127.0.0.1:8000)",
      });
    }
  }, []);

  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  const getTokenForRole = useCallback(
    async (roleKey) => {
      if (!roleKey || roleKey === "GUEST") return null;
      if (roleKey === "CURRENT") {
        return localStorage.getItem("token");
      }
      if (tokenCache[roleKey]) return tokenCache[roleKey];

      const preset = ROLE_PRESETS.find((r) => r.key === roleKey);
      if (!preset || !preset.email) return null;

      const res = await axios.post(`${API_BASE}/auth/login`, {
        username: preset.email,
        password: preset.password,
      });
      const tok = res.data?.token?.access_token;
      if (tok) {
        setTokenCache((prev) => ({ ...prev, [roleKey]: tok }));
      }
      return tok;
    },
    [tokenCache]
  );

  const rawRequest = useCallback(
    async ({ role = "GUEST", method = "GET", path = "/health", params, data, customToken }) => {
      const token = customToken !== undefined ? customToken : await getTokenForRole(role);
      const headers = { "Content-Type": "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;

      const t0 = performance.now();
      try {
        const res = await axios({
          url: `${API_BASE}${path}`,
          method,
          params: params && Object.keys(params).length > 0 ? params : undefined,
          data: data !== undefined && data !== null ? data : undefined,
          headers,
          timeout: 15000,
        });
        const latencyMs = Math.round((performance.now() - t0) * 10) / 10;
        return {
          ok: true,
          status: res.status,
          latencyMs,
          data: res.data,
          headers: res.headers,
        };
      } catch (err) {
        const latencyMs = Math.round((performance.now() - t0) * 10) / 10;
        return {
          ok: false,
          status: err.response?.status || 0,
          latencyMs,
          data: err.response?.data || { error: err.message },
          headers: err.response?.headers || {},
        };
      }
    },
    [getTokenForRole]
  );

  const handleSelectVirtualActor = (rolePreset) => {
    setReqRole(rolePreset.key);
    setActiveTab("playground");
    setRoleSwitchNotice(
      `Sandbox Actor đang giả lập Token: ${rolePreset.label} (Phiên trình duyệt của bạn vẫn giữ nguyên quyền ADMIN)`
    );
  };

  const selectPlaygroundPreset = (preset) => {
    setSelectedPresetId(preset.id);
    setReqRole(preset.role);
    setReqMethod(preset.method);
    setReqPath(preset.path);
    setReqParamsText(JSON.stringify(preset.params || {}, null, 2));
    setReqBodyText(preset.body ? JSON.stringify(preset.body, null, 2) : "");
  };

  const handleExecutePlayground = async (e) => {
    if (e) e.preventDefault();
    setPlayLoading(true);
    let parsedParams = {};
    let parsedBody = null;
    try {
      parsedParams = reqParamsText.trim() ? JSON.parse(reqParamsText) : {};
    } catch {
      setPlayResponse({
        status: 0,
        latencyMs: 0,
        data: { error: "Query Params không đúng định dạng JSON!" },
      });
      setPlayLoading(false);
      return;
    }
    if (reqBodyText.trim() && reqMethod !== "GET") {
      try {
        parsedBody = JSON.parse(reqBodyText);
      } catch {
        setPlayResponse({
          status: 0,
          latencyMs: 0,
          data: { error: "Request Body không đúng định dạng JSON!" },
        });
        setPlayLoading(false);
        return;
      }
    }

    const result = await rawRequest({
      role: reqRole,
      method: reqMethod,
      path: reqPath.startsWith("/") ? reqPath : `/${reqPath}`,
      params: parsedParams,
      data: parsedBody,
    });
    setPlayResponse(result);
    setPlayHistory((prev) => [
      {
        id: Date.now(),
        time: new Date().toLocaleTimeString("vi-VN"),
        role: reqRole,
        method: reqMethod,
        path: reqPath,
        status: result.status,
        latencyMs: result.latencyMs,
      },
      ...prev.slice(0, 14),
    ]);
    setPlayLoading(false);
  };

  // Build 36 comprehensive E2E Test Cases covering all 11 modules
  const testCases = useMemo(
    () => [
      {
        id: "TC-SYS-01",
        module: "01. System & Health",
        name: "Kiểm tra trạng thái máy chủ FastAPI & kết nối MySQL 8.0",
        expected: "HTTP 200 OK · success=true · database='MySQL: connected'",
        run: async () => {
          const r = await rawRequest({ role: "GUEST", method: "GET", path: "/health" });
          return {
            pass: r.status === 200 && r.data?.success === true,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.database || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-AUTH-01",
        module: "02. Auth & RBAC",
        name: "Đăng ký hội viên mới hợp lệ (Tự tạo User + Member + Thẻ QR)",
        expected: "HTTP 201 Created · Trả về user_id mới",
        run: async (ctx) => {
          const suffix = String(Date.now()).slice(-7);
          const email = `autotest_${suffix}@duckygym.vn`;
          const phone = `097${suffix}`;
          ctx.tempMember = { email, phone, password: "Password123" };
          const r = await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/register",
            data: {
              name: "Hội Viên AutoTest",
              email,
              phone,
              password: "Password123",
            },
          });
          return {
            pass: r.status === 201 && Boolean(r.data?.user_id),
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · user_id=${r.data?.user_id} (${email})`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-AUTH-02",
        module: "02. Auth & RBAC",
        name: "Chặn đăng ký trùng địa chỉ Email đã tồn tại (Quy tắc BR03)",
        expected: "HTTP 409 Conflict · error_code='CONFLICT'",
        run: async () => {
          const r = await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/register",
            data: {
              name: "Trùng Email",
              email: "member@duckygym.vn",
              phone: "0961234567",
              password: "Password123",
            },
          });
          return {
            pass: r.status === 409,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-AUTH-03",
        module: "02. Auth & RBAC",
        name: "Chặn đăng ký trùng Số điện thoại đã tồn tại (Quy tắc BR03)",
        expected: "HTTP 409 Conflict · Số điện thoại đã tồn tại",
        run: async () => {
          const r = await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/register",
            data: {
              name: "Trùng SĐT",
              email: `uniq_${Date.now()}@duckygym.vn`,
              phone: "0901000001",
              password: "Password123",
            },
          });
          return {
            pass: r.status === 409,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-AUTH-04",
        module: "02. Auth & RBAC",
        name: "Chặn đăng ký SĐT sai định dạng hoặc mật khẩu < 8 ký tự",
        expected: "HTTP 422 Unprocessable Entity · VALIDATION_ERROR",
        run: async () => {
          const r = await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/register",
            data: {
              name: "Sai Format",
              email: "badformat@duckygym.vn",
              phone: "abc1234567",
              password: "123",
            },
          });
          return {
            pass: r.status === 422,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.error_code || ""}: ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-AUTH-05",
        module: "02. Auth & RBAC",
        name: "Đăng nhập xác thực JWT thành công đủ 4 vai trò (ADMIN, STAFF, MEMBER, TRAINER)",
        expected: "Cả 4 tài khoản trả HTTP 200 OK kèm JWT Token & đúng role",
        run: async () => {
          const roles = ["ADMIN", "STAFF", "MEMBER", "TRAINER"];
          const checks = [];
          let totalMs = 0;
          for (const rk of roles) {
            const preset = ROLE_PRESETS.find((p) => p.key === rk);
            const r = await rawRequest({
              role: "GUEST",
              method: "POST",
              path: "/auth/login",
              data: { username: preset.email, password: preset.password },
            });
            totalMs += r.latencyMs;
            checks.push({
              role: rk,
              status: r.status,
              gotRole: r.data?.user?.role,
              hasToken: Boolean(r.data?.token?.access_token),
            });
          }
          const allOk = checks.every(
            (c) => c.status === 200 && c.gotRole === c.role && c.hasToken
          );
          return {
            pass: allOk,
            status: allOk ? 200 : 401,
            latencyMs: Math.round(totalMs * 10) / 10,
            actual: checks.map((c) => `${c.role}:${c.status}`).join(", "),
            payload: checks,
          };
        },
      },
      {
        id: "TC-AUTH-06",
        module: "02. Auth & RBAC",
        name: "Đăng nhập thất bại khi nhập sai mật khẩu",
        expected: "HTTP 401 Unauthorized · UNAUTHORIZED",
        run: async () => {
          const r = await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/login",
            data: { username: "member@duckygym.vn", password: "WrongPassword999" },
          });
          return {
            pass: r.status === 401,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-AUTH-07",
        module: "02. Auth & RBAC",
        name: "Chặn truy cập API bảo vệ khi thiếu JWT Bearer Token",
        expected: "HTTP 401 Unauthorized",
        run: async () => {
          const r = await rawRequest({
            role: "GUEST",
            method: "GET",
            path: "/users/me",
            customToken: null,
          });
          return {
            pass: r.status === 401,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-AUTH-08",
        module: "02. Auth & RBAC",
        name: "Phân quyền RBAC: Chặn MEMBER gọi API quản trị & Kiosk POS (403 Forbidden)",
        expected: "HTTP 403 Forbidden cho cả /checkins/qr và /dashboard/export-csv",
        run: async () => {
          const r1 = await rawRequest({
            role: "MEMBER",
            method: "POST",
            path: "/checkins/qr",
            data: { qr_code: "DG-000006" },
          });
          const r2 = await rawRequest({
            role: "MEMBER",
            method: "GET",
            path: "/dashboard/export-csv",
          });
          return {
            pass: r1.status === 403 && r2.status === 403,
            status: r1.status,
            latencyMs: Math.round((r1.latencyMs + r2.latencyMs) * 10) / 10,
            actual: `POST /checkins/qr -> ${r1.status}, GET /dashboard/export-csv -> ${r2.status}`,
            payload: { checkin_qr: r1.data, export_csv: r2.data },
          };
        },
      },
      {
        id: "TC-USER-01",
        module: "03. Users, Profile & BMI",
        name: "Xem hồ sơ cá nhân, mã thẻ QR, Streak & Huy hiệu (GET /users/me)",
        expected: "HTTP 200 OK · Có member_code, bmi, badges (3 mốc)",
        run: async () => {
          const r = await rawRequest({ role: "MEMBER", method: "GET", path: "/users/me" });
          return {
            pass:
              r.status === 200 &&
              Boolean(r.data?.member_code) &&
              Array.isArray(r.data?.badges) &&
              r.data.badges.length === 3,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · Mã thẻ ${r.data?.member_code} · Streak ${r.data?.streak_days} ngày`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-USER-02",
        module: "03. Users, Profile & BMI",
        name: "Cập nhật Chiều cao 175cm & Cân nặng 70kg -> Tự động tính BMI = 22.9",
        expected: "HTTP 200 OK · bmi = 22.9",
        run: async () => {
          const r = await rawRequest({
            role: "MEMBER",
            method: "PUT",
            path: "/users/me",
            data: { height_cm: 175, weight_kg: 70.0 },
          });
          const bmiNum = Number(r.data?.bmi);
          return {
            pass: r.status === 200 && Math.abs(bmiNum - 22.9) < 0.05,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · height=175cm, weight=70kg => BMI=${r.data?.bmi}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-USER-03",
        module: "03. Users, Profile & BMI",
        name: "Ghi nhận chỉ số cơ thể InBody mới & Truy vấn chuỗi lịch sử Body Metrics",
        expected: "POST 201 Created & GET 200 OK (danh sách >= 1 bản ghi)",
        run: async () => {
          const p = await rawRequest({
            role: "MEMBER",
            method: "POST",
            path: "/users/body-metrics",
            data: {
              height_cm: 175,
              weight_kg: 69.5,
              body_fat_pct: 16.5,
              muscle_mass_kg: 33.2,
              notes: "AutoTest InBody Check",
            },
          });
          const g = await rawRequest({
            role: "MEMBER",
            method: "GET",
            path: "/users/body-metrics",
          });
          return {
            pass: p.status === 201 && g.status === 200 && Array.isArray(g.data) && g.data.length > 0,
            status: p.status,
            latencyMs: Math.round((p.latencyMs + g.latencyMs) * 10) / 10,
            actual: `POST -> ${p.status} (BMI ${p.data?.bmi}), GET -> ${g.data?.length || 0} lần đo`,
            payload: { created: p.data, total_records: g.data?.length },
          };
        },
      },
      {
        id: "TC-USER-04",
        module: "03. Users, Profile & BMI",
        name: "Đổi mật khẩu bị chặn khi nhập sai mật khẩu hiện tại",
        expected: "HTTP 401 Unauthorized · Mật khẩu hiện tại không chính xác",
        run: async () => {
          const r = await rawRequest({
            role: "MEMBER",
            method: "PUT",
            path: "/users/me",
            data: {
              current_password: "WrongCurrentPassword",
              new_password: "NewPassword123",
            },
          });
          return {
            pass: r.status === 401,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-USER-05",
        module: "03. Users, Profile & BMI",
        name: "Danh sách HLV đang hoạt động & Lễ tân tìm kiếm hội viên",
        expected: "HTTP 200 OK · >= 3 HLV & tìm thấy hội viên 0901000001",
        run: async () => {
          const r1 = await rawRequest({ role: "GUEST", method: "GET", path: "/users/trainers" });
          const r2 = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/users/members",
            params: { keyword: "0901000001" },
          });
          return {
            pass:
              r1.status === 200 &&
              Array.isArray(r1.data) &&
              r1.data.length >= 3 &&
              r2.status === 200 &&
              r2.data.length >= 1,
            status: r2.status,
            latencyMs: Math.round((r1.latencyMs + r2.latencyMs) * 10) / 10,
            actual: `Trainers=${r1.data?.length}, Search '0901000001'=${r2.data?.length} HV`,
            payload: { trainers: r1.data, members: r2.data },
          };
        },
      },
      {
        id: "TC-PLAN-01",
        module: "04. Gym Plans CRUD",
        name: "Xem danh sách gói tập mở bán, lọc theo giá & xem chi tiết gói #1",
        expected: "HTTP 200 OK · Trả về danh sách gói ACTIVE và chi tiết gói #1",
        run: async () => {
          const r1 = await rawRequest({
            role: "GUEST",
            method: "GET",
            path: "/gym-plans",
            params: { min_price: 400000, max_price: 5000000 },
          });
          const firstId = r1.data?.items?.[0]?.plan_id || 1;
          const r2 = await rawRequest({
            role: "GUEST",
            method: "GET",
            path: `/gym-plans/${firstId}`,
          });
          return {
            pass: r1.status === 200 && r1.data?.items?.length >= 1 && r2.status === 200,
            status: r1.status,
            latencyMs: Math.round((r1.latencyMs + r2.latencyMs) * 10) / 10,
            actual: `Tổng ${r1.data?.total} gói ACTIVE · Chi tiết: ${r2.data?.plan_name}`,
            payload: { list_total: r1.data?.total, detail: r2.data },
          };
        },
      },
      {
        id: "TC-PLAN-02",
        module: "04. Gym Plans CRUD",
        name: "Admin tạo gói tập mới -> Cập nhật giá -> Ngừng kinh doanh an toàn (DISCONTINUED)",
        expected: "POST 201 -> PUT 200 -> DELETE 200 (status='DISCONTINUED')",
        run: async () => {
          const uniqueName = `Gói Test Lab ${String(Date.now()).slice(-6)}`;
          const c = await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/gym-plans",
            data: {
              plan_name: uniqueName,
              category: "Gói Kiểm Thử",
              duration_days: 45,
              price: 750000,
              description: "Gói tạo tự động từ System Test Lab",
            },
          });
          if (c.status !== 201) {
            return {
              pass: false,
              status: c.status,
              latencyMs: c.latencyMs,
              actual: `Tạo thất bại: ${c.data?.message}`,
              payload: c.data,
            };
          }
          const pid = c.data.plan_id;
          const u = await rawRequest({
            role: "ADMIN",
            method: "PUT",
            path: `/gym-plans/${pid}`,
            data: { price: 790000 },
          });
          const d = await rawRequest({
            role: "ADMIN",
            method: "DELETE",
            path: `/gym-plans/${pid}`,
          });
          return {
            pass: u.status === 200 && d.status === 200 && d.data?.status === "DISCONTINUED",
            status: d.status,
            latencyMs: Math.round((c.latencyMs + u.latencyMs + d.latencyMs) * 10) / 10,
            actual: `Plan #${pid}: Created(201) -> Updated(790k) -> Discontinued(${d.data?.status})`,
            payload: { created: c.data, updated: u.data, discontinued: d.data },
          };
        },
      },
      {
        id: "TC-PLAN-03",
        module: "04. Gym Plans CRUD",
        name: "Chặn tạo gói tập trùng tên (409) hoặc giá <= 0 (422)",
        expected: "Trùng tên -> 409 Conflict · Giá âm/0 -> 422 Validation Error",
        run: async () => {
          const rDup = await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/gym-plans",
            data: {
              plan_name: "Starter 1 Tháng",
              category: "Gói Cơ Bản",
              duration_days: 30,
              price: 499000,
            },
          });
          const rNeg = await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/gym-plans",
            data: {
              plan_name: `Gói Giá Âm ${Date.now()}`,
              category: "Gói Lỗi",
              duration_days: 30,
              price: 0,
            },
          });
          return {
            pass: rDup.status === 409 && rNeg.status === 422,
            status: rDup.status,
            latencyMs: Math.round((rDup.latencyMs + rNeg.latencyMs) * 10) / 10,
            actual: `Trùng tên -> ${rDup.status}, Giá=0 -> ${rNeg.status}`,
            payload: { duplicate: rDup.data, zero_price: rNeg.data },
          };
        },
      },
      {
        id: "TC-EQ-01",
        module: "05. Equipment & Maintenance",
        name: "Xem danh sách thiết bị phòng gym & Lọc thiết bị đến hạn bảo trì 7 ngày",
        expected: "HTTP 200 OK · Có trường maintenance_due_count & due_count",
        run: async () => {
          const r1 = await rawRequest({ role: "GUEST", method: "GET", path: "/equipment" });
          const r2 = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/equipment/maintenance-due",
            params: { days: 7 },
          });
          return {
            pass: r1.status === 200 && r1.data?.total >= 5 && r2.status === 200,
            status: r1.status,
            latencyMs: Math.round((r1.latencyMs + r2.latencyMs) * 10) / 10,
            actual: `Tổng ${r1.data?.total} máy · Đến hạn <=7 ngày: ${r2.data?.due_count} máy`,
            payload: { total: r1.data?.total, due: r2.data },
          };
        },
      },
      {
        id: "TC-EQ-02",
        module: "05. Equipment & Maintenance",
        name: "Vòng đời Thiết bị: Admin thêm máy BAO_TRI -> Lễ tân hoàn tất bảo trì -> Admin xóa máy test",
        expected: "POST 201 -> POST /maintain 200 (HOAT_DONG) -> DELETE 200",
        run: async () => {
          const eqName = `Tạ Tay TestLab #${String(Date.now()).slice(-5)}`;
          const c = await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/equipment",
            data: {
              name: eqName,
              zone: "Khu Free Weights",
              status: "BAO_TRI",
              maintenance_interval_days: 30,
            },
          });
          if (c.status !== 201) {
            return {
              pass: false,
              status: c.status,
              latencyMs: c.latencyMs,
              actual: `Lỗi tạo thiết bị: ${c.data?.message}`,
              payload: c.data,
            };
          }
          const eqId = c.data.equipment_id;
          const m = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: `/equipment/${eqId}/maintain`,
          });
          const d = await rawRequest({
            role: "ADMIN",
            method: "DELETE",
            path: `/equipment/${eqId}`,
          });
          return {
            pass: m.status === 200 && m.data?.status === "HOAT_DONG" && d.status === 200,
            status: m.status,
            latencyMs: Math.round((c.latencyMs + m.latencyMs + d.latencyMs) * 10) / 10,
            actual: `Created(#${eqId}) -> Maintained(${m.data?.status}) -> Deleted(200)`,
            payload: { maintained: m.data, deleted: d.data },
          };
        },
      },
      {
        id: "TC-EQ-03",
        module: "05. Equipment & Maintenance",
        name: "Chặn tạo thiết bị có trạng thái không hợp lệ",
        expected: "HTTP 422 BusinessRuleException",
        run: async () => {
          const r = await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/equipment",
            data: {
              name: `Máy Trạng Thái Lỗi ${Date.now()}`,
              zone: "Khu Cardio",
              status: "SAI_TRANG_THAI",
            },
          });
          return {
            pass: r.status === 422,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-SUB-01",
        module: "06. Subscriptions & QR Card",
        name: "Xem thẻ hội viên điện tử QR (GET /subscriptions/me)",
        expected: "HTTP 200 OK · qr_base64 hợp lệ & card_status='ACTIVE'",
        run: async () => {
          const r = await rawRequest({
            role: "MEMBER",
            method: "GET",
            path: "/subscriptions/me",
          });
          return {
            pass:
              r.status === 200 &&
              Boolean(r.data?.qr_base64) &&
              Boolean(r.data?.member_code),
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `Thẻ ${r.data?.member_code} (${r.data?.card_status}) · Còn ${r.data?.days_remaining} ngày`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-SUB-02",
        module: "06. Subscriptions & QR Card",
        name: "Hội viên mới đăng ký gói tập lần đầu (NEW) -> Tiếp tục mua gói 2 tự động nối tiếp hạn (RENEW - BR06)",
        expected: "Lần 1: NEW · Lần 2: RENEW với start_date = end_date_1 + 1 ngày",
        run: async (ctx) => {
          let tempCreds = ctx.tempMember;
          if (!tempCreds) {
            const sfx = String(Date.now()).slice(-7);
            tempCreds = {
              email: `subtest_${sfx}@duckygym.vn`,
              phone: `098${sfx}`,
              password: "Password123",
            };
            await rawRequest({
              role: "GUEST",
              method: "POST",
              path: "/auth/register",
              data: { name: "HV Test Gia Hạn", ...tempCreds },
            });
          }
          const loginRes = await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/login",
            data: { username: tempCreds.email, password: tempCreds.password },
          });
          const tok = loginRes.data?.token?.access_token;
          ctx.tempMemberToken = tok;
          ctx.tempMemberCode = loginRes.data?.user?.member_code;

          const sub1 = await rawRequest({
            method: "POST",
            path: "/subscriptions",
            customToken: tok,
            data: { plan_id: 1, payment_method: "BANK_TRANSFER" },
          });
          const sub2 = await rawRequest({
            method: "POST",
            path: "/subscriptions",
            customToken: tok,
            data: { plan_id: 1, payment_method: "CASH" },
          });
          return {
            pass:
              sub1.status === 201 &&
              sub1.data?.subscription_type === "NEW" &&
              sub2.status === 201 &&
              sub2.data?.subscription_type === "RENEW" &&
              sub2.data?.start_date > sub1.data?.end_date,
            status: sub2.status,
            latencyMs: Math.round((sub1.latencyMs + sub2.latencyMs) * 10) / 10,
            actual: `Gói 1 (${sub1.data?.subscription_type} -> ${sub1.data?.end_date}) | Gói 2 (${sub2.data?.subscription_type}: ${sub2.data?.start_date} -> ${sub2.data?.end_date})`,
            payload: { first_sub: sub1.data, renew_sub: sub2.data },
          };
        },
      },
      {
        id: "TC-SUB-03",
        module: "06. Subscriptions & QR Card",
        name: "Chặn tài khoản ADMIN/STAFF gọi API tự đăng ký gói tập hội viên",
        expected: "HTTP 422 BusinessRuleException",
        run: async () => {
          const r = await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/subscriptions",
            data: { plan_id: 1, payment_method: "CASH" },
          });
          return {
            pass: r.status === 422,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-SUB-04",
        module: "06. Subscriptions & QR Card",
        name: "Lọc danh sách thẻ sắp hết hạn & Gửi Email nhắc hạn qua BackgroundTasks",
        expected: "GET /expiring-soon 200 OK & POST /send-expiry-reminders 200 OK",
        run: async () => {
          const r1 = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/subscriptions/expiring-soon",
            params: { within_days: 7 },
          });
          const r2 = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/subscriptions/send-expiry-reminders",
            params: { within_days: 7 },
          });
          return {
            pass: r1.status === 200 && r2.status === 200 && r2.data?.queued_count >= 0,
            status: r2.status,
            latencyMs: Math.round((r1.latencyMs + r2.latencyMs) * 10) / 10,
            actual: `Sắp hết hạn: ${r1.data?.total} HV · Đã xếp hàng gửi: ${r2.data?.queued_count} email`,
            payload: { expiring: r1.data, reminders: r2.data },
          };
        },
      },
      {
        id: "TC-QR-01",
        module: "07. QR Check-in Kiosk",
        name: "Quét mã QR hợp lệ 2 lần liên tiếp (CHECK_IN -> CHECK_OUT) & Hiệu năng < 1000ms",
        expected: "Lần 1: CHECK_IN · Lần 2: CHECK_OUT · response_time_ms < 1000ms",
        run: async (ctx) => {
          const code = ctx.tempMemberCode || "DG-000008";
          const scan1 = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/checkins/qr",
            data: { qr_code: code },
          });
          const scan2 = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/checkins/qr",
            data: { qr_code: code },
          });
          const actions = [scan1.data?.action, scan2.data?.action];
          const hasInAndOut =
            actions.includes("CHECK_IN") && actions.includes("CHECK_OUT");
          const fastEnough =
            (scan1.data?.response_time_ms || 0) < 1000 &&
            (scan2.data?.response_time_ms || 0) < 1000;
          return {
            pass: scan1.status === 200 && scan2.status === 200 && hasInAndOut && fastEnough,
            status: scan2.status,
            latencyMs: Math.round((scan1.latencyMs + scan2.latencyMs) * 10) / 10,
            actual: `${actions[0]}(${scan1.data?.response_time_ms}ms) -> ${actions[1]}(${scan2.data?.response_time_ms}ms)`,
            payload: { scan1: scan1.data, scan2: scan2.data },
          };
        },
      },
      {
        id: "TC-QR-02",
        module: "07. QR Check-in Kiosk",
        name: "Quét thẻ đã hết hạn (EXPIRED_CARD) & Mã QR không tồn tại (INVALID_CODE)",
        expected: "valid=false · Trả về EXPIRED_CARD và INVALID_CODE",
        run: async () => {
          const mems = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/users/members",
            params: { keyword: "member18@duckygym.vn" },
          });
          const expCode = mems.data?.[0]?.member_code || "DG-000023";
          const rExp = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/checkins/qr",
            data: { qr_code: expCode },
          });
          const rInv = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/checkins/qr",
            data: { qr_code: "DG-999999" },
          });
          return {
            pass:
              rExp.status === 200 &&
              rExp.data?.valid === false &&
              rExp.data?.status === "EXPIRED_CARD" &&
              rInv.status === 200 &&
              rInv.data?.valid === false &&
              rInv.data?.status === "INVALID_CODE",
            status: 200,
            latencyMs: Math.round((rExp.latencyMs + rInv.latencyMs) * 10) / 10,
            actual: `Thẻ hết hạn -> ${rExp.data?.status} | Mã lạ -> ${rInv.data?.status}`,
            payload: { expired: rExp.data, invalid: rInv.data },
          };
        },
      },
      {
        id: "TC-QR-03",
        module: "07. QR Check-in Kiosk",
        name: "Phân quyền lịch sử Check-in: MEMBER chỉ thấy cá nhân, STAFF thấy toàn phòng gym",
        expected: "HTTP 200 OK · Mọi bản ghi của MEMBER đều thuộc chính hội viên đó",
        run: async () => {
          const meRes = await rawRequest({ role: "MEMBER", method: "GET", path: "/users/me" });
          const myMemberId = meRes.data?.member_id;
          const mHist = await rawRequest({
            role: "MEMBER",
            method: "GET",
            path: "/checkins/history",
            params: { page: 1, size: 20 },
          });
          const sHist = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/checkins/history",
            params: { page: 1, size: 20 },
          });
          const onlyMine = (mHist.data?.items || []).every(
            (i) => i.member_id === myMemberId
          );
          return {
            pass:
              mHist.status === 200 &&
              sHist.status === 200 &&
              onlyMine &&
              sHist.data?.total >= mHist.data?.total,
            status: 200,
            latencyMs: Math.round((mHist.latencyMs + sHist.latencyMs) * 10) / 10,
            actual: `MEMBER thấy ${mHist.data?.total} lượt cá nhân · STAFF thấy ${sHist.data?.total} lượt toàn CLB`,
            payload: { member_total: mHist.data?.total, staff_total: sHist.data?.total },
          };
        },
      },
      {
        id: "TC-PT-01",
        module: "08. PT 1-1 Scheduling",
        name: "Đặt lịch PT 1-1 trong ca trực mở -> Chặn đặt trùng giờ (409 BR13/BR14) -> Chặn MEMBER tự duyệt (403)",
        expected: "Đặt lịch 201 -> Đặt trùng 409 -> MEMBER tự confirm 403",
        run: async (ctx) => {
          const trRes = await rawRequest({ role: "GUEST", method: "GET", path: "/users/trainers" });
          const trainerId = trRes.data?.[0]?.user_id;
          const dayOffset = 10 + (Math.floor(Date.now() / 1000) % 40);
          const futureDate = formatLocalISO(dayOffset);
          await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/pt-schedules/work-slots",
            data: {
              trainer_id: trainerId,
              work_date: futureDate,
              start_time: "11:00",
              end_time: "12:00",
            },
          });
          const tok = ctx.tempMemberToken || (await getTokenForRole("MEMBER"));
          const book1 = await rawRequest({
            method: "POST",
            path: "/pt-schedules",
            customToken: tok,
            data: {
              trainer_id: trainerId,
              booking_date: futureDate,
              start_time: "11:00",
            },
          });
          ctx.ptBookingId = book1.data?.booking_id;

          const bookDup = await rawRequest({
            role: "MEMBER",
            method: "POST",
            path: "/pt-schedules",
            data: {
              trainer_id: trainerId,
              booking_date: futureDate,
              start_time: "11:00",
            },
          });
          const illegalConfirm = await rawRequest({
            method: "PATCH",
            path: `/pt-schedules/${ctx.ptBookingId}/confirm`,
            customToken: tok,
          });
          return {
            pass:
              book1.status === 201 &&
              bookDup.status === 409 &&
              illegalConfirm.status === 403,
            status: book1.status,
            latencyMs: Math.round(
              (book1.latencyMs + bookDup.latencyMs + illegalConfirm.latencyMs) * 10
            ) / 10,
            actual: `Book(#${ctx.ptBookingId})->${book1.status}, Overlap->${bookDup.status}, MemberConfirm->${illegalConfirm.status}`,
            payload: { booked: book1.data, overlap: bookDup.data, member_confirm: illegalConfirm.data },
          };
        },
      },
      {
        id: "TC-PT-02",
        module: "08. PT 1-1 Scheduling",
        name: "Máy trạng thái PT (Mục 4.5 & 5.6): PATCH /confirm -> PATCH /complete (trừ 1 buổi PT) & chặn chuyển ngược trạng thái kết thúc",
        expected: "CONFIRMED (200) -> COMPLETED (200, trừ buổi) -> Hủy sau COMPLETED bị chặn 400",
        run: async (ctx) => {
          if (!ctx.ptBookingId) {
            return {
              pass: false,
              status: 0,
              latencyMs: 0,
              actual: "Chưa có booking từ TC-PT-01",
              payload: null,
            };
          }
          const conf = await rawRequest({
            role: "TRAINER",
            method: "PATCH",
            path: `/pt-schedules/${ctx.ptBookingId}/confirm`,
          });
          const beforeSessions = conf.data?.sessions_remaining;
          const comp = await rawRequest({
            role: "TRAINER",
            method: "PATCH",
            path: `/pt-schedules/${ctx.ptBookingId}/complete`,
          });
          const afterSessions = comp.data?.sessions_remaining;
          const illegalAfterTerminal = await rawRequest({
            role: "ADMIN",
            method: "PATCH",
            path: `/pt-schedules/${ctx.ptBookingId}/cancel`,
            data: { reason: "Thử hủy ca đã hoàn thành" },
          });
          return {
            pass:
              conf.status === 200 &&
              conf.data?.status === "CONFIRMED" &&
              comp.status === 200 &&
              comp.data?.status === "COMPLETED" &&
              afterSessions === beforeSessions - 1 &&
              illegalAfterTerminal.status === 400,
            status: comp.status,
            latencyMs: Math.round(
              (conf.latencyMs + comp.latencyMs + illegalAfterTerminal.latencyMs) * 10
            ) / 10,
            actual: `#${ctx.ptBookingId}: CONFIRMED -> COMPLETED (Buổi PT: ${beforeSessions} -> ${afterSessions}) · CancelAfterComplete -> ${illegalAfterTerminal.status}`,
            payload: { confirmed: conf.data, completed: comp.data, blocked_cancel: illegalAfterTerminal.data },
          };
        },
      },
      {
        id: "TC-PAST-01",
        module: "08. PT 1-1 Scheduling",
        name: "[BR15 - Mục 4.4 & 7.3] Chặn đặt lịch PT vào giờ đã qua trong ngày hôm nay",
        expected: "HTTP 400 Bad Request (datetime(booking_date, start_time) <= now + 30p)",
        run: async () => {
          const trRes = await rawRequest({ role: "GUEST", method: "GET", path: "/users/trainers" });
          const trainerId = trRes.data?.[0]?.user_id;
          const r = await rawRequest({
            role: "MEMBER",
            method: "POST",
            path: "/pt-schedules",
            data: {
              trainer_id: trainerId,
              booking_date: formatLocalISO(0),
              start_time: "00:05",
            },
          });
          return {
            pass: r.status === 400,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-QUOTA-01",
        module: "08. PT 1-1 Scheduling",
        name: "[BR16 - Mục 4.4 & 7.3] Chặn hội viên chưa có gói PT / hết số buổi tập PT (sessions_remaining=0) đặt lịch",
        expected: "HTTP 403 Forbidden (BR16)",
        run: async () => {
          const sfx = String(Date.now()).slice(-7);
          const email = `noquota_${sfx}@duckygym.vn`;
          const phone = `092${sfx}`;
          await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/register",
            data: { name: "HV Hết Buổi PT", email, phone, password: "Password123" },
          });
          const lg = await rawRequest({
            role: "GUEST",
            method: "POST",
            path: "/auth/login",
            data: { username: email, password: "Password123" },
          });
          const noQuotaTok = lg.data?.token?.access_token;
          const trRes = await rawRequest({ role: "GUEST", method: "GET", path: "/users/trainers" });
          const r = await rawRequest({
            method: "POST",
            path: "/pt-schedules",
            customToken: noQuotaTok,
            data: {
              trainer_id: trRes.data?.[0]?.user_id,
              booking_date: formatLocalISO(7),
              start_time: "09:00",
            },
          });
          return {
            pass: r.status === 403,
            status: r.status,
            latencyMs: r.latencyMs,
            actual: `HTTP ${r.status} · ${r.data?.message || ""}`,
            payload: r.data,
          };
        },
      },
      {
        id: "TC-CANCEL-LATE",
        module: "08. PT 1-1 Scheduling",
        name: "[BR17 - Mục 4.4 & 7.3] Chặn hội viên tự hủy ca sát giờ (< 2 tiếng trước giờ bắt đầu)",
        expected: "Đặt ca cách hiện tại ~60 phút -> Hội viên gọi PATCH /cancel trả HTTP 400 Bad Request",
        run: async (ctx) => {
          const trRes = await rawRequest({ role: "GUEST", method: "GET", path: "/users/trainers" });
          const trainerId = trRes.data?.[0]?.user_id;
          const targetDt = new Date(Date.now() + 65 * 60 * 1000);
          const y = targetDt.getFullYear();
          const m = String(targetDt.getMonth() + 1).padStart(2, "0");
          const d = String(targetDt.getDate()).padStart(2, "0");
          const hh = String(targetDt.getHours()).padStart(2, "0");
          const mm = String(targetDt.getMinutes()).padStart(2, "0");
          const endDt = new Date(targetDt.getTime() + 60 * 60 * 1000);
          const ehh = String(endDt.getHours()).padStart(2, "0");
          const emm = String(endDt.getMinutes()).padStart(2, "0");
          const dateStr = `${y}-${m}-${d}`;

          await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/pt-schedules/work-slots",
            data: {
              trainer_id: trainerId,
              work_date: dateStr,
              start_time: `${hh}:${mm}`,
              end_time: `${ehh}:${emm}`,
              overnight: endDt.getDate() !== targetDt.getDate(),
            },
          });
          const tok = ctx.tempMemberToken || (await getTokenForRole("MEMBER"));
          const bk = await rawRequest({
            method: "POST",
            path: "/pt-schedules",
            customToken: tok,
            data: {
              trainer_id: trainerId,
              booking_date: dateStr,
              start_time: `${hh}:${mm}`,
              end_time: `${ehh}:${emm}`,
              overnight: endDt.getDate() !== targetDt.getDate(),
            },
          });
          const lateCancel = await rawRequest({
            method: "PATCH",
            path: `/pt-schedules/${bk.data?.booking_id}/cancel`,
            customToken: tok,
            data: { reason: "Thử hủy sát giờ < 2 tiếng" },
          });
          // Admin dọn lịch test sau khi kiểm chứng chặn hội viên
          if (bk.data?.booking_id) {
            await rawRequest({
              role: "ADMIN",
              method: "PATCH",
              path: `/pt-schedules/${bk.data.booking_id}/cancel`,
              data: { reason: "Admin cleanup test slot" },
            });
          }
          return {
            pass: bk.status === 201 && lateCancel.status === 400,
            status: lateCancel.status,
            latencyMs: Math.round((bk.latencyMs + lateCancel.latencyMs) * 10) / 10,
            actual: `Book(+65p)->${bk.status}, MemberLateCancel->${lateCancel.status} (${lateCancel.data?.message || ""})`,
            payload: lateCancel.data,
          };
        },
      },
      {
        id: "TC-PT-NOSHOW",
        module: "08. PT 1-1 Scheduling",
        name: "[Mục 4.5 & 5.6] Học viên vắng mặt (CONFIRMED -> NO_SHOW) & Vẫn trừ 1 buổi PT",
        expected: "PATCH /no-show trả HTTP 200 · status='NO_SHOW' · trừ 1 buổi sessions_remaining",
        run: async (ctx) => {
          const trRes = await rawRequest({ role: "GUEST", method: "GET", path: "/users/trainers" });
          const trainerId = trRes.data?.[1]?.user_id || trRes.data?.[0]?.user_id;
          const futureDate = formatLocalISO(14 + (Math.floor(Date.now() / 1000) % 30));
          await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/pt-schedules/work-slots",
            data: {
              trainer_id: trainerId,
              work_date: futureDate,
              start_time: "12:00",
              end_time: "13:00",
            },
          });
          const tok = ctx.tempMemberToken || (await getTokenForRole("MEMBER"));
          const bk = await rawRequest({
            method: "POST",
            path: "/pt-schedules",
            customToken: tok,
            data: { trainer_id: trainerId, booking_date: futureDate, start_time: "12:00" },
          });
          const conf = await rawRequest({
            role: "ADMIN",
            method: "PATCH",
            path: `/pt-schedules/${bk.data?.booking_id}/confirm`,
          });
          const beforeRem = conf.data?.sessions_remaining;
          const ns = await rawRequest({
            role: "ADMIN",
            method: "PATCH",
            path: `/pt-schedules/${bk.data?.booking_id}/no-show`,
            data: { reason: "Học viên không đến tập" },
          });
          return {
            pass:
              ns.status === 200 &&
              ns.data?.status === "NO_SHOW" &&
              ns.data?.sessions_remaining === beforeRem - 1,
            status: ns.status,
            latencyMs: Math.round((bk.latencyMs + conf.latencyMs + ns.latencyMs) * 10) / 10,
            actual: `status=${ns.data?.status} · Buổi PT: ${beforeRem} -> ${ns.data?.sessions_remaining}`,
            payload: ns.data,
          };
        },
      },
      {
        id: "TC-PT-WORKSLOT",
        module: "08. PT 1-1 Scheduling",
        name: "[Mục 5.2 & 5.3] Chặn đặt ngoài ca trực PT (không tự tạo TrainerSchedule) & Hỗ trợ ca xuyên đêm 23:00 -> 01:00",
        expected: "Ngoài ca trực -> 400 Bad Request | Mở ca đêm 23:00-01:00 -> 201 Created",
        run: async (ctx) => {
          const trRes = await rawRequest({ role: "GUEST", method: "GET", path: "/users/trainers" });
          const trainerId = trRes.data?.[0]?.user_id;
          const tok = ctx.tempMemberToken || (await getTokenForRole("MEMBER"));
          const farDate = formatLocalISO(85); // Ngoài vùng seed 60 ngày -> chưa có ca trực

          const outsideRes = await rawRequest({
            method: "POST",
            path: "/pt-schedules",
            customToken: tok,
            data: { trainer_id: trainerId, booking_date: farDate, start_time: "08:00" },
          });

          const nightSlot = await rawRequest({
            role: "TRAINER",
            method: "POST",
            path: "/pt-schedules/work-slots",
            data: {
              trainer_id: trainerId,
              work_date: farDate,
              start_time: "23:00",
              end_time: "01:00",
              overnight: true,
            },
          });
          return {
            pass: outsideRes.status === 400 && nightSlot.status === 201,
            status: nightSlot.status,
            latencyMs: Math.round((outsideRes.latencyMs + nightSlot.latencyMs) * 10) / 10,
            actual: `Ngoài ca trực -> ${outsideRes.status} | Mở ca đêm 23:00-01:00 -> ${nightSlot.status}`,
            payload: { rejected_outside_shift: outsideRes.data, overnight_slot: nightSlot.data },
          };
        },
      },
      {
        id: "TC-PT-NODEL-WEEK53",
        module: "08. PT 1-1 Scheduling",
        name: "[Mục 1.4, 5.5 & 5.6] Cấm xóa vật lý DELETE ca tập (403) & Bắt lỗi tràn tuần ISO week=53 năm 2025 (400)",
        expected: "DELETE /pt-schedules/1 -> 403 Forbidden | GET ?week=53&year=2025 -> 400 Bad Request",
        run: async () => {
          const delRes = await rawRequest({
            role: "TRAINER",
            method: "DELETE",
            path: "/pt-schedules/1",
          });
          const w53Res = await rawRequest({
            role: "MEMBER",
            method: "GET",
            path: "/pt-schedules",
            params: { week: 53, year: 2025 },
          });
          return {
            pass: delRes.status === 403 && w53Res.status === 400,
            status: delRes.status,
            latencyMs: Math.round((delRes.latencyMs + w53Res.latencyMs) * 10) / 10,
            actual: `DELETE ca tập -> ${delRes.status} | ISO week=53 (2025) -> ${w53Res.status}`,
            payload: { delete_blocked: delRes.data, week53_handled: w53Res.data },
          };
        },
      },
      {
        id: "TC-POS-01",
        module: "09. POS & Invoices",
        name: "Tra cứu SĐT tại quầy POS: Hội viên có sẵn (found=true) & Khách mới (found=false)",
        expected: "HTTP 200 OK · 0901000001 -> found=true, 0999888777 -> found=false",
        run: async () => {
          const rFound = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/pos/member-lookup",
            params: { phone: "0901000001" },
          });
          const rMiss = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/pos/member-lookup",
            params: { phone: "0999888777" },
          });
          return {
            pass:
              rFound.status === 200 &&
              rFound.data?.found === true &&
              rMiss.status === 200 &&
              rMiss.data?.found === false,
            status: 200,
            latencyMs: Math.round((rFound.latencyMs + rMiss.latencyMs) * 10) / 10,
            actual: `0901000001: ${rFound.data?.full_name} | 0999888777: found=${rMiss.data?.found}`,
            payload: { found: rFound.data, not_found: rMiss.data },
          };
        },
      },
      {
        id: "TC-POS-02",
        module: "09. POS & Invoices",
        name: "Thu ngân POS 1-Transaction ACID: Áp mã WELCOME20 (-20%) & Tạo hóa đơn INV-XXXXXX",
        expected: "HTTP 201 Created · final_amount=399200 · Xuất hiện trong GET /pos/invoices",
        run: async (ctx) => {
          const targetPhone = ctx.tempMember?.phone || "0901000002";
          const co = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/pos/checkout",
            data: {
              phone: targetPhone,
              full_name: "Khách POS TestLab",
              plan_id: 1,
              discount_code: "WELCOME20",
              payment_method: "CASH",
            },
          });
          const invList = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: "/pos/invoices",
            params: { keyword: targetPhone, page: 1, size: 5 },
          });
          return {
            pass:
              co.status === 201 &&
              Number(co.data?.billing?.final_amount) === 399200 &&
              invList.status === 200 &&
              invList.data?.total >= 1,
            status: co.status,
            latencyMs: Math.round((co.latencyMs + invList.latencyMs) * 10) / 10,
            actual: `${co.data?.invoice_code} · Thực thu ${co.data?.billing?.final_amount}đ (${co.data?.subscription?.subscription_type})`,
            payload: co.data,
          };
        },
      },
      {
        id: "TC-DISC-01",
        module: "10. Discounts / Vouchers",
        name: "Validate Voucher: Hợp lệ (WELCOME20) vs Hết hạn (EXPIRED10) vs Chưa đủ đơn tối thiểu (DUCKYVIP)",
        expected: "WELCOME20 -> 200 OK | EXPIRED10 -> 422 | DUCKYVIP (499k < 2M) -> 422",
        run: async () => {
          const rOk = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/discounts/validate",
            data: { code: "WELCOME20", order_amount: 499000 },
          });
          const rExp = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/discounts/validate",
            data: { code: "EXPIRED10", order_amount: 499000 },
          });
          const rMin = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/discounts/validate",
            data: { code: "DUCKYVIP", order_amount: 499000 },
          });
          return {
            pass: rOk.status === 200 && rExp.status === 422 && rMin.status === 422,
            status: rOk.status,
            latencyMs: Math.round((rOk.latencyMs + rExp.latencyMs + rMin.latencyMs) * 10) / 10,
            actual: `WELCOME20->${rOk.status} (-${rOk.data?.discount_amount}đ), EXPIRED10->${rExp.status}, DUCKYVIP->${rMin.status}`,
            payload: { valid: rOk.data, expired: rExp.data, min_order: rMin.data },
          };
        },
      },
      {
        id: "TC-DISC-02",
        module: "10. Discounts / Vouchers",
        name: "Admin CRUD Voucher & Chặn cập nhật mức giảm PERCENT > 100% (BUG-05 Regression)",
        expected: "POST 201 -> PUT >100% bị chặn 422 -> DELETE 200",
        run: async () => {
          const vCode = `LAB${String(Date.now()).slice(-6)}`;
          const c = await rawRequest({
            role: "ADMIN",
            method: "POST",
            path: "/discounts",
            data: {
              code: vCode,
              description: "Voucher kiểm thử tự động",
              discount_type: "PERCENT",
              discount_value: 15,
              min_order_amount: 100000,
              expiry_date: formatLocalISO(30),
              usage_limit: 20,
            },
          });
          if (c.status !== 201) {
            return {
              pass: false,
              status: c.status,
              latencyMs: c.latencyMs,
              actual: `Lỗi tạo voucher: ${c.data?.message}`,
              payload: c.data,
            };
          }
          const did = c.data.discount_id;
          const badUpdate = await rawRequest({
            role: "ADMIN",
            method: "PUT",
            path: `/discounts/${did}`,
            data: { discount_value: 150 },
          });
          const del = await rawRequest({
            role: "ADMIN",
            method: "DELETE",
            path: `/discounts/${did}`,
          });
          return {
            pass: badUpdate.status === 422 && del.status === 200,
            status: del.status,
            latencyMs: Math.round((c.latencyMs + badUpdate.latencyMs + del.latencyMs) * 10) / 10,
            actual: `Created(${vCode}) -> Update 150% blocked(${badUpdate.status}) -> Deleted(${del.status})`,
            payload: { created: c.data, blocked_150pct: badUpdate.data, deleted: del.data },
          };
        },
      },
      {
        id: "TC-DASH-01",
        module: "11. Dashboard & Group Classes",
        name: "Dashboard KPI từ 4 SQL Views & Xuất báo cáo doanh thu CSV chuẩn UTF-8",
        expected: "GET /dashboard/summary 200 OK & GET /dashboard/export-csv 200 OK (text/csv)",
        run: async () => {
          const s = await rawRequest({
            role: "ADMIN",
            method: "GET",
            path: "/dashboard/summary",
          });
          const csvRes = await rawRequest({
            role: "ADMIN",
            method: "GET",
            path: "/dashboard/export-csv",
          });
          const hasCsvText =
            typeof csvRes.data === "string" &&
            csvRes.data.includes("BÁO CÁO DOANH THU");
          return {
            pass:
              s.status === 200 &&
              Boolean(s.data?.kpis) &&
              csvRes.status === 200 &&
              hasCsvText,
            status: 200,
            latencyMs: Math.round((s.latencyMs + csvRes.latencyMs) * 10) / 10,
            actual: `Tổng HV: ${s.data?.kpis?.total_members} · Gói ACTIVE: ${s.data?.kpis?.active_subscriptions} · CSV OK`,
            payload: s.data?.kpis,
          };
        },
      },
      {
        id: "TC-CLASS-01",
        module: "11. Dashboard & Group Classes",
        name: "Lớp tập nhóm: Tạo lớp -> Hội viên đăng ký -> Chặn đăng ký trùng (409) -> Điểm danh ATTENDED -> Hủy đăng ký",
        expected: "Create 201 -> Enroll 200 -> Dup 409 -> Attendance 200 -> Cancel 200",
        run: async () => {
          const createRes = await rawRequest({
            role: "STAFF",
            method: "POST",
            path: "/group-classes",
            data: {
              class_name: `Yoga TestLab ${String(Date.now()).slice(-4)}`,
              category: "YOGA",
              room: "Studio Test",
              schedule_date: formatLocalISO(5),
              start_time: "08:00",
              end_time: "09:00",
              max_capacity: 10,
            },
          });
          if (createRes.status !== 201) {
            return {
              pass: false,
              status: createRes.status,
              latencyMs: createRes.latencyMs,
              actual: `Không tạo được lớp: ${createRes.data?.message}`,
              payload: createRes.data,
            };
          }
          const cid = createRes.data.class_id;
          const enr = await rawRequest({
            role: "MEMBER",
            method: "POST",
            path: `/group-classes/${cid}/enroll`,
          });
          const dupEnr = await rawRequest({
            role: "MEMBER",
            method: "POST",
            path: `/group-classes/${cid}/enroll`,
          });
          const listEnr = await rawRequest({
            role: "STAFF",
            method: "GET",
            path: `/group-classes/${cid}/enrollments`,
          });
          const enrollmentId = listEnr.data?.students?.[0]?.enrollment_id;
          const att = await rawRequest({
            role: "STAFF",
            method: "PUT",
            path: `/group-classes/${cid}/attendance/${enrollmentId}`,
            data: { status: "ATTENDED" },
          });
          const cancel = await rawRequest({
            role: "MEMBER",
            method: "DELETE",
            path: `/group-classes/${cid}/enroll`,
          });
          return {
            pass:
              enr.status === 200 &&
              dupEnr.status === 409 &&
              att.status === 200 &&
              att.data?.status === "ATTENDED" &&
              cancel.status === 200,
            status: 200,
            latencyMs: Math.round(
              (createRes.latencyMs +
                enr.latencyMs +
                dupEnr.latencyMs +
                att.latencyMs +
                cancel.latencyMs) *
                10
            ) / 10,
            actual: `Class #${cid}: Enrolled -> DupBlocked(409) -> Marked(${att.data?.status}) -> Cancelled`,
            payload: { enrolled: enr.data, attendance: att.data, cancelled: cancel.data },
          };
        },
      },
    ],
    [rawRequest]
  );

  const runAllTests = async () => {
    setSuiteRunning(true);
    const sharedContext = {};
    const initialMap = {};
    testCases.forEach((tc) => {
      initialMap[tc.id] = { state: "PENDING" };
    });
    setTestResults(initialMap);

    for (const tc of testCases) {
      setTestResults((prev) => ({
        ...prev,
        [tc.id]: { state: "RUNNING" },
      }));
      try {
        const outcome = await tc.run(sharedContext);
        setTestResults((prev) => ({
          ...prev,
          [tc.id]: {
            state: outcome.pass ? "PASS" : "FAIL",
            ...outcome,
          },
        }));
      } catch (err) {
        setTestResults((prev) => ({
          ...prev,
          [tc.id]: {
            state: "FAIL",
            pass: false,
            status: 0,
            latencyMs: 0,
            actual: err.message || "Unhandled exception",
            payload: null,
          },
        }));
      }
    }
    setSuiteRunning(false);
    checkBackendHealth();
  };

  const runSingleTest = async (tc) => {
    setTestResults((prev) => ({
      ...prev,
      [tc.id]: { state: "RUNNING" },
    }));
    const outcome = await tc.run({});
    setTestResults((prev) => ({
      ...prev,
      [tc.id]: {
        state: outcome.pass ? "PASS" : "FAIL",
        ...outcome,
      },
    }));
  };

  const exportTestResultsCsv = () => {
    const header = [
      "Mã TC",
      "Phân hệ",
      "Tên Test Case",
      "Kết quả mong đợi",
      "Kết quả thực tế",
      "Độ trễ (ms)",
      "Trạng thái",
    ];
    const rows = testCases.map((tc) => {
      const r = testResults[tc.id] || {};
      return [
        tc.id,
        tc.module,
        tc.name,
        tc.expected,
        r.actual || "Chưa chạy",
        r.latencyMs ?? "",
        r.state || "PENDING",
      ];
    });
    const csvContent =
      "\ufeff" +
      [header, ...rows]
        .map((row) =>
          row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")
        )
        .join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DuckyGym_LiveTestLab_Report_${formatLocalISO(0)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const modulesList = useMemo(
    () => ["ALL", ...Array.from(new Set(testCases.map((t) => t.module)))],
    [testCases]
  );

  const filteredTestCases = useMemo(
    () =>
      testCases.filter((tc) => {
        if (moduleFilter !== "ALL" && tc.module !== moduleFilter) return false;
        const st = testResults[tc.id]?.state || "PENDING";
        if (statusFilter !== "ALL" && st !== statusFilter) return false;
        return true;
      }),
    [testCases, moduleFilter, statusFilter, testResults]
  );

  const summaryStats = useMemo(() => {
    const vals = Object.values(testResults);
    const passed = vals.filter((v) => v.state === "PASS").length;
    const failed = vals.filter((v) => v.state === "FAIL").length;
    const done = passed + failed;
    const avgMs =
      done > 0
        ? Math.round(
            vals
              .filter((v) => typeof v.latencyMs === "number")
              .reduce((acc, v) => acc + v.latencyMs, 0) / done
          )
        : 0;
    return {
      total: testCases.length,
      passed,
      failed,
      done,
      passRate: done > 0 ? Math.round((passed / done) * 100) : 0,
      avgMs,
    };
  }, [testResults, testCases.length]);

  const generatedSnippet = useMemo(() => {
    const cleanPath = reqPath.startsWith("/") ? reqPath : `/${reqPath}`;
    return `// Axios Request (${reqRole})
const res = await axiosClient.${reqMethod.toLowerCase()}("${cleanPath}"${
      reqMethod !== "GET" && reqBodyText.trim() ? `, ${reqBodyText.trim()}` : ""
    }${
      reqParamsText.trim() && reqParamsText.trim() !== "{}"
        ? `, { params: ${reqParamsText.trim()} }`
        : ""
    });
console.log(res.status, res.data);`;
  }, [reqRole, reqMethod, reqPath, reqBodyText, reqParamsText]);

  // Phòng vệ kép (Defense-in-Depth): ngoài ProtectedRoute allowedRoles=["ADMIN"], chặn cứng tại component nếu không phải ADMIN
  if (!user || user.role?.toUpperCase() !== "ADMIN") {
    return <Navigate to="/unauthorized" replace />;
  }

  return (
    <div className="lab-shell">
      <style>{labStyles}</style>

      <header className="lab-topbar">
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div className="lab-brand">
            <div className="lab-brand-icon">QA</div>
            <div>
              <b style={{ display: "block", fontSize: "15px" }}>
                INTERNAL QA &amp; CODE SANDBOX · /pages/test-lab
              </b>
              <small style={{ color: "#7dd3fc", fontSize: "11.5px" }}>
                Môi trường Chạy thử Code &amp; Kiểm thử Độc lập — Chỉ hiển thị và cấp quyền duy nhất cho ADMIN
              </small>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span
            data-testid="admin-exclusive-badge"
            style={{
              padding: "6px 12px",
              borderRadius: "8px",
              fontSize: "11.5px",
              fontWeight: 700,
              background: "rgba(14, 165, 233, 0.16)",
              color: "#7dd3fc",
              border: "1px solid rgba(56, 189, 248, 0.35)",
            }}
          >
            🔒 ADMIN EXCLUSIVE ({user.email})
          </span>

          <span
            data-testid="backend-health-badge"
            style={{
              padding: "6px 12px",
              borderRadius: "999px",
              fontSize: "12px",
              fontWeight: 700,
              background:
                healthState.ok === null
                  ? "rgba(148,163,184,0.16)"
                  : healthState.ok
                  ? "rgba(34,197,94,0.18)"
                  : "rgba(239,68,68,0.2)",
              color:
                healthState.ok === null
                  ? "#cbd5e1"
                  : healthState.ok
                  ? "#86efac"
                  : "#fca5a5",
              border: "1px solid rgba(255,255,255,0.12)",
            }}
          >
            {healthState.ok ? "● Backend Online" : healthState.ok === false ? "✕ Backend Offline" : "● Checking..."}{" "}
            · {healthState.db}
            {healthState.latencyMs !== null ? ` (${healthState.latencyMs}ms)` : ""}
          </span>

          <a
            href={`${API_BASE}/docs`}
            target="_blank"
            rel="noreferrer"
            className="lab-btn lab-btn-secondary"
            style={{ textDecoration: "none" }}
          >
            Swagger API Docs ↗
          </a>
          <Link
            to="/admin"
            data-testid="back-to-admin-btn"
            className="lab-btn lab-btn-primary"
            style={{ textDecoration: "none" }}
          >
            ← Quay về Trang Admin
          </Link>
        </div>
      </header>

      <div className="lab-container">
        {/* Bộ chọn Virtual Actor cô lập trong bộ nhớ (không làm mất phiên ADMIN của trình duyệt) */}
        <section className="lab-card">
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "12px",
              marginBottom: "12px",
            }}
          >
            <div>
              <b style={{ fontSize: "14px" }}>
                🎭 Bộ Giả Lập Token Vai Trò Trong Bộ Nhớ Cô Lập (Virtual Sandbox Actor)
              </b>
              <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "3px" }}>
                Người truy cập màn hình:{" "}
                <b style={{ color: "#7dd3fc" }}>
                  {user.role} — {user.full_name} ({user.email})
                </b>{" "}
                · Token giả lập khi bắn API Playground:{" "}
                <b style={{ color: "#4ade80" }}>{reqRole}</b>
              </div>
            </div>
            {roleSwitchNotice && (
              <span
                style={{
                  fontSize: "12px",
                  padding: "5px 12px",
                  borderRadius: "8px",
                  background: "rgba(14,165,233,0.16)",
                  color: "#7dd3fc",
                  border: "1px solid rgba(56,189,248,0.35)",
                }}
              >
                {roleSwitchNotice}
              </span>
            )}
          </div>

          <div className="lab-role-bar">
            {ROLE_PRESETS.map((rp) => {
              const isSelectedActor = reqRole === rp.key;
              return (
                <button
                  key={rp.key}
                  type="button"
                  data-testid={`virtual-actor-${rp.key}`}
                  className={`lab-role-chip ${isSelectedActor ? "is-active" : ""}`}
                  onClick={() => handleSelectVirtualActor(rp)}
                >
                  Giả lập API: {rp.label}
                </button>
              );
            })}
          </div>
        </section>

        {/* Thanh chuyển Tab */}
        <div className="lab-tabs">
          <button
            type="button"
            data-testid="tab-runner"
            className={`lab-tab-btn ${activeTab === "runner" ? "is-active" : ""}`}
            onClick={() => setActiveTab("runner")}
          >
            ⚡ Bộ Kiểm Thử Tự Động Toàn Hệ Thống ({testCases.length} E2E Cases)
          </button>
          <button
            type="button"
            data-testid="tab-playground"
            className={`lab-tab-btn ${activeTab === "playground" ? "is-active" : ""}`}
            onClick={() => setActiveTab("playground")}
          >
            🛠️ Chạy Thử Code &amp; API Tương Tác ({PLAYGROUND_PRESETS.length} Kịch bản)
          </button>
          <button
            type="button"
            data-testid="tab-rbac"
            className={`lab-tab-btn ${activeTab === "screens" ? "is-active" : ""}`}
            onClick={() => setActiveTab("screens")}
          >
            🔒 Chính Sách Cô Lập &amp; Phân Quyền Truy Cập
          </button>
        </div>

        {/* TAB 1: LIVE AUTOMATED E2E TEST SUITE */}
        {activeTab === "runner" && (
          <section className="lab-card" style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
              }}
            >
              <div>
                <h2 style={{ margin: 0, fontSize: "18px" }}>
                  Trình Chạy Kiểm Thử Tự Động Trực Tiếp (11 Phân Hệ · End-to-End Live Runner)
                </h2>
                <p style={{ margin: "4px 0 0", fontSize: "12.5px", color: "#94a3b8" }}>
                  Thực thi trực tiếp các request thật lên FastAPI + MySQL 8.0, tự động kiểm chứng HTTP Status, Ràng buộc nghiệp vụ (BR03, BR06, BR12), Phân quyền RBAC, Hiệu năng (&lt; 1000ms) và tự động dọn dẹp dữ liệu tạm.
                </p>
              </div>

              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  data-testid="btn-run-all-tests"
                  className="lab-btn lab-btn-primary"
                  disabled={suiteRunning}
                  onClick={runAllTests}
                >
                  {suiteRunning
                    ? `⏳ Đang chạy (${summaryStats.done}/${summaryStats.total})...`
                    : `▶ Chạy Toàn Bộ ${testCases.length} Test Cases`}
                </button>
                <button
                  type="button"
                  data-testid="btn-export-test-csv"
                  className="lab-btn lab-btn-success"
                  onClick={exportTestResultsCsv}
                >
                  📥 Xuất Kết Quả CSV
                </button>
              </div>
            </div>

            <div className="lab-kpis">
              <div className="lab-kpi">
                <small>TỔNG SỐ TEST CASE E2E</small>
                <b data-testid="stat-total">{summaryStats.total}</b>
              </div>
              <div className="lab-kpi">
                <small>ĐẠT (PASS)</small>
                <b data-testid="stat-passed" style={{ color: "#4ade80" }}>
                  {summaryStats.passed}
                </b>
              </div>
              <div className="lab-kpi">
                <small>LỖI (FAIL)</small>
                <b data-testid="stat-failed" style={{ color: summaryStats.failed > 0 ? "#f87171" : "#94a3b8" }}>
                  {summaryStats.failed}
                </b>
              </div>
              <div className="lab-kpi">
                <small>TỶ LỆ PASS</small>
                <b data-testid="stat-pass-rate" style={{ color: "#ffb690" }}>
                  {summaryStats.passRate}%
                </b>
              </div>
              <div className="lab-kpi">
                <small>ĐỘ TRỄ TRUNG BÌNH</small>
                <b>{summaryStats.avgMs} ms</b>
              </div>
            </div>

            {/* Thanh tiến trình */}
            <div
              style={{
                height: "8px",
                borderRadius: "999px",
                background: "#0f172a",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${Math.round((summaryStats.done / summaryStats.total) * 100)}%`,
                  background: summaryStats.failed > 0 ? "#ef4444" : "#22c55e",
                  transition: "width 0.2s ease",
                }}
              />
            </div>

            {/* Bộ lọc */}
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <select
                className="lab-select"
                style={{ width: "260px" }}
                value={moduleFilter}
                onChange={(e) => setModuleFilter(e.target.value)}
              >
                {modulesList.map((m) => (
                  <option key={m} value={m}>
                    {m === "ALL" ? "Tất cả 11 phân hệ" : m}
                  </option>
                ))}
              </select>

              <select
                className="lab-select"
                style={{ width: "180px" }}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">Mọi trạng thái</option>
                <option value="PASS">Chỉ PASS</option>
                <option value="FAIL">Chỉ FAIL</option>
                <option value="PENDING">Chưa chạy</option>
              </select>
            </div>

            {/* Bảng kết quả chi tiết */}
            <div style={{ overflowX: "auto" }}>
              <table className="lab-table">
                <thead>
                  <tr>
                    <th style={{ width: "105px" }}>Mã TC</th>
                    <th style={{ width: "185px" }}>Phân hệ</th>
                    <th>Kịch bản kiểm thử &amp; Kỳ vọng</th>
                    <th>Kết quả thực tế (Actual)</th>
                    <th style={{ width: "85px" }}>Độ trễ</th>
                    <th style={{ width: "95px" }}>Trạng thái</th>
                    <th style={{ width: "100px" }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTestCases.map((tc) => {
                    const res = testResults[tc.id] || { state: "PENDING" };
                    const isExpanded = expandedTcId === tc.id;
                    const badgeClass =
                      res.state === "PASS"
                        ? "lab-badge-pass"
                        : res.state === "FAIL"
                        ? "lab-badge-fail"
                        : res.state === "RUNNING"
                        ? "lab-badge-running"
                        : "lab-badge-pending";
                    return (
                      <React.Fragment key={tc.id}>
                        <tr>
                          <td>
                            <b style={{ color: "#ffb690" }}>{tc.id}</b>
                          </td>
                          <td style={{ color: "#94a3b8", fontSize: "12px" }}>{tc.module}</td>
                          <td>
                            <div style={{ fontWeight: 600, marginBottom: "3px" }}>{tc.name}</div>
                            <div style={{ fontSize: "11.5px", color: "#94a3b8" }}>
                              Kỳ vọng: {tc.expected}
                            </div>
                          </td>
                          <td style={{ fontSize: "12px", color: "#cbd5e1" }}>
                            {res.actual || "—"}
                          </td>
                          <td>{res.latencyMs !== undefined ? `${res.latencyMs} ms` : "—"}</td>
                          <td>
                            <span className={`lab-badge ${badgeClass}`}>{res.state}</span>
                          </td>
                          <td>
                            <div style={{ display: "flex", gap: "6px" }}>
                              <button
                                type="button"
                                className="lab-btn lab-btn-secondary"
                                style={{ padding: "5px 9px", fontSize: "11px" }}
                                disabled={suiteRunning}
                                onClick={() => runSingleTest(tc)}
                              >
                                Chạy
                              </button>
                              {res.payload && (
                                <button
                                  type="button"
                                  className="lab-btn lab-btn-secondary"
                                  style={{ padding: "5px 8px", fontSize: "11px" }}
                                  onClick={() =>
                                    setExpandedTcId(isExpanded ? null : tc.id)
                                  }
                                >
                                  {isExpanded ? "Ẩn" : "JSON"}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                        {isExpanded && res.payload && (
                          <tr>
                            <td colSpan={7} style={{ background: "#0b1326" }}>
                              <pre className="lab-code">
                                {JSON.stringify(res.payload, null, 2)}
                              </pre>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* TAB 2: INTERACTIVE API & CODE PLAYGROUND */}
        {activeTab === "playground" && (
          <div className="lab-playground-grid">
            <aside className="lab-card">
              <h3 style={{ margin: "0 0 10px", fontSize: "15px" }}>
                📚 Thư Viện Kịch Bản Chạy Thử ({PLAYGROUND_PRESETS.length})
              </h3>
              <div className="lab-preset-list">
                {PLAYGROUND_PRESETS.map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    data-testid={`preset-${preset.id}`}
                    className={`lab-preset-item ${
                      selectedPresetId === preset.id ? "is-selected" : ""
                    }`}
                    onClick={() => selectPlaygroundPreset(preset)}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: "11px",
                        color: "#94a3b8",
                        marginBottom: "3px",
                      }}
                    >
                      <span>{preset.module}</span>
                      <b style={{ color: "#ffb690" }}>
                        {preset.method} · {preset.role}
                      </b>
                    </div>
                    <div style={{ fontSize: "12.5px", fontWeight: 600 }}>
                      {preset.title}
                    </div>
                  </button>
                ))}
              </div>
            </aside>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <form className="lab-card" onSubmit={handleExecutePlayground}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "14px",
                    flexWrap: "wrap",
                    gap: "10px",
                  }}
                >
                  <h3 style={{ margin: 0, fontSize: "16px" }}>
                    🚀 Bộ Soạn Thảo &amp; Thực Thi Request Trực Tiếp
                  </h3>
                  <button
                    type="submit"
                    data-testid="btn-execute-request"
                    className="lab-btn lab-btn-primary"
                    disabled={playLoading}
                  >
                    {playLoading ? "Đang gửi..." : "▶ Chạy Thử Request"}
                  </button>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "130px 1fr 220px",
                    gap: "10px",
                    marginBottom: "12px",
                  }}
                >
                  <select
                    className="lab-select"
                    value={reqMethod}
                    onChange={(e) => setReqMethod(e.target.value)}
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                  </select>

                  <input
                    className="lab-input"
                    data-testid="input-req-path"
                    value={reqPath}
                    onChange={(e) => setReqPath(e.target.value)}
                    placeholder="/endpoint-path"
                  />

                  <select
                    className="lab-select"
                    value={reqRole}
                    onChange={(e) => setReqRole(e.target.value)}
                  >
                    <option value="GUEST">Token: GUEST (Không gắn)</option>
                    <option value="CURRENT">Token: Phiên hiện tại</option>
                    <option value="ADMIN">Token: ADMIN</option>
                    <option value="STAFF">Token: STAFF (Lễ tân)</option>
                    <option value="MEMBER">Token: MEMBER (Hội viên)</option>
                    <option value="TRAINER">Token: TRAINER (PT)</option>
                  </select>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "12px",
                    marginBottom: "12px",
                  }}
                >
                  <div>
                    <label
                      style={{
                        display: "block",
                        fontSize: "12px",
                        color: "#94a3b8",
                        marginBottom: "5px",
                      }}
                    >
                      Query Params (JSON)
                    </label>
                    <textarea
                      className="lab-textarea"
                      rows={5}
                      value={reqParamsText}
                      onChange={(e) => setReqParamsText(e.target.value)}
                    />
                  </div>
                  <div>
                    <label
                      style={{
                        display: "block",
                        fontSize: "12px",
                        color: "#94a3b8",
                        marginBottom: "5px",
                      }}
                    >
                      Request Body Payload (JSON)
                    </label>
                    <textarea
                      className="lab-textarea"
                      rows={5}
                      value={reqBodyText}
                      onChange={(e) => setReqBodyText(e.target.value)}
                      placeholder={reqMethod === "GET" ? "// GET không dùng body" : "{}"}
                    />
                  </div>
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "12px",
                      color: "#94a3b8",
                      marginBottom: "5px",
                    }}
                  >
                    Đoạn Code Frontend Tương Ứng (Tự động sinh):
                  </label>
                  <pre className="lab-code" style={{ maxHeight: "120px" }}>
                    {generatedSnippet}
                  </pre>
                </div>
              </form>

              <section className="lab-card">
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "10px",
                  }}
                >
                  <h3 style={{ margin: 0, fontSize: "15px" }}>📡 Kết Quả Phản Hồi Thực Tế (Live Response)</h3>
                  {playResponse && (
                    <span
                      data-testid="playground-response-status"
                      className={`lab-badge ${
                        playResponse.status >= 200 && playResponse.status < 300
                          ? "lab-badge-pass"
                          : "lab-badge-fail"
                      }`}
                    >
                      HTTP {playResponse.status} · {playResponse.latencyMs} ms
                    </span>
                  )}
                </div>
                <pre className="lab-code" data-testid="playground-response-body">
                  {playResponse
                    ? typeof playResponse.data === "string"
                      ? playResponse.data.slice(0, 3000)
                      : JSON.stringify(playResponse.data, null, 2)
                    : "// Bấm '▶ Chạy Thử Request' để xem dữ liệu trả về trực tiếp từ Backend + MySQL..."}
                </pre>

                {playHistory.length > 0 && (
                  <div style={{ marginTop: "14px" }}>
                    <small style={{ color: "#94a3b8", fontWeight: 700 }}>
                      Nhật ký các lần gọi gần nhất:
                    </small>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "4px",
                        marginTop: "6px",
                        fontSize: "12px",
                      }}
                    >
                      {playHistory.map((h) => (
                        <div
                          key={h.id}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            padding: "6px 10px",
                            borderRadius: "6px",
                            background: "#131b2e",
                          }}
                        >
                          <span>
                            [{h.time}] <b>{h.method}</b> {h.path} ({h.role})
                          </span>
                          <span>
                            HTTP <b>{h.status}</b> · {h.latencyMs}ms
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            </div>
          </div>
        )}

        {/* TAB 3: ISOLATION & RBAC SECURITY MATRIX */}
        {activeTab === "screens" && (
          <section className="lab-card" style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            <div>
              <h2 style={{ margin: 0, fontSize: "18px" }}>
                🔒 Ma Trận Cô Lập Màn Hình `/pages/test-lab` &amp; Phân Quyền Hệ Thống
              </h2>
              <p style={{ margin: "4px 0 0", fontSize: "12.5px", color: "#94a3b8" }}>
                Màn hình Test Lab được tách biệt hoàn toàn khỏi giao diện người dùng chung. Khi gõ trực tiếp đường dẫn <code>/pages/test-lab</code> (hoặc <code>/admin/test-lab</code>, <code>/test-lab</code>) trên thanh địa chỉ: khách chưa đăng nhập bị đẩy về <code>/login</code>, các vai trò <code>MEMBER</code>, <code>STAFF</code>, <code>TRAINER</code> bị chặn <code>403 Forbidden (/unauthorized)</code>. Chỉ duy nhất <code>ADMIN</code> truy cập được và thấy lối vào trong trang <code>/admin</code>.
              </p>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table className="lab-table">
                <thead>
                  <tr>
                    <th>Đường dẫn URL</th>
                    <th>Phân hệ / Màn hình</th>
                    <th>GUEST (Chưa login)</th>
                    <th>MEMBER (Hội viên)</th>
                    <th>STAFF (Lễ tân)</th>
                    <th>TRAINER (PT)</th>
                    <th>ADMIN (Quản trị)</th>
                  </tr>
                </thead>
                <tbody>
                  {RBAC_ROUTE_POLICIES.map((row) => (
                    <tr key={row.route}>
                      <td>
                        <code style={{ color: "#7dd3fc", fontWeight: 700 }}>{row.route}</code>
                      </td>
                      <td>{row.component}</td>
                      <td style={{ color: "#fca5a5" }}>{row.guest}</td>
                      <td style={{ color: row.member.startsWith("✓") ? "#86efac" : "#fca5a5" }}>
                        {row.member}
                      </td>
                      <td style={{ color: row.staff.startsWith("✓") ? "#86efac" : "#fca5a5" }}>
                        {row.staff}
                      </td>
                      <td style={{ color: row.trainer.startsWith("✓") ? "#86efac" : "#fca5a5" }}>
                        {row.trainer}
                      </td>
                      <td style={{ color: "#86efac", fontWeight: 700 }}>{row.admin}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default SystemTestLabPage;
