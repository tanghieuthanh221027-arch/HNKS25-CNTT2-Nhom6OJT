import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./MemberPage.css";

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
      <header className="member-header">
        <div className="member-nav">
          <Link className="member-brand" to="/member" aria-label="Ducky Gym trang hội viên">
            <span className="member-brand-icon material-symbols-outlined">fitness_center</span>
            <span><b>DUCKY GYM</b><small>PERFORMANCE CLUB</small></span>
          </Link>

          <nav className="member-links" aria-label="Điều hướng hội viên">
            <a className="is-current" href="#overview">Tổng quan</a>
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
                <a className="member-primary-button" href="#member-pass"><span className="material-symbols-outlined">qr_code_scanner</span>Mở thẻ check-in</a>
                <a className="member-secondary-button" href="#schedule"><span className="material-symbols-outlined">event_available</span>Xem lịch tập</a>
                <Link className="member-secondary-button" to="/membership"><span className="material-symbols-outlined">credit_card</span>Khám phá gói tập</Link>
              </div>
            </div>

            <aside className="member-pass-card" id="member-pass">
              <div className="member-pass-heading"><span>THẺ HỘI VIÊN ĐIỆN TỬ</span><span className="member-online"><i /> SẴN SÀNG</span></div>
              <div className="member-qr" aria-label="Mã QR check-in minh họa">
                <svg viewBox="0 0 160 160" role="img" aria-label="Mã QR minh họa">
                  <rect width="46" height="46" x="0" y="0" rx="5"/><rect width="30" height="30" x="8" y="8" className="qr-white"/><rect width="14" height="14" x="16" y="16" rx="2"/>
                  <rect width="46" height="46" x="114" y="0" rx="5"/><rect width="30" height="30" x="122" y="8" className="qr-white"/><rect width="14" height="14" x="130" y="16" rx="2"/>
                  <rect width="46" height="46" x="0" y="114" rx="5"/><rect width="30" height="30" x="8" y="122" className="qr-white"/><rect width="14" height="14" x="16" y="130" rx="2"/>
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
