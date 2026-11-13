import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./MemberProfilePage.css";

const MemberProfilePage = () => {
  const { user } = useAuth();
  const [notice, setNotice] = useState("");
  const [profile, setProfile] = useState({
    fullName: user?.full_name || user?.name || "",
    phone: user?.phone || "",
    email: user?.email || "",
    birthDate: user?.date_of_birth || "",
    gender: user?.gender || "",
    emergencyContact: "",
    address: user?.address || "",
    height: "",
    weight: "",
    targetWeight: "",
    weeklyWorkouts: "",
  });
  const memberCode = user?.user_id ? `DG-${String(user.user_id).padStart(6, "0")}` : "Chưa cấp mã";

  const updateField = (event) => {
    const { name, value } = event.target;
    setProfile((current) => ({ ...current, [name]: value }));
    setNotice("");
  };

  const saveProfile = (event) => {
    event.preventDefault();
    setNotice("Thông tin đã được cập nhật trong trang này. Chức năng lưu lên hệ thống chưa được kết nối.");
  };

  return (
    <div className="member-profile-page">
      <header className="profile-header">
        <div className="profile-nav">
          <Link className="profile-brand" to="/member" aria-label="Ducky Gym trang hội viên">
            <span className="material-symbols-outlined">fitness_center</span>
            <span><b>DUCKY GYM</b><small>PERFORMANCE CLUB</small></span>
          </Link>
          <Link className="profile-back" to="/member"><span className="material-symbols-outlined">arrow_back</span>Về trang hội viên</Link>
        </div>
      </header>

      <main className="profile-main">
        <nav className="profile-breadcrumb" aria-label="Đường dẫn"><Link to="/member">Trang hội viên</Link><span className="material-symbols-outlined">chevron_right</span><b>Thông tin cá nhân</b></nav>
        <div className="profile-title-row">
          <div>
            <span className="profile-label">TÀI KHOẢN HỘI VIÊN · {memberCode}</span>
            <h1>Hồ sơ hội viên</h1>
            <p>Quản lý thông tin liên hệ và mục tiêu tập luyện của bạn.</p>
          </div>
          <span className="profile-status"><i />Tài khoản đang hoạt động</span>
        </div>

        <div className="profile-layout">
          <aside className="profile-sidebar">
            <section className="profile-card">
              <div className="profile-card-top"><span className="profile-card-logo material-symbols-outlined">fitness_center</span><b>DUCKY GYM</b><span className="profile-card-tier">MEMBER</span></div>
              <div className="profile-card-chip"><span /><span /></div>
              <div className="profile-card-bottom"><b>{profile.fullName || "HỘI VIÊN"}</b><div><span>{memberCode}</span><span>DUCKY GYM</span></div></div>
            </section>

            <section className="profile-qr-card">
              <div className="profile-card-heading"><span className="material-symbols-outlined">qr_code_2</span><h2>Mã hội viên</h2></div>
              <div className="profile-qr" aria-label="Mã QR minh họa"><svg viewBox="0 0 100 100" aria-hidden="true"><path d="M5 5h28v28H5zm6 6v16h16V11zm5 5h6v6h-6zM67 5h28v28H67zm6 6v16h16V11zm5 5h6v6h-6zM5 67h28v28H5zm6 6v16h16V73zm5 5h6v6h-6zM40 6h8v8h-8zm12 0h8v14h-8zM39 23h17v8H39zm-31 17h11v8H8zm18 0h9v18h-9zm14 2h17v9H40zm22-4h8v17h-8zm13 0h18v8H75zM39 62h10v8H39zm17-4h8v19h-8zm16 5h9v9h-9zm13 11h10v8H85zM39 78h17v8H39zm25 0h8v17h-8zm14 5h17v8H78z"/></svg></div>
              <b>{memberCode}</b><p>Thẻ điện tử hội viên</p>
            </section>

            <section className="profile-help"><span className="material-symbols-outlined">support_agent</span><div><b>Cần hỗ trợ?</b><p>Liên hệ quầy lễ tân để cập nhật gói tập hoặc thông tin tài khoản.</p></div></section>
          </aside>

          <div className="profile-details">
            <form className="profile-panel" onSubmit={saveProfile}>
              <div className="profile-panel-heading"><span className="material-symbols-outlined">person</span><div><h2>Thông tin cá nhân</h2><p>Kiểm tra thông tin để phòng tập có thể liên hệ với bạn.</p></div></div>
              <div className="profile-fields">
                <label>Họ và tên<input name="fullName" value={profile.fullName} onChange={updateField} placeholder="Nhập họ và tên" autoComplete="name" /></label>
                <label>Số điện thoại<input name="phone" type="tel" value={profile.phone} onChange={updateField} placeholder="Chưa cập nhật" autoComplete="tel" /></label>
                <label>Email<input name="email" type="email" value={profile.email} onChange={updateField} placeholder="Chưa cập nhật" autoComplete="email" /></label>
                <label>Ngày sinh<input name="birthDate" type="date" value={profile.birthDate} onChange={updateField} /></label>
                <fieldset className="profile-gender"><legend>Giới tính</legend>{[["MALE", "Nam"], ["FEMALE", "Nữ"], ["OTHER", "Khác"]].map(([value, label]) => <label key={value}><input type="radio" name="gender" value={value} checked={profile.gender === value} onChange={updateField} />{label}</label>)}</fieldset>
                <label>Liên hệ khẩn cấp<input name="emergencyContact" value={profile.emergencyContact} onChange={updateField} placeholder="Tên và số điện thoại liên hệ" /></label>
                <label className="profile-field-wide">Địa chỉ<input name="address" value={profile.address} onChange={updateField} placeholder="Nhập địa chỉ của bạn" autoComplete="street-address" /></label>
              </div>
              <div className="profile-form-actions"><button className="profile-save" type="submit"><span className="material-symbols-outlined">save</span>Lưu thay đổi</button></div>
              {notice && <p className="profile-notice" role="status">{notice}</p>}
            </form>

            <form className="profile-panel" onSubmit={saveProfile}>
              <div className="profile-panel-heading"><span className="material-symbols-outlined">monitoring</span><div><h2>Mục tiêu thể lực</h2><p>Cập nhật chỉ số để theo dõi quá trình luyện tập.</p></div></div>
              <div className="profile-fields profile-health-fields">
                <label>Chiều cao (cm)<input name="height" type="number" min="0" value={profile.height} onChange={updateField} placeholder="Chưa cập nhật" /></label>
                <label>Cân nặng hiện tại (kg)<input name="weight" type="number" min="0" step="0.1" value={profile.weight} onChange={updateField} placeholder="Chưa cập nhật" /></label>
                <label>Cân nặng mục tiêu (kg)<input name="targetWeight" type="number" min="0" step="0.1" value={profile.targetWeight} onChange={updateField} placeholder="Chưa cập nhật" /></label>
                <label>Số buổi tập mỗi tuần<select name="weeklyWorkouts" value={profile.weeklyWorkouts} onChange={updateField}><option value="">Chọn tần suất</option><option value="3">3 buổi</option><option value="4">4 buổi</option><option value="5">5 buổi</option><option value="6">6 buổi</option></select></label>
              </div>
              <div className="profile-form-actions"><button className="profile-save" type="submit"><span className="material-symbols-outlined">update</span>Cập nhật mục tiêu</button></div>
            </form>

            <section className="profile-panel profile-account-help"><span className="material-symbols-outlined">manage_accounts</span><div><h2>Quản lý tài khoản</h2><p>Để tạm ngưng thẻ hoặc yêu cầu xóa tài khoản, vui lòng liên hệ nhân viên tại quầy. Các thao tác này cần được xác nhận trực tiếp.</p></div></section>
          </div>
        </div>
        <footer className="profile-footer"><span>© 2026 Ducky Gym</span><Link to="/member">Quay lại trang hội viên</Link></footer>
      </main>
    </div>
  );
};

export default MemberProfilePage;
