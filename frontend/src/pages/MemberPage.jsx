import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const memberStyles = `.member-page {
  --member-bg: #0b1326;
  --member-surface: #131b2e;
  --member-card: #171f33;
  --member-text: #e3e9f7;
  --member-muted: #9ca8bf;
  --member-accent: #ff9b62;
  min-height: 100vh;
  overflow: hidden;
  background: var(--member-bg);
  color: var(--member-text);
  font-family: Inter, Arial, sans-serif;
}

.member-page *,
.member-page *::before,
.member-page *::after { box-sizing: border-box; }
.member-page a { color: inherit; text-decoration: none; }
.member-page button { color: inherit; font: inherit; }
.member-page .material-symbols-outlined { line-height: 1; }

.member-header {
  position: sticky;
  z-index: 10;
  top: 0;
  border-bottom: 1px solid rgb(255 255 255 / 7%);
  background: rgb(11 19 38 / 92%);
  backdrop-filter: blur(16px);
}

.member-nav {
  display: flex;
  width: min(1440px, 100%);
  height: 72px;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: 0 auto;
  padding: 0 clamp(18px, 5vw, 72px);
}

.member-brand { display: inline-flex; flex: 0 0 auto; align-items: center; gap: 10px; }
.member-brand-icon { color: var(--member-accent); font-size: 25px; }
.member-brand b, .member-brand small { display: block; }
.member-brand b { font-size: 14px; letter-spacing: .08em; }
.member-brand small { margin-top: 4px; color: var(--member-muted); font-size: 8px; letter-spacing: .16em; }
.member-links { display: flex; align-items: center; gap: clamp(16px, 3vw, 36px); }
.member-links a { color: var(--member-muted); font-size: 12px; transition: color .2s; }
.member-links a:hover, .member-links a.member-link-current { color: var(--member-accent); }
.member-account { position: relative; }
.member-account-button { display: flex; align-items: center; gap: 10px; padding: 5px; border: 0; background: transparent; cursor: pointer; text-align: left; }
.member-avatar { display: grid; width: 38px; height: 38px; place-items: center; border: 1px solid rgb(255 155 98 / 35%); border-radius: 50%; background: #29263a; color: var(--member-accent); font-size: 12px; font-weight: 700; }
.member-account-name b, .member-account-name small { display: block; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.member-account-name b { font-size: 11px; }
.member-account-name small { margin-top: 5px; color: var(--member-muted); font-size: 9px; }
.member-account-name small i, .member-online i { display: inline-block; width: 6px; height: 6px; margin-right: 4px; border-radius: 50%; background: #62d6a0; }
.member-chevron { color: var(--member-muted); font-size: 18px; }
.member-menu { position: absolute; top: calc(100% + 10px); right: 0; width: 215px; padding: 6px; border: 1px solid rgb(255 255 255 / 8%); border-radius: 8px; background: #192237; box-shadow: 0 16px 40px rgb(0 0 0 / 32%); }
.member-menu button { display: flex; width: 100%; align-items: center; gap: 10px; padding: 11px; border: 0; border-radius: 5px; background: transparent; color: var(--member-text); cursor: pointer; font-size: 12px; text-align: left; }
.member-menu button:hover { background: rgb(255 255 255 / 6%); }
.member-menu button .material-symbols-outlined { color: var(--member-muted); font-size: 18px; }
.member-menu .member-menu-logout { color: #ff9c9c; }

.member-main { position: relative; min-height: calc(100vh - 72px); }
.member-glow { position: absolute; z-index: 0; width: 400px; height: 400px; border-radius: 50%; background: rgb(249 115 22 / 8%); filter: blur(100px); pointer-events: none; }
.member-glow-one { top: 40px; left: -240px; }
.member-glow-two { top: 470px; right: -280px; background: rgb(55 125 218 / 8%); }
.member-content { position: relative; z-index: 1; width: min(1296px, 100%); margin: 0 auto; padding: 40px clamp(18px, 5vw, 72px) 28px; }
.member-welcome { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 18px; }
.member-welcome-card, .member-pass-card, .member-workout, .member-activity, .member-info-card { border: 1px solid rgb(255 255 255 / 6%); border-radius: 10px; background: var(--member-surface); }
.member-welcome-card { position: relative; overflow: hidden; padding: clamp(24px, 4vw, 42px); background: radial-gradient(ellipse at 90% 0%, rgb(255 155 98 / 13%), transparent 42%), var(--member-surface); }
.member-badge { display: inline-flex; align-items: center; gap: 6px; color: var(--member-accent); font-size: 9px; font-weight: 700; letter-spacing: .13em; }
.member-badge .material-symbols-outlined { font-size: 16px; }
.member-eyebrow { margin: 30px 0 8px; color: var(--member-muted); font-size: 10px; font-weight: 700; letter-spacing: .16em; }
.member-welcome-card h1 { margin: 0; font-size: clamp(28px, 4vw, 42px); letter-spacing: -.04em; }
.member-welcome-text { max-width: 570px; margin: 12px 0 26px; color: var(--member-muted); font-size: 13px; line-height: 1.7; }
.member-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.member-stats > div { display: flex; min-height: 105px; flex-direction: column; align-items: flex-start; gap: 7px; padding: 13px; border: 1px solid rgb(255 255 255 / 6%); border-radius: 7px; background: rgb(7 14 29 / 36%); }
.member-stats > div > .material-symbols-outlined { color: var(--member-accent); font-size: 19px; }
.member-stats small { color: var(--member-muted); font-size: 8px; font-weight: 700; letter-spacing: .07em; }
.member-stats b { font-size: 12px; }
.member-stats em { color: var(--member-muted); font-size: 9px; font-style: normal; font-weight: 400; }
.member-stats .member-stat-note { font-size: 8px; font-weight: 400; letter-spacing: 0; }
.member-actions { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 20px; }
.member-primary-button, .member-secondary-button { display: inline-flex; min-height: 39px; align-items: center; justify-content: center; gap: 7px; padding: 0 13px; border: 1px solid rgb(255 255 255 / 10%); border-radius: 5px; font-size: 10px; font-weight: 700; transition: transform .2s, background .2s; }
.member-primary-button { border-color: var(--member-accent); background: var(--member-accent); color: #291406 !important; }
.member-secondary-button { background: rgb(255 255 255 / 3%); }
.member-primary-button:hover, .member-secondary-button:hover { transform: translateY(-2px); }
.member-actions .material-symbols-outlined { font-size: 16px; }

.member-pass-card { display: flex; flex-direction: column; align-items: center; padding: 20px; background: linear-gradient(155deg, #202940, #11192b 68%); text-align: center; }
.member-pass-heading { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 8px; color: var(--member-muted); font-size: 8px; font-weight: 700; letter-spacing: .08em; }
.member-online { color: #8ce0b8; white-space: nowrap; }
.member-online i { width: 5px; height: 5px; }
.member-qr { position: relative; display: grid; width: 164px; height: 164px; place-items: center; margin: 26px auto 14px; padding: 8px; border-radius: 7px; background: #fff; }
.member-qr svg { display: block; width: 100%; height: 100%; fill: #111827; }
.member-qr .member-qr-white { fill: #fff; }
.member-qr-logo { position: absolute; display: grid; width: 32px; height: 32px; place-items: center; border: 4px solid #fff; border-radius: 7px; background: var(--member-accent); color: #21150e; font-size: 17px; }
.member-pass-card > p { margin: 0 0 8px; color: var(--member-muted); font-size: 10px; }
.member-pass-card > b { color: var(--member-accent); font-size: 12px; letter-spacing: .1em; }

.member-section { margin-top: 38px; }
.member-section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 15px; }
.member-section-heading > div:first-child { display: flex; align-items: center; gap: 12px; }
.member-section-mark { width: 3px; height: 33px; border-radius: 4px; background: var(--member-accent); }
.member-section-heading h2, .member-info-card h2 { margin: 0; font-size: 13px; letter-spacing: .08em; }
.member-section-heading p, .member-info-card p { margin: 5px 0 0; color: var(--member-muted); font-size: 10px; }
.member-section-heading > a { display: inline-flex; align-items: center; gap: 5px; color: var(--member-accent); font-size: 10px; }
.member-section-heading > a .material-symbols-outlined { font-size: 15px; }
.member-workouts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.member-workout { display: grid; grid-template-columns: auto 38px minmax(0, 1fr) 16px; align-items: center; gap: 11px; padding: 16px 13px; transition: border-color .2s, transform .2s; }
.member-workout:hover { transform: translateY(-2px); border-color: rgb(255 155 98 / 35%); }
.member-workout-time { display: flex; flex-direction: column; gap: 6px; }
.member-workout-time small { color: var(--member-muted); font-size: 8px; font-weight: 700; }
.member-workout-time b { font-size: 14px; }
.member-workout-icon { display: grid; width: 36px; height: 36px; place-items: center; border-radius: 7px; background: rgb(255 155 98 / 11%); color: var(--member-accent); font-size: 19px; }
.member-workout-info { min-width: 0; }
.member-workout-info h3 { overflow: hidden; margin: 0; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.member-workout-info p { overflow: hidden; margin: 5px 0; color: var(--member-muted); font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.member-workout-info > small { display: flex; align-items: center; gap: 3px; color: #7f8ba3; font-size: 8px; }
.member-workout-info > small .material-symbols-outlined { font-size: 12px; }
.member-workout-arrow { color: var(--member-muted); font-size: 17px; }
.member-activity-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.member-activity { display: grid; grid-template-columns: 34px 1fr; align-items: center; column-gap: 10px; padding: 17px; }
.member-activity > .material-symbols-outlined { display: grid; width: 34px; height: 34px; grid-row: span 3; place-items: center; border-radius: 7px; background: rgb(255 155 98 / 11%); color: var(--member-accent); font-size: 19px; }
.member-activity > small { color: var(--member-muted); font-size: 9px; }
.member-activity > b { margin-top: 4px; font-size: 17px; }
.member-activity > p { margin: 4px 0 0; color: #7f8ba3; font-size: 9px; }
.member-info-card { display: flex; align-items: flex-start; justify-content: space-between; gap: 28px; margin-top: 38px; padding: 22px; }
.member-info-card > div:first-child { display: flex; align-items: center; gap: 11px; flex: 0 0 auto; }
.member-info-card > div:first-child > .material-symbols-outlined { color: var(--member-accent); font-size: 23px; }
.member-info-card dl { display: grid; width: min(700px, 70%); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 24px; margin: 0; }
.member-info-card dl > div { min-width: 0; }
.member-info-card dt { margin-bottom: 5px; color: var(--member-muted); font-size: 9px; }
.member-info-card dd { overflow: hidden; margin: 0; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.member-footer { display: flex; justify-content: space-between; gap: 15px; padding-top: 24px; color: #77829a; font-size: 9px; }
.member-footer a { color: var(--member-accent); }

@media (max-width: 900px) {
  .member-welcome { grid-template-columns: minmax(0, 1fr) 250px; }
  .member-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .member-workouts { grid-template-columns: 1fr; }
}

@media (max-width: 680px) {
  .member-nav { height: 64px; gap: 12px; padding: 0 16px; }
  .member-links { display: none; }
  .member-account-name { display: none; }
  .member-content { padding: 22px 16px; }
  .member-welcome { grid-template-columns: 1fr; }
  .member-welcome-card { padding: 23px 18px; }
  .member-eyebrow { margin-top: 23px; }
  .member-pass-card { min-height: 310px; }
  .member-qr { width: 145px; height: 145px; margin-top: 18px; }
  .member-activity-grid { grid-template-columns: 1fr; }
  .member-info-card { flex-direction: column; gap: 20px; padding: 18px; }
  .member-info-card dl { width: 100%; gap: 14px; }
  .member-section-heading { align-items: flex-start; }
  .member-section-heading > a { max-width: 100px; text-align: right; }
}

@media (max-width: 420px) {
  .member-stats { grid-template-columns: 1fr 1fr; }
  .member-actions > a { flex: 1 1 100%; }
  .member-workout { grid-template-columns: auto 32px minmax(0, 1fr) 14px; gap: 8px; padding: 13px 10px; }
  .member-info-card dl { grid-template-columns: 1fr; }
  .member-footer { flex-direction: column; }
}
`;

const workouts = [
  { day: "HÔM NAY", time: "18:30", name: "Cardio & Kháng lực 1:1", trainer: "HLV Trần Tuấn Anh", place: "Studio A · Tầng 2", icon: "fitness_center" },
  { day: "THỨ TƯ", time: "07:00", name: "Functional Training", trainer: "Lớp nhóm · Tối đa 8 người", place: "Studio B · Tầng 1", icon: "groups" },
  { day: "THỨ SÁU", time: "17:00", name: "Đánh giá thể lực", trainer: "HLV Nguyễn Minh Khoa", place: "Khu InBody", icon: "monitor_heart" },
];

const activities = [
  { icon: "local_fire_department", title: "Buổi tập hoàn thành", value: "12 buổi", note: "Trong tháng này" },
  { icon: "timer", title: "Thời gian tập", value: "18,5 giờ", note: "Tăng 12% so với tháng trước" },
  { icon: "monitor_weight", title: "InBody gần nhất", value: "68,5 kg", note: "Cập nhật ngày 12/10" },
];

const MemberPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const fullName = user?.full_name || user?.name || user?.username || "Hội viên";
  const initials = fullName.trim().split(/\s+/).slice(-2).map((part) => part[0]).join("").toUpperCase();

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
      <style>{memberStyles}</style>
      <header className="member-header">
        <div className="member-nav">
          <Link className="member-brand" to="/member" aria-label="Ducky Gym trang hội viên">
            <span className="member-brand-icon material-symbols-outlined">fitness_center</span>
            <span><b>DUCKY GYM</b><small>PERFORMANCE CLUB</small></span>
          </Link>

          <nav className="member-links" aria-label="Điều hướng hội viên">
            <a className="member-link-current" href="#overview">Tổng quan</a>
            <a href="#schedule">Lịch tập</a>
            <a href="#activity">Hoạt động</a>
          </nav>

          <div className="member-account" ref={menuRef}>
            <button className="member-account-button" type="button" aria-expanded={menuOpen} aria-haspopup="menu" onClick={() => setMenuOpen((open) => !open)}>
              <span className="member-avatar">{initials || "HV"}</span>
              <span className="member-account-name"><b>{fullName}</b><small><i /> Hội viên</small></span>
              <span className="material-symbols-outlined member-chevron">{menuOpen ? "expand_less" : "expand_more"}</span>
            </button>
            {menuOpen && (
              <div className="member-menu" role="menu">
                <button type="button" role="menuitem" onClick={showMemberInfo}><span className="material-symbols-outlined">account_circle</span>Thông tin hội viên</button>
                <button type="button" role="menuitem" className="member-menu-logout" onClick={signOut}><span className="material-symbols-outlined">logout</span>Đăng xuất</button>
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
                <span className="member-badge"><span className="material-symbols-outlined">stars</span> HỘI VIÊN DUCKY GYM</span>
                <p className="member-eyebrow">CHÀO MỪNG TRỞ LẠI</p>
                <h1>{fullName}</h1>
                <p className="member-welcome-text">Mỗi buổi tập là một bước tiến. Cùng xem lịch tập và hoạt động gần đây của bạn.</p>
              </div>
              <div className="member-stats">
                <div><span className="material-symbols-outlined">badge</span><small>MÃ HỘI VIÊN</small><b>{user?.user_id ? `DG-${String(user.user_id).padStart(6, "0")}` : "DG-MEMBER"}</b></div>
                <div><span className="material-symbols-outlined">calendar_month</span><small>GÓI TẬP</small><b>Hội viên</b><small className="member-stat-note">Xem chi tiết tại quầy</small></div>
                <div><span className="material-symbols-outlined">sports_gymnastics</span><small>BUỔI TẬP PT</small><b>03 <em>/ 24 buổi</em></b><small className="member-stat-note">Đã hoàn thành</small></div>
                <div><span className="material-symbols-outlined">monitor_weight</span><small>INBODY GẦN NHẤT</small><b>68,5 <em>kg</em></b><small className="member-stat-note">Mỡ cơ thể 14,2%</small></div>
              </div>
              <div className="member-actions">
                <Link className="member-primary-button" to="/member/check-in"><span className="material-symbols-outlined">qr_code_scanner</span>Mở thẻ check-in?i?m danh QR check-in</Link>
                <a className="member-secondary-button" href="#schedule"><span className="material-symbols-outlined">event_available</span>Xem lịch tập</a>
                <Link className="member-secondary-button" to="/membership"><span className="material-symbols-outlined">credit_card</span>Khám phá gói tập</Link>
              </div>
            </div>

            <aside className="member-pass-card" id="member-pass">
              <div className="member-pass-heading"><span>THẺ HỘI VIÊN ĐIỆN TỬ</span><span className="member-online"><i /> SẴN SÀNG</span></div>
              <div className="member-qr" aria-label="Mã QR check-in minh họa">
                <svg viewBox="0 0 160 160" role="img" aria-label="Mã QR minh họa">
                  <rect width="46" height="46" x="0" y="0" rx="5"/><rect width="30" height="30" x="8" y="8" className="member-qr-white"/><rect width="14" height="14" x="16" y="16" rx="2"/>
                  <rect width="46" height="46" x="114" y="0" rx="5"/><rect width="30" height="30" x="122" y="8" className="member-qr-white"/><rect width="14" height="14" x="130" y="16" rx="2"/>
                  <rect width="46" height="46" x="0" y="114" rx="5"/><rect width="30" height="30" x="8" y="122" className="member-qr-white"/><rect width="14" height="14" x="16" y="130" rx="2"/>
                  <path d="M56 10h12v24H56zm20-2h18v12H76zm-12 36h32v10H64zm-54 12h24v10H10zm28 4h16v38H38zm26 8h28v28H64zm38-12h14v30h-14zm26 4h22v10h-22zm-4 20h16v26h-16zm-68 30h20v14H56zm30-2h16v38H86zm26 16h38v14h-38zm-48 12h14v18H64z"/>
                </svg>
                <span className="member-qr-logo material-symbols-outlined">fitness_center</span>
              </div>
              <p>Đưa mã này cho nhân viên khi check-in</p>
              <b>{user?.user_id ? `DG-${String(user.user_id).padStart(6, "0")}` : "DUCKY GYM MEMBER"}</b>
            </aside>
          </section>

          <section className="member-section" id="schedule">
            <div className="member-section-heading"><div><span className="member-section-mark" /><div><h2>LỊCH TẬP SẮP TỚI</h2><p>Lịch luyện tập của bạn trong tuần này</p></div></div><a href="#schedule">Xem toàn bộ lịch <span className="material-symbols-outlined">arrow_forward</span></a></div>
            <div className="member-workouts">
              {workouts.map((workout) => <article className="member-workout" key={`${workout.day}-${workout.time}`}>
                <div className="member-workout-time"><small>{workout.day}</small><b>{workout.time}</b></div>
                <div className="member-workout-icon material-symbols-outlined">{workout.icon}</div>
                <div className="member-workout-info"><h3>{workout.name}</h3><p>{workout.trainer}</p><small><span className="material-symbols-outlined">location_on</span>{workout.place}</small></div>
                <span className="member-workout-arrow material-symbols-outlined">chevron_right</span>
              </article>)}
            </div>
          </section>

          <section className="member-section" id="activity">
            <div className="member-section-heading"><div><span className="member-section-mark" /><div><h2>HOẠT ĐỘNG CỦA BẠN</h2><p>Tổng kết quá trình tập luyện gần đây</p></div></div></div>
            <div className="member-activity-grid">
              {activities.map((item) => <article className="member-activity" key={item.title}><span className="material-symbols-outlined">{item.icon}</span><small>{item.title}</small><b>{item.value}</b><p>{item.note}</p></article>)}
            </div>
          </section>

          <section className="member-info-card" id="member-info">
            <div><span className="material-symbols-outlined">account_circle</span><div><h2>THÔNG TIN HỘI VIÊN</h2><p>Thông tin tài khoản đang đăng nhập</p></div></div>
            <dl><div><dt>Họ và tên</dt><dd>{fullName}</dd></div><div><dt>Email</dt><dd>{user?.email || "Chưa cập nhật"}</dd></div><div><dt>Số điện thoại</dt><dd>{user?.phone || "Chưa cập nhật"}</dd></div><div><dt>Mã hội viên</dt><dd>{user?.user_id ? `DG-${String(user.user_id).padStart(6, "0")}` : "Chưa cập nhật"}</dd></div></dl>
          </section>

          <footer className="member-footer"><span>© 2026 Ducky Gym · Cùng bạn bền bỉ mỗi ngày</span><a href="mailto:support@duckygym.vn">Hỗ trợ hội viên</a></footer>
        </div>
      </main>
    </div>
  );
};

export default MemberPage;
