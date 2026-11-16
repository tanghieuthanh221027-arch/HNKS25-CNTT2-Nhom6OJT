import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const workouts = [
  { day: "HÔM NAY", time: "18:30", name: "Cardio & Kháng lực 1:1", trainer: "HLV Trần Tuấn Anh", place: "Studio A · Tầng 2", icon: "fitness_center" },
  { day: "THỨ TƯ", time: "07:00", name: "Functional Training", trainer: "Lớp nhóm · Tối đa 8 người", place: "Studio B · Tầng 1", icon: "groups" },
  { day: "THỨ SÁU", time: "17:00", name: "Tập luyện cùng PT", trainer: "HLV Nguyễn Minh Khoa", place: "Khu Functional", icon: "sports_gymnastics" },
];

const activities = [
  { icon: "local_fire_department", title: "Buổi tập hoàn thành", value: "12 buổi", note: "Trong tháng này" },
  { icon: "timer", title: "Thời gian tập", value: "18,5 giờ", note: "Tăng 12% so với tháng trước" },
  { icon: "bolt", title: "Chuỗi ngày tập", value: "5 ngày", note: "Duy trì đều đặn tuần này" },
];

const memberPageStyles = `
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
.member-page button { color: inherit; font: inherit; cursor: pointer; background: none; border: none; }
.member-page .material-symbols-outlined { font-size: 20px; line-height: 1; }
.member-page a:focus-visible, .member-page button:focus-visible { outline: 2px solid #ffb690; outline-offset: 2px; }

.member-header { position: sticky; z-index: 20; top: 0; border-bottom: 1px solid rgba(255, 255, 255, 0.07); background: rgba(11, 19, 38, 0.9); backdrop-filter: blur(18px); }
.member-nav { display: flex; width: min(1440px, 100%); height: 74px; align-items: center; justify-content: space-between; gap: 24px; margin: 0 auto; padding: 0 clamp(18px, 5vw, 72px); }
.member-brand { display: inline-flex; align-items: center; gap: 10px; flex: 0 0 auto; }
.member-brand-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 9px; background: var(--member-orange); color: #351400; box-shadow: 0 0 20px rgba(249, 115, 22, 0.25); }
.member-brand > span:last-child { display: flex; flex-direction: column; gap: 3px; font-family: "Space Grotesk", Arial, sans-serif; letter-spacing: .08em; }
.member-brand b { font-size: 16px; }
.member-brand small { color: #ffb690; font-size: 9px; letter-spacing: .16em; }

.member-links { display: flex; align-items: center; gap: 8px; }
.member-links a { padding: 10px 14px; border-radius: 7px; color: var(--member-muted); font-size: 13px; font-weight: 500; transition: color .2s, background .2s; }
.member-links a:hover, .member-links a.is-current { background: var(--member-field); color: var(--member-text); }

.member-account { position: relative; }
.member-account-button { display: flex; align-items: center; gap: 10px; padding: 6px 12px 6px 6px; border-radius: 999px; background: var(--member-surface); border: 1px solid rgba(255, 255, 255, 0.08); }
.member-avatar { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; background: var(--member-orange); color: #351400; font-weight: 700; font-size: 13px; }
.member-account-name { display: flex; flex-direction: column; text-align: left; line-height: 1.2; }
.member-account-name b { font-size: 13px; }
.member-account-name small { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: var(--member-muted); }
.member-account-name small i { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; display: inline-block; }
.member-menu { position: absolute; right: 0; top: calc(100% + 8px); width: 210px; background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 6px; box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45); display: flex; flex-direction: column; gap: 4px; }
.member-menu button { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 12px; border-radius: 8px; font-size: 13px; text-align: left; transition: background .2s; }
.member-menu button:hover { background: var(--member-field); }
.member-menu-logout { color: #f87171 !important; }

.member-main { position: relative; overflow: hidden; padding: 36px 0 64px; }
.member-glow { position: absolute; width: 420px; height: 420px; border-radius: 50%; filter: blur(130px); opacity: 0.14; pointer-events: none; }
.member-glow-one { top: -80px; left: -100px; background: var(--member-orange); }
.member-glow-two { bottom: 10%; right: -120px; background: #3b82f6; }
.member-content { position: relative; z-index: 1; width: min(1440px, 100%); margin: 0 auto; padding: 0 clamp(18px, 5vw, 72px); display: flex; flex-direction: column; gap: 36px; }

.member-welcome { display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: stretch; }
.member-welcome-card { background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 20px; padding: 32px; display: flex; flex-direction: column; justify-content: space-between; gap: 28px; }
.member-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; background: rgba(249, 115, 22, 0.15); color: #ffb690; font-size: 11px; font-weight: 600; letter-spacing: .08em; margin-bottom: 12px; }
.member-eyebrow { color: var(--member-muted); font-size: 12px; letter-spacing: .12em; margin: 0 0 6px; }
.member-welcome-copy h1 { font-size: clamp(26px, 3vw, 36px); margin: 0 0 10px; }
.member-welcome-text { color: var(--member-muted); margin: 0; font-size: 15px; line-height: 1.5; }

.member-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.member-stats > div { background: var(--member-surface); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 14px; padding: 16px; display: flex; flex-direction: column; gap: 6px; }
.member-stats > div > .material-symbols-outlined { color: var(--member-orange); margin-bottom: 4px; }
.member-stats small { color: var(--member-muted); font-size: 11px; }
.member-stats b { font-size: 17px; }
.member-stats b em { font-style: normal; font-size: 13px; color: var(--member-muted); font-weight: 400; }

.member-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.member-primary-button, .member-secondary-button { display: inline-flex; align-items: center; gap: 8px; padding: 11px 18px; border-radius: 10px; font-size: 13px; font-weight: 600; transition: transform .15s, opacity .2s; }
.member-primary-button { background: var(--member-orange); color: #351400; }
.member-secondary-button { background: var(--member-field); color: var(--member-text); border: 1px solid rgba(255, 255, 255, 0.08); }
.member-primary-button:hover, .member-secondary-button:hover { transform: translateY(-1px); }

.member-pass-card { background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 20px; padding: 24px; display: flex; flex-direction: column; align-items: center; justify-content: space-between; text-align: center; gap: 16px; }
.member-pass-heading { width: 100%; display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-weight: 600; color: var(--member-muted); letter-spacing: .08em; }
.member-online { display: inline-flex; align-items: center; gap: 5px; color: #4ade80; }
.member-online i { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; }
.member-qr { position: relative; width: 180px; height: 180px; padding: 16px; background: #fff; border-radius: 16px; display: grid; place-items: center; }
.member-qr svg { width: 148px; height: 148px; fill: #0b1326; display: block; }
.member-qr .qr-white { fill: #fff; }
.member-qr-logo { position: absolute; background: var(--member-orange); color: #351400; padding: 6px; border-radius: 8px; }
.member-pass-card p { color: var(--member-muted); font-size: 13px; margin: 0; }
.member-pass-card b { font-size: 15px; letter-spacing: .1em; color: #ffb690; }

.member-section { display: flex; flex-direction: column; gap: 18px; }
.member-section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.member-section-heading > div { display: flex; align-items: center; gap: 12px; }
.member-section-mark { width: 4px; height: 36px; border-radius: 4px; background: var(--member-orange); }
.member-section-heading h2 { margin: 0; font-size: 18px; }
.member-section-heading p { margin: 4px 0 0; font-size: 13px; color: var(--member-muted); }
.member-section-heading a { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: #ffb690; }

.member-workouts { display: grid; gap: 12px; }
.member-workout { background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 14px; padding: 18px 22px; display: grid; grid-template-columns: 90px 44px 1fr auto; align-items: center; gap: 18px; }
.member-workout-time { display: flex; flex-direction: column; gap: 2px; }
.member-workout-time small { font-size: 11px; color: #ffb690; font-weight: 600; }
.member-workout-time b { font-size: 18px; }
.member-workout-icon { width: 44px; height: 44px; border-radius: 12px; background: var(--member-field); display: grid; place-items: center; color: var(--member-orange); }
.member-workout-info h3 { margin: 0 0 4px; font-size: 16px; }
.member-workout-info p { margin: 0 0 6px; font-size: 13px; color: var(--member-muted); }
.member-workout-info small { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: var(--member-muted); }
.member-workout-arrow { color: var(--member-muted); }

.member-activity-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.member-activity { background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 16px; padding: 22px; display: flex; flex-direction: column; gap: 8px; }
.member-activity .material-symbols-outlined { color: var(--member-orange); font-size: 26px; }
.member-activity small { color: var(--member-muted); font-size: 12px; }
.member-activity b { font-size: 24px; }
.member-activity p { margin: 0; font-size: 13px; color: var(--member-muted); }

.member-info-card { background: var(--member-card); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 18px; padding: 26px; display: flex; flex-direction: column; gap: 20px; }
.member-info-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.member-info-header > div { display: flex; align-items: center; gap: 12px; }
.member-info-header .material-symbols-outlined { font-size: 28px; color: var(--member-orange); }
.member-info-header h2 { margin: 0; font-size: 18px; }
.member-info-header p { margin: 4px 0 0; font-size: 13px; color: var(--member-muted); }
.member-info-card dl { margin: 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.member-info-card dl > div { background: var(--member-surface); padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); }
.member-info-card dt { font-size: 12px; color: var(--member-muted); margin-bottom: 6px; }
.member-info-card dd { margin: 0; font-size: 15px; font-weight: 600; word-break: break-word; }

.member-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 20px; border-top: 1px solid rgba(255, 255, 255, 0.07); color: var(--member-muted); font-size: 13px; }
.member-footer a { color: #ffb690; }

@media (max-width: 992px) {
  .member-welcome { grid-template-columns: 1fr; }
  .member-stats, .member-info-card dl { grid-template-columns: repeat(2, 1fr); }
  .member-activity-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .member-links { display: none; }
  .member-stats, .member-info-card dl { grid-template-columns: 1fr; }
  .member-workout { grid-template-columns: 1fr; gap: 10px; }
}
`;

const MemberPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const fullName = user?.full_name || user?.name || user?.username || "Hội viên";
  const initials = fullName
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  const memberCode = user?.user_id
    ? `DG-${String(user.user_id).padStart(6, "0")}`
    : "DG-MEMBER";

  useEffect(() => {
    const closeMenu = (event) => {
      if (!menuRef.current?.contains(event.target)) setMenuOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("mousedown", closeMenu);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeMenu);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  const showMemberInfo = () => {
    setMenuOpen(false);
    navigate("/member/profile");
  };

  const signOut = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="member-page">
      <style>{memberPageStyles}</style>

      <header className="member-header">
        <div className="member-nav">
          <Link className="member-brand" to="/member" aria-label="Ducky Gym trang hội viên">
            <span className="member-brand-icon material-symbols-outlined">fitness_center</span>
            <span>
              <b>DUCKY GYM</b>
              <small>PERFORMANCE CLUB</small>
            </span>
          </Link>

          <nav className="member-links" aria-label="Điều hướng hội viên">
            <a className="is-current" href="#overview">Tổng quan</a>
            <a href="#schedule">Lịch tập</a>
            <a href="#activity">Hoạt động</a>
            <a href="#member-info">Hồ sơ</a>
          </nav>

          <div className="member-account" ref={menuRef}>
            <button
              className="member-account-button"
              type="button"
              aria-expanded={menuOpen}
              aria-haspopup="menu"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span className="member-avatar">{initials || "HV"}</span>
              <span className="member-account-name">
                <b>{fullName}</b>
                <small><i /> Hội viên</small>
              </span>
              <span className="material-symbols-outlined member-chevron">
                {menuOpen ? "expand_less" : "expand_more"}
              </span>
            </button>
            {menuOpen && (
              <div className="member-menu" role="menu">
                <button type="button" role="menuitem" onClick={showMemberInfo}>
                  <span className="material-symbols-outlined">account_circle</span>
                  Thông tin hội viên
                </button>
                <button type="button" role="menuitem" className="member-menu-logout" onClick={signOut}>
                  <span className="material-symbols-outlined">logout</span>
                  Đăng xuất
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="member-main">
        <div className="member-glow member-glow-one" />
        <div className="member-glow member-glow-two" />
        <div className="member-content">
          <section className="member-welcome" id="overview">
            <div className="member-welcome-card">
              <div className="member-welcome-copy">
                <span className="member-badge">
                  <span className="material-symbols-outlined">stars</span> HỘI VIÊN DUCKY GYM
                </span>
                <p className="member-eyebrow">CHÀO MỪNG TRỞ LẠI</p>
                <h1>{fullName}</h1>
                <p className="member-welcome-text">
                  Mỗi buổi tập là một bước tiến. Cùng xem lịch tập và hoạt động gần đây của bạn.
                </p>
              </div>

              <div className="member-stats">
                <div>
                  <span className="material-symbols-outlined">badge</span>
                  <small>MÃ HỘI VIÊN</small>
                  <b>{memberCode}</b>
                  <small className="member-stat-note">Định danh cá nhân</small>
                </div>
                <div>
                  <span className="material-symbols-outlined">calendar_month</span>
                  <small>GÓI TẬP</small>
                  <b>Hội viên</b>
                  <small className="member-stat-note">Xem chi tiết tại quầy</small>
                </div>
                <div>
                  <span className="material-symbols-outlined">sports_gymnastics</span>
                  <small>BUỔI TẬP PT</small>
                  <b>03 <em>/ 24 buổi</em></b>
                  <small className="member-stat-note">Đã hoàn thành</small>
                </div>
                <div>
                  <span className="material-symbols-outlined">verified_user</span>
                  <small>TRẠNG THÁI THẺ</small>
                  <b>Đang hoạt động</b>
                  <small className="member-stat-note">Hợp lệ check-in</small>
                </div>
              </div>

              <div className="member-actions">
                <a className="member-primary-button" href="#member-pass">
                  <span className="material-symbols-outlined">qr_code_scanner</span>
                  Mở thẻ check-in
                </a>
                <a className="member-secondary-button" href="#schedule">
                  <span className="material-symbols-outlined">event_available</span>
                  Xem lịch tập
                </a>
                <Link className="member-secondary-button" to="/membership">
                  <span className="material-symbols-outlined">credit_card</span>
                  Khám phá gói tập
                </Link>
              </div>
            </div>

            <aside className="member-pass-card" id="member-pass">
              <div className="member-pass-heading">
                <span>THẺ HỘI VIÊN ĐIỆN TỬ</span>
                <span className="member-online"><i /> SẴN SÀNG</span>
              </div>
              <div className="member-qr" aria-label="Mã QR check-in minh họa">
                <svg width="148" height="148" viewBox="0 0 160 160" role="img" aria-label="Mã QR minh họa">
                  <rect width="46" height="46" x="0" y="0" rx="5" />
                  <rect width="30" height="30" x="8" y="8" className="qr-white" />
                  <rect width="14" height="14" x="16" y="16" rx="2" />
                  <rect width="46" height="46" x="114" y="0" rx="5" />
                  <rect width="30" height="30" x="122" y="8" className="qr-white" />
                  <rect width="14" height="14" x="130" y="16" rx="2" />
                  <rect width="46" height="46" x="0" y="114" rx="5" />
                  <rect width="30" height="30" x="8" y="122" className="qr-white" />
                  <rect width="14" height="14" x="16" y="130" rx="2" />
                  <path d="M56 10h12v24H56zm20-2h18v12H76zm-12 36h32v10H64zm-54 12h24v10H10zm28 4h16v38H38zm26 8h28v28H64zm38-12h14v30h-14zm26 4h22v10h-22zm-4 20h16v26h-16zm-68 30h20v14H56zm30-2h16v38H86zm26 16h38v14h-38zm-48 12h14v18H64z" />
                </svg>
                <span className="member-qr-logo material-symbols-outlined">fitness_center</span>
              </div>
              <p>Đưa mã này cho nhân viên khi check-in</p>
              <b>{memberCode}</b>
            </aside>
          </section>

          <section className="member-section" id="schedule">
            <div className="member-section-heading">
              <div>
                <span className="member-section-mark" />
                <div>
                  <h2>LỊCH TẬP SẮP TỚI</h2>
                  <p>Lịch luyện tập của bạn trong tuần này</p>
                </div>
              </div>
              <a href="#schedule">
                Xem toàn bộ lịch <span className="material-symbols-outlined">arrow_forward</span>
              </a>
            </div>
            <div className="member-workouts">
              {workouts.map((workout) => (
                <article className="member-workout" key={`${workout.day}-${workout.time}`}>
                  <div className="member-workout-time">
                    <small>{workout.day}</small>
                    <b>{workout.time}</b>
                  </div>
                  <div className="member-workout-icon material-symbols-outlined">{workout.icon}</div>
                  <div className="member-workout-info">
                    <h3>{workout.name}</h3>
                    <p>{workout.trainer}</p>
                    <small>
                      <span className="material-symbols-outlined">location_on</span>
                      {workout.place}
                    </small>
                  </div>
                  <span className="member-workout-arrow material-symbols-outlined">chevron_right</span>
                </article>
              ))}
            </div>
          </section>

          <section className="member-section" id="activity">
            <div className="member-section-heading">
              <div>
                <span className="member-section-mark" />
                <div>
                  <h2>HOẠT ĐỘNG CỦA BẠN</h2>
                  <p>Tổng kết quá trình tập luyện gần đây</p>
                </div>
              </div>
            </div>
            <div className="member-activity-grid">
              {activities.map((item) => (
                <article className="member-activity" key={item.title}>
                  <span className="material-symbols-outlined">{item.icon}</span>
                  <small>{item.title}</small>
                  <b>{item.value}</b>
                  <p>{item.note}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="member-info-card" id="member-info">
            <div className="member-info-header">
              <div>
                <span className="material-symbols-outlined">account_circle</span>
                <div>
                  <h2>THÔNG TIN HỘI VIÊN</h2>
                  <p>Thông tin tài khoản đang đăng nhập</p>
                </div>
              </div>
              <button type="button" className="member-secondary-button" onClick={showMemberInfo}>
                <span className="material-symbols-outlined">edit</span>
                Cập nhật hồ sơ
              </button>
            </div>
            <dl>
              <div>
                <dt>Họ và tên</dt>
                <dd>{fullName}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{user?.email || "Chưa cập nhật"}</dd>
              </div>
              <div>
                <dt>Số điện thoại</dt>
                <dd>{user?.phone || "Chưa cập nhật"}</dd>
              </div>
              <div>
                <dt>Mã hội viên</dt>
                <dd>{memberCode}</dd>
              </div>
            </dl>
          </section>

          <footer className="member-footer">
            <span>© 2026 Ducky Gym · Cùng bạn bền bỉ mỗi ngày</span>
            <a href="mailto:support@duckygym.vn">Hỗ trợ hội viên</a>
          </footer>
        </div>
      </main>
    </div>
  );
};

export default MemberPage;