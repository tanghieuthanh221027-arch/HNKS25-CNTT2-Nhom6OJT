import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import QRCodeDisplay from "../components/QRCodeDisplay";
import { useAuth } from "../context/AuthContext";
import gymApi from "../api/gymApi";
import "./MemberProfilePage.css";

const MemberProfilePage = () => {
  const { user } = useAuth();
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [metrics, setMetrics] = useState([]);
  const [profile, setProfile] = useState({
    fullName: user?.full_name || user?.name || "",
    phone: user?.phone || "",
    email: user?.email || "",
    birthDate: user?.date_of_birth || "2000-01-01",
    gender: user?.gender || "MALE",
    emergencyContact: user?.emergency_contact || "",
    address: user?.address || "Hà Nội",
    height: user?.height_cm || 172,
    weight: user?.weight_kg || 66,
    bmi: user?.bmi || 22.3,
    targetWeight: user?.target_weight_kg || 64,
    weeklyWorkouts: user?.weekly_workouts || "4",
    currentPassword: "",
    newPassword: "",
  });

  const memberCode =
    user?.member_code ||
    (user?.user_id
      ? `DG-${String(user.user_id).padStart(6, "0")}`
      : "DG-000001");

  const loadData = () => {
    gymApi
      .getMe()
      .then((res) => {
        const d = res.data;
        setProfile((prev) => ({
          ...prev,
          fullName: d.full_name || prev.fullName,
          phone: d.phone || prev.phone,
          email: d.email || prev.email,
          birthDate: d.date_of_birth || prev.birthDate,
          gender: d.gender || prev.gender,
          emergencyContact: d.emergency_contact || prev.emergencyContact,
          address: d.address || prev.address,
          height: d.height_cm ?? prev.height,
          weight: d.weight_kg ?? prev.weight,
          bmi: d.bmi ?? prev.bmi,
          targetWeight: d.target_weight_kg ?? prev.targetWeight,
          weeklyWorkouts: String(d.weekly_workouts || prev.weeklyWorkouts),
        }));
      })
      .catch(() => {});

    gymApi
      .getBodyMetrics()
      .then((res) => setMetrics(res.data || []))
      .catch(() => {});
  };

  useEffect(() => {
    loadData();
  }, []);

  const computedBmi =
    profile.height > 0 && profile.weight > 0
      ? (
          Number(profile.weight) /
          Math.pow(Number(profile.height) / 100, 2)
        ).toFixed(1)
      : profile.bmi;

  const updateField = (event) => {
    const { name, value } = event.target;
    setProfile((current) => ({ ...current, [name]: value }));
    setNotice("");
    setError("");
  };

  const saveProfile = async (event) => {
    event.preventDefault();
    setNotice("");
    setError("");
    try {
      const payload = {
        full_name: profile.fullName,
        phone: profile.phone,
        email: profile.email,
        gender: profile.gender,
        date_of_birth: profile.birthDate || undefined,
        address: profile.address,
        emergency_contact: profile.emergencyContact,
        height_cm: Number(profile.height) || undefined,
        weight_kg: Number(profile.weight) || undefined,
        target_weight_kg: Number(profile.targetWeight) || undefined,
        weekly_workouts: Number(profile.weeklyWorkouts) || undefined,
      };
      if (profile.newPassword) {
        payload.current_password = profile.currentPassword;
        payload.new_password = profile.newPassword;
      }
      const res = await gymApi.updateMe(payload);
      setProfile((prev) => ({
        ...prev,
        bmi: res.data.bmi || computedBmi,
        currentPassword: "",
        newPassword: "",
      }));
      setNotice(
        `Đã lưu hồ sơ thành công! Chỉ số BMI hiện tại: ${
          res.data.bmi || computedBmi
        }`
      );
      loadData();
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Cập nhật hồ sơ thất bại."
      );
    }
  };

  const handleLogBodyMetric = async (event) => {
    event.preventDefault();
    setNotice("");
    setError("");
    try {
      await gymApi.addBodyMetric({
        height_cm: Number(profile.height),
        weight_kg: Number(profile.weight),
        notes: "Ghi nhận chỉ số định kỳ",
      });
      setNotice("Đã ghi nhận chỉ số cân nặng & BMI hôm nay vào biểu đồ!");
      loadData();
    } catch (err) {
      setError(
        err.response?.data?.message || "Không thể ghi nhận chỉ số cơ thể."
      );
    }
  };

  return (
    <div className="member-profile-page">
      <header className="profile-header">
        <div className="profile-nav">
          <Link
            className="profile-brand"
            to="/member"
            aria-label="Ducky Gym trang hội viên"
          >
            <span className="material-symbols-outlined">fitness_center</span>
            <span>
              <b>DUCKY GYM</b>
              <small>PERFORMANCE CLUB</small>
            </span>
          </Link>
          <Link className="profile-back" to="/member">
            <span className="material-symbols-outlined">arrow_back</span>Về
            trang hội viên
          </Link>
        </div>
      </header>

      <main className="profile-main">
        <nav className="profile-breadcrumb" aria-label="Đường dẫn">
          <Link to="/member">Trang hội viên</Link>
          <span className="material-symbols-outlined">chevron_right</span>
          <b>Hồ sơ cá nhân &amp; Theo dõi BMI</b>
        </nav>
        <div className="profile-title-row">
          <div>
            <span className="profile-label">
              TÀI KHOẢN HỘI VIÊN · {memberCode}
            </span>
            <h1>Hồ sơ hội viên &amp; Chỉ số BMI</h1>
            <p>
              Cập nhật thông tin cá nhân, đổi mật khẩu và theo dõi biểu đồ cân
              nặng, BMI theo thời gian.
            </p>
          </div>
          <span className="profile-status">
            <i />
            BMI hiện tại: <b>{computedBmi}</b>
          </span>
        </div>

        <div className="profile-layout">
          <aside className="profile-sidebar">
            <section className="profile-card">
              <div className="profile-card-top">
                <span className="profile-card-logo material-symbols-outlined">
                  fitness_center
                </span>
                <b>DUCKY GYM</b>
                <span className="profile-card-tier">MEMBER</span>
              </div>
              <div className="profile-card-chip">
                <span />
                <span />
              </div>
              <div className="profile-card-bottom">
                <b>{profile.fullName || "HỘI VIÊN"}</b>
                <div>
                  <span>{memberCode}</span>
                  <span>BMI {computedBmi}</span>
                </div>
              </div>
            </section>

            <section className="profile-qr-card">
              <div className="profile-card-heading">
                <span className="material-symbols-outlined">qr_code_2</span>
                <h2>Mã QR hội viên</h2>
              </div>
              <div
                className="profile-qr"
                style={{
                  position: "relative",
                  display: "grid",
                  placeItems: "center",
                  background: "#ffffff",
                  padding: "14px",
                  borderRadius: "16px",
                  width: "fit-content",
                  margin: "0 auto",
                }}
              >
                <QRCodeDisplay
                  value={memberCode}
                  size={150}
                  bgColor="#ffffff"
                  fgColor="#0b1326"
                  level="H"
                />
                <span
                  className="material-symbols-outlined"
                  style={{
                    position: "absolute",
                    background: "#f97316",
                    color: "#351400",
                    padding: "4px",
                    borderRadius: "8px",
                    border: "3px solid #ffffff",
                    fontSize: "18px",
                    lineHeight: 1,
                  }}
                >
                  fitness_center
                </span>
              </div>
              <b>{memberCode}</b>
              <p>Thẻ điện tử hội viên</p>
            </section>
          </aside>

          <div className="profile-details">
            {notice && (
              <p
                className="profile-notice"
                role="status"
                style={{
                  padding: "12px 16px",
                  borderRadius: "10px",
                  background: "rgba(34,197,94,0.16)",
                  border: "1px solid #22c55e",
                  color: "#86efac",
                }}
              >
                {notice}
              </p>
            )}
            {error && (
              <p
                role="alert"
                style={{
                  padding: "12px 16px",
                  borderRadius: "10px",
                  background: "rgba(239,68,68,0.16)",
                  border: "1px solid #ef4444",
                  color: "#fca5a5",
                }}
              >
                {error}
              </p>
            )}

            <form className="profile-panel" onSubmit={saveProfile}>
              <div className="profile-panel-heading">
                <span className="material-symbols-outlined">person</span>
                <div>
                  <h2>Thông tin cá nhân &amp; Đổi mật khẩu (PUT /users/me)</h2>
                  <p>
                    Cập nhật hồ sơ và tự động đồng bộ với thẻ hội viên Ducky Gym.
                  </p>
                </div>
              </div>
              <div className="profile-fields">
                <label>
                  Họ và tên
                  <input
                    name="fullName"
                    value={profile.fullName}
                    onChange={updateField}
                    required
                  />
                </label>
                <label>
                  Số điện thoại
                  <input
                    name="phone"
                    type="tel"
                    value={profile.phone}
                    onChange={updateField}
                    required
                  />
                </label>
                <label>
                  Email
                  <input
                    name="email"
                    type="email"
                    value={profile.email}
                    onChange={updateField}
                    required
                  />
                </label>
                <label>
                  Ngày sinh
                  <input
                    name="birthDate"
                    type="date"
                    value={profile.birthDate}
                    onChange={updateField}
                  />
                </label>
                <fieldset className="profile-gender">
                  <legend>Giới tính</legend>
                  {[
                    ["MALE", "Nam"],
                    ["FEMALE", "Nữ"],
                    ["OTHER", "Khác"],
                  ].map(([value, label]) => (
                    <label key={value}>
                      <input
                        type="radio"
                        name="gender"
                        value={value}
                        checked={profile.gender === value}
                        onChange={updateField}
                      />
                      {label}
                    </label>
                  ))}
                </fieldset>
                <label>
                  Liên hệ khẩn cấp
                  <input
                    name="emergencyContact"
                    value={profile.emergencyContact}
                    onChange={updateField}
                    placeholder="Tên và SĐT liên hệ"
                  />
                </label>
                <label className="profile-field-wide">
                  Địa chỉ
                  <input
                    name="address"
                    value={profile.address}
                    onChange={updateField}
                  />
                </label>
                <label>
                  Mật khẩu hiện tại (nếu đổi MK)
                  <input
                    name="currentPassword"
                    type="password"
                    value={profile.currentPassword}
                    onChange={updateField}
                    placeholder="Để trống nếu không đổi"
                  />
                </label>
                <label>
                  Mật khẩu mới (tối thiểu 8 ký tự)
                  <input
                    name="newPassword"
                    type="password"
                    value={profile.newPassword}
                    onChange={updateField}
                    placeholder="Nhập mật khẩu mới"
                  />
                </label>
              </div>
              <div className="profile-form-actions">
                <button className="profile-save" type="submit">
                  <span className="material-symbols-outlined">save</span>Lưu
                  thông tin
                </button>
              </div>
            </form>

            {/* Chỉ số cơ thể & Biểu đồ Cân nặng / BMI theo thời gian (Task T067D56 & Bonus T3CD409) */}
            <form className="profile-panel" onSubmit={handleLogBodyMetric}>
              <div className="profile-panel-heading">
                <span className="material-symbols-outlined">monitoring</span>
                <div>
                  <h2>
                    Chỉ số cơ thể &amp; Biểu đồ theo dõi BMI theo thời gian
                  </h2>
                  <p>
                    Tự động tính chỉ số BMI = Cân nặng / (Chiều cao m)² và vẽ
                    biểu đồ tiến độ.
                  </p>
                </div>
              </div>
              <div className="profile-fields profile-health-fields">
                <label>
                  Chiều cao (cm)
                  <input
                    name="height"
                    type="number"
                    min="100"
                    max="250"
                    step="0.5"
                    value={profile.height}
                    onChange={updateField}
                  />
                </label>
                <label>
                  Cân nặng hiện tại (kg)
                  <input
                    name="weight"
                    type="number"
                    min="25"
                    max="250"
                    step="0.1"
                    value={profile.weight}
                    onChange={updateField}
                  />
                </label>
                <label>
                  Chỉ số BMI (Tự động tính)
                  <input value={computedBmi} readOnly />
                </label>
                <label>
                  Cân nặng mục tiêu (kg)
                  <input
                    name="targetWeight"
                    type="number"
                    min="25"
                    max="250"
                    step="0.1"
                    value={profile.targetWeight}
                    onChange={updateField}
                  />
                </label>
              </div>
              <div
                className="profile-form-actions"
                style={{ display: "flex", gap: "10px" }}
              >
                <button className="profile-save" type="submit">
                  <span className="material-symbols-outlined">add_chart</span>
                  Ghi nhận Cân nặng &amp; BMI hôm nay
                </button>
              </div>

              {/* Biểu đồ xu hướng Cân nặng & BMI */}
              {metrics.length > 0 && (
                <div
                  style={{
                    marginTop: "20px",
                    padding: "16px",
                    borderRadius: "12px",
                    background: "#131b2e",
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  <h3 style={{ margin: "0 0 12px", fontSize: "14px" }}>
                    Biểu đồ lịch sử Cân nặng (kg) &amp; BMI ({metrics.length} lần
                    đo)
                  </h3>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: `repeat(${metrics.length}, minmax(60px, 1fr))`,
                      gap: "10px",
                      alignItems: "end",
                      height: "150px",
                      paddingTop: "20px",
                    }}
                  >
                    {metrics.map((m) => {
                      const w = Number(m.weight_kg);
                      const barHeight = Math.max(30, Math.min(115, (w - 40) * 2.2));
                      return (
                        <div
                          key={m.metric_id}
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
                              fontWeight: 700,
                              color: "#ffb690",
                            }}
                          >
                            {w}kg (BMI {m.bmi})
                          </span>
                          <div
                            style={{
                              width: "34px",
                              height: `${barHeight}px`,
                              borderRadius: "6px 6px 0 0",
                              background:
                                "linear-gradient(180deg, #f97316, #ea580c)",
                            }}
                          />
                          <small
                            style={{ fontSize: "10px", color: "#a6adc2" }}
                          >
                            {String(m.recorded_date).slice(5)}
                          </small>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </form>
          </div>
        </div>
        <footer className="profile-footer">
          <span>© 2026 Ducky Gym</span>
          <Link to="/member">Quay lại trang hội viên</Link>
        </footer>
      </main>
    </div>
  );
};

export default MemberProfilePage;
