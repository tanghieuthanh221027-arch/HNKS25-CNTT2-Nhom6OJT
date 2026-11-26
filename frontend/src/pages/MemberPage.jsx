import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import QRCodeDisplay, { downloadQRCodeImage } from "../components/QRCodeDisplay";
import { useAuth } from "../context/AuthContext";
import gymApi from "../api/gymApi";

const memberStyles = `
.member-page {
  --member-bg: #0b1326;
  --member-surface: #131b2e;
  --member-card: #171f33;
  --member-field: #222a3d;
  --member-text: #dae2fd;
  --member-muted: #a6adc2;
  --member-orange: #f97316;
  min-height: 100vh;
  background: var(--member-bg);
  color: var(--member-text);
  font-family: Inter, Arial, sans-serif;
}
.member-page * { box-sizing: border-box; }
.member-page a { color: inherit; text-decoration: none; }
.member-page button { color: inherit; font: inherit; cursor: pointer; }
.member-page .material-symbols-outlined { font-size: 20px; line-height: 1; }

.member-header { position: sticky; z-index: 20; top: 0; border-bottom: 1px solid rgba(255, 255, 255, 0.07); background: rgba(11, 19, 38, 0.92); backdrop-filter: blur(18px); }
.member-nav { display: flex; width: min(1440px, 100%); height: 74px; align-items: center; justify-content: space-between; gap: 20px; margin: 0 auto; padding: 0 clamp(18px, 4vw, 56px); }
.member-brand { display: inline-flex; align-items: center; gap: 10px; }
.member-brand-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 9px; background: var(--member-orange); color: #351400; }
.member-brand b { font-size: 15px; display: block; letter-spacing: .06em; }
.member-brand small { color: #ffb690; font-size: 9px; letter-spacing: .14em; }

.member-links { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.member-links a { padding: 8px 12px; border-radius: 7px; color: var(--member-muted); font-size: 13px; font-weight: 500; }
.member-links a:hover { background: var(--member-field); color: var(--member-text); }

.member-account { position: relative; }
.member-account-button { display: flex; align-items: center; gap: 10px; padding: 6px 12px 6px 6px; border-radius: 999px; background: var(--member-surface); border: 1px solid rgba(255, 255, 255, 0.08); }
.member-avatar { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; background: var(--member-orange); color: #351400; font-weight: 700; font-size: 13px; }
.member-account-name { display: flex; flex-direction: column; text-align: left; }
.member-account-name b { font-size: 13px; }
.member-account-name small { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: var(--member-muted); }
.member-account-name small i { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; display: inline-block; }
.member-menu { position: absolute; right: 0; top: calc(100% + 8px); width: 220px; background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 6px; box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45); display: flex; flex-direction: column; gap: 4px; }
.member-menu button { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 12px; border-radius: 8px; border: none; background: transparent; font-size: 13px; text-align: left; }
.member-menu button:hover { background: var(--member-field); }
.member-menu-logout { color: #f87171 !important; }

.member-main { padding: 32px 0 64px; }
.member-content { width: min(1440px, 100%); margin: 0 auto; padding: 0 clamp(18px, 4vw, 56px); display: flex; flex-direction: column; gap: 32px; }

.member-warning-banner { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 20px; border-radius: 12px; background: rgba(245, 158, 11, 0.16); border: 1px solid rgba(245, 158, 11, 0.45); color: #fde68a; font-size: 13px; }
.member-welcome { display: grid; grid-template-columns: 1fr 340px; gap: 24px; }
.member-welcome-card, .member-pass-card, .member-panel { background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 18px; padding: 26px; }
.member-badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px; background: rgba(249, 115, 22, 0.15); color: #ffb690; font-size: 11px; font-weight: 600; margin-bottom: 10px; }
.member-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }
.member-stats > div { background: var(--member-surface); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 5px; }
.member-stats > div > .material-symbols-outlined { color: var(--member-orange); }
.member-stats small { color: var(--member-muted); font-size: 11px; }
.member-stats b { font-size: 15px; }

.member-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.member-primary-button, .member-secondary-button { display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: 10px; font-size: 13px; font-weight: 600; border: none; }
.member-primary-button { background: var(--member-orange); color: #351400; }
.member-secondary-button { background: var(--member-field); color: var(--member-text); border: 1px solid rgba(255, 255, 255, 0.08); }

.member-pass-card { display: flex; flex-direction: column; align-items: center; justify-content: space-between; text-align: center; gap: 12px; }
.member-pass-heading { width: 100%; display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-weight: 600; color: var(--member-muted); }
.member-online { display: inline-flex; align-items: center; gap: 5px; color: #4ade80; }
.member-online i { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; }
.member-qr { position: relative; width: 188px; height: 188px; padding: 14px; background: #ffffff; border-radius: 16px; display: grid; place-items: center; }
.member-qr-logo { position: absolute; background: var(--member-orange); color: #351400; padding: 4px; border-radius: 8px; border: 3px solid #ffffff; display: grid; place-items: center; }

.member-badges-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.member-badge-card { display: flex; align-items: center; gap: 14px; padding: 16px; border-radius: 14px; background: var(--member-surface); border: 1px solid rgba(255,255,255,0.06); }
.member-badge-card.is-unlocked { border-color: rgba(249, 115, 22, 0.45); background: linear-gradient(135deg, rgba(249,115,22,0.14), rgba(19,27,46,0.95)); }
.member-badge-icon { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; background: var(--member-field); color: var(--member-muted); }
.member-badge-card.is-unlocked .member-badge-icon { background: var(--member-orange); color: #351400; }

.pt-calendar-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.pt-calendar-grid { width: 100%; border-collapse: collapse; font-size: 12px; }
.pt-calendar-grid th, .pt-calendar-grid td { border: 1px solid rgba(255,255,255,0.08); padding: 8px; text-align: center; }
.pt-calendar-grid th { background: var(--member-surface); color: var(--member-muted); font-weight: 600; }
.pt-slot-btn { width: 100%; padding: 6px 4px; border-radius: 6px; font-size: 11px; font-weight: 600; border: 1px solid transparent; }
.pt-slot-free { background: rgba(34, 197, 94, 0.12); color: #86efac; border-color: rgba(34, 197, 94, 0.25); }
.pt-slot-free:hover { background: rgba(34, 197, 94, 0.25); }
.pt-slot-mine { background: rgba(249, 115, 22, 0.22); color: #ffb690; border-color: #f97316; }
.pt-slot-busy { background: rgba(239, 68, 68, 0.14); color: #fca5a5; cursor: not-allowed; }

.group-class-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 16px; }
.group-class-card { background: var(--member-surface); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; gap: 12px; }

.history-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.history-table th, .history-table td { padding: 11px 12px; border-bottom: 1px solid rgba(255,255,255,0.07); text-align: left; }
.history-table th { color: var(--member-muted); font-size: 12px; }

@media (max-width: 960px) {
  .member-welcome { grid-template-columns: 1fr; }
  .member-stats, .member-badges-row { grid-template-columns: repeat(2, 1fr); }
}
`;

const DAY_NAMES = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"];
const HOURS = ["07:00", "08:00", "09:00", "10:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"];

const formatLocalDate = (d) => {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const getMondayStr = (baseDate = new Date()) => {
  const d = new Date(baseDate);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  return formatLocalDate(d);
};

const addDaysStr = (dateStr, days) => {
  const [y, m, day] = dateStr.split("-").map(Number);
  const d = new Date(y, m - 1, day + days);
  return formatLocalDate(d);
};

const MemberPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const [subInfo, setSubInfo] = useState(null);
  const [ptData, setPtData] = useState({ trainers: [], bookings: [] });
  const [selectedTrainerId, setSelectedTrainerId] = useState(null);
  const [weekStart, setWeekStart] = useState(getMondayStr);
  const [ptMessage, setPtMessage] = useState({ type: "", text: "" });

  const [groupClasses, setGroupClasses] = useState([]);
  const [classNotice, setClassNotice] = useState("");

  const [historyData, setHistoryData] = useState({
    items: [],
    total: 0,
    page: 1,
    pages: 0,
    active_in_gym_count: 0,
  });
  const [dateFilter, setDateFilter] = useState({ from_date: "", to_date: "" });

  const fullName = user?.full_name || user?.name || user?.username || "Hội viên";
  const initials = fullName
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  const memberCode =
    subInfo?.member_code ||
    user?.member_code ||
    (user?.user_id ? `DG-${String(user.user_id).padStart(6, "0")}` : "DG-000001");

  const loadSubscription = useCallback(() => {
    gymApi
      .getMySubscription()
      .then((res) => setSubInfo(res.data))
      .catch(() => {});
  }, []);

  const loadPTSchedules = useCallback(() => {
    gymApi
      .getPTSchedules({
        trainer_id: selectedTrainerId || undefined,
        week_start: weekStart,
      })
      .then((res) => {
        const data = res.data || { trainers: [], bookings: [] };
        setPtData(data);
        if (!selectedTrainerId && data.trainers?.length > 0) {
          setSelectedTrainerId(data.trainers[0].user_id);
        }
      })
      .catch(() => {});
  }, [selectedTrainerId, weekStart]);

  const loadGroupClasses = useCallback(() => {
    gymApi
      .getGroupClasses()
      .then((res) => setGroupClasses(res.data || []))
      .catch(() => {});
  }, []);

  const loadCheckInHistory = useCallback(
    (page = 1) => {
      gymApi
        .getCheckInHistory({
          page,
          size: 8,
          from_date: dateFilter.from_date || undefined,
          to_date: dateFilter.to_date || undefined,
        })
        .then((res) => setHistoryData(res.data))
        .catch(() => {});
    },
    [dateFilter.from_date, dateFilter.to_date]
  );

  useEffect(() => {
    loadSubscription();
    loadGroupClasses();
    loadCheckInHistory(1);
  }, [loadSubscription, loadGroupClasses, loadCheckInHistory]);

  useEffect(() => {
    loadPTSchedules();
  }, [loadPTSchedules]);

  useEffect(() => {
    const closeMenu = (event) => {
      if (!menuRef.current?.contains(event.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", closeMenu);
    return () => document.removeEventListener("mousedown", closeMenu);
  }, []);

  const handleBookPTSlot = async (dateStr, hourStr) => {
    if (!selectedTrainerId) return;
    setPtMessage({ type: "", text: "" });
    try {
      const res = await gymApi.createPTBooking({
        trainer_id: selectedTrainerId,
        booking_date: dateStr,
        start_time: hourStr,
      });
      setPtMessage({ type: "success", text: res.data.message });
      loadPTSchedules();
    } catch (err) {
      setPtMessage({
        type: "error",
        text:
          err.response?.data?.message ||
          err.response?.data?.detail ||
          "Không thể đặt lịch do trùng khung giờ.",
      });
    }
  };

  const handleCancelPTBooking = async (bookingId) => {
    setPtMessage({ type: "", text: "" });
    try {
      await gymApi.cancelPTBooking(bookingId, "Hội viên chủ động hủy trước giờ tập");
      setPtMessage({ type: "success", text: "Đã hủy lịch tập PT thành công." });
      loadPTSchedules();
      loadSubscription();
    } catch (err) {
      setPtMessage({
        type: "error",
        text: err.response?.data?.message || "Không thể hủy lịch tập.",
      });
    }
  };

  const handleToggleClassEnroll = async (cls) => {
    setClassNotice("");
    try {
      if (cls.is_enrolled) {
        const res = await gymApi.cancelGroupClass(cls.class_id);
        setClassNotice(res.data.message);
      } else {
        const res = await gymApi.enrollGroupClass(cls.class_id);
        setClassNotice(res.data.message);
      }
      loadGroupClasses();
    } catch (err) {
      setClassNotice(
        err.response?.data?.message || "Thao tác đăng ký lớp thất bại."
      );
    }
  };

  const weekDays = Array.from({ length: 7 }, (_, i) => addDaysStr(weekStart, i));
  const badges = subInfo?.badges ||
    user?.badges || [
      {
        threshold: 10,
        title: "Tân Binh Kỷ Luật",
        icon: "military_tech",
        description: "Hoàn thành 10 buổi tập",
        unlocked: (subInfo?.total_checkins || 0) >= 10,
      },
      {
        threshold: 30,
        title: "Chiến Binh Bền Bỉ",
        icon: "workspace_premium",
        description: "Hoàn thành 30 buổi tập",
        unlocked: (subInfo?.total_checkins || 0) >= 30,
      },
      {
        threshold: 100,
        title: "Huyền Thoại Ducky Gym",
        icon: "emoji_events",
        description: "Hoàn thành 100 buổi tập",
        unlocked: (subInfo?.total_checkins || 0) >= 100,
      },
    ];

  return (
    <div className="member-page">
      <style>{memberStyles}</style>
      <header className="member-header">
        <div className="member-nav">
          <Link className="member-brand" to="/member">
            <span className="member-brand-icon material-symbols-outlined">
              fitness_center
            </span>
            <span>
              <b>DUCKY GYM</b>
              <small>MEMBER PORTAL</small>
            </span>
          </Link>

          <nav className="member-links" aria-label="Điều hướng hội viên">
            <a href="#overview">Thẻ QR</a>
            <a href="#pt-booking">Đặt lịch PT 1-1</a>
            <a href="#group-classes">Lớp tập nhóm</a>
            <a href="#checkin-history">Lịch sử Check-in</a>
            <Link to="/member/profile">Hồ sơ &amp; BMI</Link>
          </nav>

          <div className="member-account" ref={menuRef}>
            <button
              className="member-account-button"
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span className="member-avatar">{initials || "HV"}</span>
              <span className="member-account-name">
                <b>{fullName}</b>
                <small>
                  <i /> Đang tập tại phòng: {historyData.active_in_gym_count} người
                </small>
              </span>
              <span className="material-symbols-outlined">
                {menuOpen ? "expand_less" : "expand_more"}
              </span>
            </button>
            {menuOpen && (
              <div className="member-menu" role="menu">
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    navigate("/member/profile");
                  }}
                >
                  <span className="material-symbols-outlined">
                    account_circle
                  </span>
                  Hồ sơ &amp; Theo dõi BMI
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    navigate("/membership");
                  }}
                >
                  <span className="material-symbols-outlined">
                    card_membership
                  </span>
                  Đăng ký / Gia hạn gói tập
                </button>
                <button
                  type="button"
                  className="member-menu-logout"
                  onClick={() => {
                    logout();
                    navigate("/login", { replace: true });
                  }}
                >
                  <span className="material-symbols-outlined">logout</span>
                  Đăng xuất
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="member-main">
        <div className="member-content">
          {/* Cảnh báo thẻ sắp hết hạn hoặc đã hết hạn (Task T067F69) */}
          {subInfo?.warning_message && (
            <div className="member-warning-banner" role="alert">
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span className="material-symbols-outlined">warning</span>
                <span>{subInfo.warning_message}</span>
              </div>
              <Link className="member-primary-button" to="/membership">
                Gia hạn ngay
              </Link>
            </div>
          )}

          {/* Khu vực Thẻ Hội viên Điện tử QR & Tổng quan (Task T067F69 & T3CD518) */}
          <section className="member-welcome" id="overview">
            <div className="member-welcome-card">
              <div>
                <span className="member-badge">
                  <span className="material-symbols-outlined">stars</span> HỘI
                  VIÊN DUCKY GYM · STREAK {subInfo?.streak_days ?? user?.streak_days ?? 5} NGÀY 🔥
                </span>
                <h1 style={{ margin: "6px 0 8px", fontSize: "28px" }}>
                  Xin chào, {fullName}!
                </h1>
                <p style={{ margin: 0, color: "var(--member-muted)", fontSize: "14px" }}>
                  Quản lý thẻ hội viên QR, đặt lịch PT 1-1 theo tuần, đăng ký lớp
                  tập nhóm và theo dõi chỉ số BMI của bạn.
                </p>
              </div>

              <div className="member-stats">
                <div>
                  <span className="material-symbols-outlined">badge</span>
                  <small>MÃ THẺ QR</small>
                  <b>{memberCode}</b>
                </div>
                <div>
                  <span className="material-symbols-outlined">
                    card_membership
                  </span>
                  <small>GÓI TẬP HIỆN TẠI</small>
                  <b>{subInfo?.plan_name || "Pro Fitness"}</b>
                </div>
                <div>
                  <span className="material-symbols-outlined">
                    event_upcoming
                  </span>
                  <small>HẠN THẺ</small>
                  <b>
                    {subInfo?.end_date
                      ? `${subInfo.end_date} (${subInfo.days_remaining} ngày)`
                      : "Đang hoạt động"}
                  </b>
                </div>
                <div>
                  <span className="material-symbols-outlined">
                    local_fire_department
                  </span>
                  <small>CHUỖI NGÀY TẬP &amp; TỔNG BUỔI</small>
                  <b>
                    {subInfo?.streak_days ?? 5} ngày ·{" "}
                    {subInfo?.total_checkins ?? 32} buổi
                  </b>
                </div>
              </div>

              <div className="member-actions">
                <a className="member-primary-button" href="#member-pass">
                  <span className="material-symbols-outlined">
                    qr_code_2
                  </span>
                  Đưa mã QR cho Lễ tân quét
                </a>
                <Link className="member-secondary-button" to="/membership">
                  <span className="material-symbols-outlined">autorenew</span>
                  Đăng ký / Gia hạn gói tập
                </Link>
                <Link className="member-secondary-button" to="/member/profile">
                  <span className="material-symbols-outlined">monitoring</span>
                  Cập nhật Chiều cao, Cân nặng &amp; BMI
                </Link>
              </div>
            </div>

            <aside className="member-pass-card" id="member-pass">
              <div className="member-pass-heading">
                <span>THẺ HỘI VIÊN ĐIỆN TỬ</span>
                <span className="member-online">
                  <i />{" "}
                  {subInfo?.card_status === "EXPIRED" ? "HẾT HẠN" : "ĐANG HOẠT ĐỘNG"}
                </span>
              </div>
              <div
                id="member-qr-box"
                className="member-qr"
                aria-label={`Mã QR check-in của ${memberCode}`}
              >
                <QRCodeDisplay
                  value={memberCode}
                  size={160}
                  bgColor="#ffffff"
                  fgColor="#0b1326"
                  level="H"
                />
                <span className="member-qr-logo material-symbols-outlined">
                  fitness_center
                </span>
              </div>
              <div style={{ fontSize: "12px", color: "var(--member-muted)" }}>
                Hạn thẻ: <b>{subInfo?.end_date || "2026-12-31"}</b>
              </div>
              <b style={{ color: "#ffb690", letterSpacing: ".08em" }}>
                {memberCode}
              </b>
              <button
                type="button"
                className="member-secondary-button"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() =>
                  downloadQRCodeImage(
                    "member-qr-box",
                    memberCode,
                    subInfo?.qr_base64
                  )
                }
              >
                <span className="material-symbols-outlined">download</span>
                Tải ảnh QR về máy
              </button>
            </aside>
          </section>

          {/* Huy hiệu Chuỗi ngày tập (Bonus T3CD518) */}
          <section className="member-panel">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "14px",
              }}
            >
              <div>
                <h2 style={{ margin: 0, fontSize: "17px" }}>
                  HUY HIỆU THÀNH TÍCH &amp; CHUỖI NGÀY TẬP
                </h2>
                <p
                  style={{
                    margin: "4px 0 0",
                    fontSize: "13px",
                    color: "var(--member-muted)",
                  }}
                >
                  Duy trì check-in đều đặn để mở khóa các mốc 10, 30 và 100 buổi
                  tập
                </p>
              </div>
              <span className="member-badge">
                Tổng tích lũy: {subInfo?.total_checkins ?? 32} buổi
              </span>
            </div>
            <div className="member-badges-row">
              {badges.map((b) => (
                <div
                  key={b.threshold}
                  className={`member-badge-card${
                    b.unlocked ? " is-unlocked" : ""
                  }`}
                >
                  <div className="member-badge-icon">
                    <span className="material-symbols-outlined">{b.icon}</span>
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: "14px" }}>
                      {b.title} ({b.threshold} buổi)
                    </div>
                    <div
                      style={{
                        fontSize: "12px",
                        color: "var(--member-muted)",
                        marginTop: "3px",
                      }}
                    >
                      {b.unlocked ? "✓ Đã đạt huy hiệu" : b.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Lịch tuần Đặt lịch PT 1-1 (Task T067EF6 & T067DB0) */}
          <section className="member-panel" id="pt-booking">
            <div className="pt-calendar-toolbar">
              <div>
                <h2 style={{ margin: 0, fontSize: "17px" }}>
                  ĐẶT LỊCH TẬP PT 1-1 THEO TUẦN
                </h2>
                <p
                  style={{
                    margin: "4px 0 0",
                    fontSize: "13px",
                    color: "var(--member-muted)",
                  }}
                >
                  Chọn Huấn luyện viên và bấm vào ô trống màu xanh thuộc ca trực của PT để đặt lịch (Đặt trước &gt; 30 phút, hủy miễn phí trước &ge; 2 tiếng · Số buổi PT còn lại:{" "}
                  <b style={{ color: "#ffb690" }}>
                    {ptData.pt_quota?.sessions_remaining ?? subInfo?.sessions_remaining ?? 0}/
                    {ptData.pt_quota?.total_sessions ?? subInfo?.total_sessions ?? 0} buổi
                  </b>
                  )
                </p>
              </div>

              <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
                <select
                  value={selectedTrainerId || ""}
                  onChange={(e) => setSelectedTrainerId(Number(e.target.value))}
                  style={{
                    padding: "9px 12px",
                    borderRadius: "8px",
                    background: "var(--member-field)",
                    color: "var(--member-text)",
                    border: "1px solid rgba(255,255,255,0.12)",
                  }}
                >
                  {(ptData.trainers || []).map((t) => (
                    <option key={t.user_id} value={t.user_id}>
                      HLV {t.full_name} ({t.specialization || "Personal Trainer"})
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  className="member-secondary-button"
                  onClick={() => setWeekStart(addDaysStr(weekStart, -7))}
                >
                  ← Tuần trước
                </button>
                <span style={{ fontSize: "13px", fontWeight: 600 }}>
                  Tuần từ {weekStart}
                </span>
                <button
                  type="button"
                  className="member-secondary-button"
                  onClick={() => setWeekStart(addDaysStr(weekStart, 7))}
                >
                  Tuần sau →
                </button>
              </div>
            </div>

            {ptMessage.text && (
              <div
                role="alert"
                style={{
                  padding: "12px 16px",
                  borderRadius: "10px",
                  marginBottom: "14px",
                  fontSize: "13px",
                  background:
                    ptMessage.type === "error"
                      ? "rgba(239, 68, 68, 0.16)"
                      : "rgba(34, 197, 94, 0.16)",
                  border: `1px solid ${
                    ptMessage.type === "error" ? "#ef4444" : "#22c55e"
                  }`,
                  color: ptMessage.type === "error" ? "#fca5a5" : "#86efac",
                }}
              >
                {ptMessage.text}
              </div>
            )}

            <div style={{ overflowX: "auto" }}>
              <table className="pt-calendar-grid">
                <thead>
                  <tr>
                    <th>Khung giờ</th>
                    {weekDays.map((d, idx) => (
                      <th key={d}>
                        <div>{DAY_NAMES[idx]}</div>
                        <small style={{ fontWeight: 400 }}>{d.slice(5)}</small>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {HOURS.map((hour) => (
                    <tr key={hour}>
                      <td style={{ fontWeight: 700 }}>{hour}</td>
                      {weekDays.map((dayStr) => {
                        const existing = (ptData.bookings || []).find(
                          (b) =>
                            b.booking_date === dayStr &&
                            b.start_time === hour &&
                            b.status !== "CANCELLED" &&
                            b.status !== "EXPIRED"
                        );
                        if (existing) {
                          if (existing.is_mine) {
                            const canCancel =
                              existing.status === "PENDING" ||
                              existing.status === "CONFIRMED";
                            return (
                              <td key={dayStr}>
                                <button
                                  type="button"
                                  className="pt-slot-btn pt-slot-mine"
                                  disabled={!canCancel}
                                  onClick={() =>
                                    canCancel &&
                                    handleCancelPTBooking(existing.booking_id)
                                  }
                                  title={
                                    canCancel
                                      ? "Bấm để hủy lịch đặt này (trước giờ tập >= 2 tiếng)"
                                      : `Trạng thái kết thúc: ${existing.status}`
                                  }
                                >
                                  Của bạn ({existing.status})
                                  {canCancel ? " · Hủy" : ""}
                                </button>
                              </td>
                            );
                          }
                          return (
                            <td key={dayStr}>
                              <button
                                type="button"
                                className="pt-slot-btn pt-slot-busy"
                                onClick={() =>
                                  handleBookPTSlot(dayStr, hour)
                                }
                              >
                                Đã kín ({existing.member_name})
                              </button>
                            </td>
                          );
                        }
                        return (
                          <td key={dayStr}>
                            <button
                              type="button"
                              className="pt-slot-btn pt-slot-free"
                              onClick={() => handleBookPTSlot(dayStr, hour)}
                            >
                              + Đặt lịch
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Lớp tập nhóm Yoga, Zumba, HIIT (Bonus T3CD532) */}
          <section className="member-panel" id="group-classes">
            <div style={{ marginBottom: "16px" }}>
              <h2 style={{ margin: 0, fontSize: "17px" }}>
                LỊCH LỚP TẬP NHÓM (YOGA, ZUMBA, HIIT, BOXING)
              </h2>
              <p
                style={{
                  margin: "4px 0 0",
                  fontSize: "13px",
                  color: "var(--member-muted)",
                }}
              >
                Đăng ký giữ chỗ trước khi lớp đủ sĩ số tối đa
              </p>
            </div>

            {classNotice && (
              <p
                style={{
                  padding: "10px 14px",
                  borderRadius: "8px",
                  background: "rgba(249, 115, 22, 0.15)",
                  color: "#ffb690",
                  fontSize: "13px",
                }}
              >
                {classNotice}
              </p>
            )}

            <div className="group-class-grid">
              {groupClasses.map((cls) => (
                <article className="group-class-card" key={cls.class_id}>
                  <div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "8px",
                      }}
                    >
                      <span className="member-badge">{cls.category}</span>
                      <span
                        style={{
                          fontSize: "12px",
                          color: cls.is_full ? "#f87171" : "#4ade80",
                          fontWeight: 600,
                        }}
                      >
                        Sĩ số: {cls.enrolled_count}/{cls.max_capacity}
                      </span>
                    </div>
                    <h3 style={{ margin: "0 0 6px", fontSize: "16px" }}>
                      {cls.class_name}
                    </h3>
                    <p
                      style={{
                        margin: "0 0 8px",
                        fontSize: "12px",
                        color: "var(--member-muted)",
                      }}
                    >
                      {cls.description}
                    </p>
                    <div
                      style={{
                        fontSize: "12px",
                        color: "var(--member-muted)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "4px",
                      }}
                    >
                      <span>
                        📅 {cls.schedule_date} · ⏰ {cls.start_time} -{" "}
                        {cls.end_time}
                      </span>
                      <span>
                        📍 {cls.room} · 👤 {cls.trainer_name}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    className={
                      cls.is_enrolled
                        ? "member-secondary-button"
                        : "member-primary-button"
                    }
                    style={{ width: "100%", justifyContent: "center" }}
                    disabled={!cls.is_enrolled && cls.is_full}
                    onClick={() => handleToggleClassEnroll(cls)}
                  >
                    {cls.is_enrolled
                      ? "Đã đăng ký · Bấm để Hủy"
                      : cls.is_full
                      ? "Đã đủ sĩ số"
                      : "Đăng ký tham gia"}
                  </button>
                </article>
              ))}
            </div>
          </section>

          {/* Lịch sử Check-in có phân trang & lọc theo ngày (Task T067E45) */}
          <section className="member-panel" id="checkin-history">
            <div className="pt-calendar-toolbar">
              <div>
                <h2 style={{ margin: 0, fontSize: "17px" }}>
                  LỊCH SỬ CHECK-IN / CHECK-OUT CỦA BẠN
                </h2>
                <p
                  style={{
                    margin: "4px 0 0",
                    fontSize: "13px",
                    color: "var(--member-muted)",
                  }}
                >
                  Đang có{" "}
                  <b style={{ color: "#4ade80" }}>
                    {historyData.active_in_gym_count} hội viên
                  </b>{" "}
                  tập luyện trong phòng gym ngay lúc này
                </p>
              </div>

              <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                <input
                  type="date"
                  value={dateFilter.from_date}
                  onChange={(e) =>
                    setDateFilter((prev) => ({
                      ...prev,
                      from_date: e.target.value,
                    }))
                  }
                  style={{
                    padding: "8px 10px",
                    borderRadius: "8px",
                    background: "var(--member-field)",
                    color: "var(--member-text)",
                    border: "1px solid rgba(255,255,255,0.12)",
                  }}
                />
                <span>→</span>
                <input
                  type="date"
                  value={dateFilter.to_date}
                  onChange={(e) =>
                    setDateFilter((prev) => ({
                      ...prev,
                      to_date: e.target.value,
                    }))
                  }
                  style={{
                    padding: "8px 10px",
                    borderRadius: "8px",
                    background: "var(--member-field)",
                    color: "var(--member-text)",
                    border: "1px solid rgba(255,255,255,0.12)",
                  }}
                />
                <button
                  type="button"
                  className="member-primary-button"
                  onClick={() => loadCheckInHistory(1)}
                >
                  Lọc lịch sử
                </button>
              </div>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Mã lượt</th>
                    <th>Mã thẻ QR</th>
                    <th>Gói tập</th>
                    <th>Giờ Check-in</th>
                    <th>Giờ Check-out</th>
                    <th>Thời lượng</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {(historyData.items || []).length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: "center", padding: "20px" }}>
                        Chưa có dữ liệu check-in trong khoảng thời gian này.
                      </td>
                    </tr>
                  ) : (
                    historyData.items.map((item) => (
                      <tr key={item.attendance_id}>
                        <td>#{item.attendance_id}</td>
                        <td>{item.member_code}</td>
                        <td>{item.plan_name}</td>
                        <td>{String(item.check_in).replace("T", " ").slice(0, 16)}</td>
                        <td>
                          {item.check_out
                            ? String(item.check_out).replace("T", " ").slice(0, 16)
                            : "Đang trong phòng tập"}
                        </td>
                        <td>
                          {item.duration_minutes
                            ? `${item.duration_minutes} phút`
                            : "--"}
                        </td>
                        <td>
                          <span
                            style={{
                              padding: "4px 8px",
                              borderRadius: "6px",
                              fontSize: "11px",
                              fontWeight: 600,
                              background:
                                item.status === "CHECKED_IN"
                                  ? "rgba(34,197,94,0.18)"
                                  : "rgba(148,163,184,0.18)",
                              color:
                                item.status === "CHECKED_IN"
                                  ? "#4ade80"
                                  : "#cbd5e1",
                            }}
                          >
                            {item.status === "CHECKED_IN"
                              ? "ĐANG TẬP"
                              : "ĐÃ CHECK-OUT"}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {historyData.pages > 1 && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: "8px",
                  marginTop: "14px",
                }}
              >
                <button
                  type="button"
                  className="member-secondary-button"
                  disabled={historyData.page <= 1}
                  onClick={() => loadCheckInHistory(historyData.page - 1)}
                >
                  Trang trước
                </button>
                <span style={{ alignSelf: "center", fontSize: "13px" }}>
                  Trang {historyData.page} / {historyData.pages}
                </span>
                <button
                  type="button"
                  className="member-secondary-button"
                  disabled={historyData.page >= historyData.pages}
                  onClick={() => loadCheckInHistory(historyData.page + 1)}
                >
                  Trang sau
                </button>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
};

export default MemberPage;
