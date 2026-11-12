import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Register.css";

const plans = [
  { id: "starter", name: "STARTER BASIC", duration: "1 Tháng", price: "499.000", label: "Starter 1T" },
  { id: "pro", name: "PRO FITNESS", duration: "6 Tháng", price: "399.000", label: "Pro 6T" },
  { id: "vip", name: "VIP ELITE", duration: "12 Tháng", price: "299.000", label: "VIP 12T" },
];

const timeOptions = [
  { id: "morning", label: "Sáng sớm", icon: "wb_sunny" },
  { id: "evening", label: "Chiều tối", icon: "nights_stay" },
  { id: "anytime", label: "Tự do (24/7)", icon: "all_inclusive" },
];

const goals = ["Giảm mỡ", "Tăng cơ", "Sức khỏe", "PT riêng"];

const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", confirmPassword: "" });
  const [selectedPlan, setSelectedPlan] = useState("pro");
  const [selectedTime, setSelectedTime] = useState("morning");
  const [selectedGoals, setSelectedGoals] = useState(["Giảm mỡ"]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const plan = plans.find((item) => item.id === selectedPlan);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((currentForm) => ({ ...currentForm, [name]: value }));
  };

  const toggleGoal = (goal) => {
    setSelectedGoals((currentGoals) =>
      currentGoals.includes(goal)
        ? currentGoals.filter((item) => item !== goal)
        : [...currentGoals, goal]
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }

    setLoading(true);
    try {
      await register({ name: form.name, email: form.email, phone: form.phone, password: form.password });
      alert("Đăng ký thành công!");
      navigate("/login");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Đăng ký thất bại!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-page">
      <header className="register-header">
        <Link className="register-brand" to="/login" aria-label="Ducky Gym">
          <span className="material-symbols-outlined">fitness_center</span> Ducky Gym
        </Link>
        <Link className="register-back" to="/login">
          <span className="material-symbols-outlined">arrow_back</span> Quay lại đăng nhập
        </Link>
      </header>

      <main className="register-main">
        <div className="register-layout">
          <aside className="register-aside">
            <section className="register-plan-card">
              <div className="register-plan-tag"><i /> Gói tập đang chọn</div>
              <div className="register-plan-heading">
                <h2>{plan.name}</h2>
                <span>{plan.duration}</span>
              </div>
              <p className="register-price">{plan.price}<small> đ / tháng</small></p>

              <div className="register-gift">
                <span className="material-symbols-outlined">redeem</span>
                <div><b>Quà tặng hôm nay</b><span>Bình nước Titan &amp; 1 buổi InBody chuyên sâu</span></div>
              </div>
              <ul className="register-benefits">
                <li><span className="material-symbols-outlined">check_circle</span> Check-in không giới hạn tại Ducky Gym 24/7</li>
                <li><span className="material-symbols-outlined">check_circle</span> Tủ đồ thông minh và khu Sauna cao cấp</li>
                <li><span className="material-symbols-outlined">check_circle</span> 40+ lớp Yoga, Les Mills &amp; HIIT mỗi tuần</li>
              </ul>

              <div className="register-plan-picker">
                <p>Đổi gói tập nhanh</p>
                <div className="register-plan-options">
                  {plans.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={selectedPlan === item.id ? "is-selected" : ""}
                      aria-pressed={selectedPlan === item.id}
                      onClick={() => setSelectedPlan(item.id)}
                    >
                      {item.label}{selectedPlan === item.id ? " ✓" : ""}
                    </button>
                  ))}
                </div>
              </div>
            </section>

            <div className="register-pass">
              <div><span>Ducky Gym Digital Pass</span><b>Kích hoạt qua ứng dụng sau khi đăng ký</b></div>
              <span className="material-symbols-outlined">contactless</span>
            </div>
          </aside>

          <section className="register-form-card">
            <div className="register-title">
              <h1>Thông tin hội viên mới</h1>
              <p>Hoàn thiện thông tin cơ bản để bắt đầu hành trình tập luyện.</p>
            </div>

            <form className="register-form" onSubmit={handleSubmit}>
              <div className="register-fields two-columns">
                <div className="register-field">
                  <label htmlFor="register-name">Họ và tên</label>
                  <div className="register-input"><span className="material-symbols-outlined">person</span><input id="register-name" name="name" value={form.name} onChange={handleChange} placeholder="Nguyễn Văn A" autoComplete="name" required /></div>
                </div>
                <div className="register-field">
                  <label htmlFor="register-phone">Số điện thoại</label>
                  <div className="register-input"><span className="material-symbols-outlined">smartphone</span><input id="register-phone" name="phone" type="tel" value={form.phone} onChange={handleChange} placeholder="090 123 4567" autoComplete="tel" required /></div>
                </div>
              </div>

              <div className="register-fields two-columns">
                <div className="register-field">
                  <label htmlFor="register-email">Email</label>
                  <div className="register-input"><span className="material-symbols-outlined">alternate_email</span><input id="register-email" name="email" type="email" value={form.email} onChange={handleChange} placeholder="name@example.com" autoComplete="email" required /></div>
                </div>
                <div className="register-field">
                  <label htmlFor="register-branch">Chi nhánh tập chính</label>
                  <div className="register-input"><span className="material-symbols-outlined">storefront</span><select id="register-branch" defaultValue="q1"><option value="q1">Ducky Gym Quận 1 (Nguyễn Huệ)</option><option value="q3">Ducky Gym Quận 3 (Nam Kỳ Khởi Nghĩa)</option><option value="thaodien">Ducky Gym Thảo Điền (TP. Thủ Đức)</option></select><span className="material-symbols-outlined register-select-icon">expand_more</span></div>
                </div>
              </div>

              <fieldset className="register-choice">
                <legend>Khung giờ tập dự kiến</legend>
                <div className="register-time-options">
                  {timeOptions.map((item) => (
                    <button key={item.id} type="button" className={selectedTime === item.id ? "is-selected" : ""} aria-pressed={selectedTime === item.id} onClick={() => setSelectedTime(item.id)}>
                      <span className="material-symbols-outlined">{item.icon}</span>{item.label}
                    </button>
                  ))}
                </div>
              </fieldset>

              <fieldset className="register-choice">
                <legend>Mục tiêu ưu tiên</legend>
                <div className="register-goals">
                  {goals.map((goal) => (
                    <button key={goal} type="button" className={selectedGoals.includes(goal) ? "is-selected" : ""} aria-pressed={selectedGoals.includes(goal)} onClick={() => toggleGoal(goal)}>{goal}</button>
                  ))}
                </div>
              </fieldset>

              <div className="register-fields two-columns">
                <div className="register-field">
                  <label htmlFor="register-password">Mật khẩu</label>
                  <div className="register-input"><span className="material-symbols-outlined">lock</span><input id="register-password" name="password" type="password" value={form.password} onChange={handleChange} placeholder="Tối thiểu 8 ký tự" autoComplete="new-password" minLength="8" required /></div>
                </div>
                <div className="register-field">
                  <label htmlFor="register-confirm-password">Xác nhận mật khẩu</label>
                  <div className="register-input"><span className="material-symbols-outlined">check_circle_outline</span><input id="register-confirm-password" name="confirmPassword" type="password" value={form.confirmPassword} onChange={handleChange} placeholder="Nhập lại mật khẩu" autoComplete="new-password" minLength="8" required /></div>
                </div>
              </div>

              <label className="register-terms"><input type="checkbox" required /><span>Tôi đồng ý với <a href="#terms" onClick={(event) => event.preventDefault()}>điều khoản hội viên Ducky Gym</a> và chính sách dịch vụ.</span></label>
              {error && <p className="register-error" role="alert">{error}</p>}
              <div className="register-actions">
                <button className="register-submit" type="submit" disabled={loading}>
                  {loading ? "Đang đăng ký..." : "Hoàn tất đăng ký hội viên"}
                  <span className="material-symbols-outlined">{loading ? "progress_activity" : "arrow_forward"}</span>
                </button>
                <p>Đã có tài khoản? <Link to="/login">Đăng nhập tại đây</Link></p>
              </div>
            </form>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Register;
