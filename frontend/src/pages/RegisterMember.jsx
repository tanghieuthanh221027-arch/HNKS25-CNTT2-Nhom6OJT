import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./RegisterMember.css";

const RegisterMember = () => {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    fullName: "",
    phone: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((currentForm) => ({ ...currentForm, [name]: value }));
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
      await register({
        name: form.fullName,
        email: form.email,
        phone: form.phone,
        password: form.password,
      });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Đăng ký thất bại. Vui lòng thử lại.");
      setLoading(false);
      return;
    }

    try {
      await login({ email: form.email, password: form.password });
      navigate("/", { state: { message: "Tài khoản đã được tạo. Chọn gói tập để tiếp tục nhé." } });
    } catch {
      navigate("/login", { state: { message: "Tài khoản đã được tạo. Đăng nhập để tiếp tục chọn gói tập.", from: "/" } });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="member-register-page">
      <header className="member-register-header">
        <Link className="member-register-brand" to="/" aria-label="Ducky Gym trang chủ">
          <span className="member-register-logo"><span className="material-symbols-outlined">fitness_center</span></span>
          <span>Ducky Gym</span>
        </Link>
        <Link className="member-register-login" to="/login">Đã có tài khoản? <b>Đăng nhập</b></Link>
      </header>

      <main className="member-register-main">
        <section className="member-register-card">
          <div className="member-register-intro">
            <div className="member-register-intro-content">
              <p className="member-register-eyebrow"><span /> Gia nhập cộng đồng Ducky Gym</p>
              <h1>Bắt đầu hành trình <em>khỏe hơn</em> từ hôm nay.</h1>
              <p className="member-register-description">Tạo tài khoản hội viên để khám phá lớp tập, theo dõi tiến độ và kết nối cùng đội ngũ huấn luyện viên.</p>
              <ul className="member-register-benefits">
                <li><span className="material-symbols-outlined">verified</span> Lộ trình tập luyện phù hợp với mục tiêu</li>
                <li><span className="material-symbols-outlined">schedule</span> Linh hoạt lựa chọn lịch tập của bạn</li>
                <li><span className="material-symbols-outlined">groups</span> Đồng hành cùng cộng đồng Ducky Gym</li>
              </ul>
            </div>
          </div>

          <div className="member-register-form-side">
            <div className="member-register-form-wrap">
              <div className="member-register-title">
                <p className="member-register-step">Đăng ký hội viên</p>
                <h2>Tạo tài khoản</h2>
                <p>Điền thông tin của bạn để tham gia Ducky Gym.</p>
                <p className="member-register-note">Miễn phí tập thử 3 ngày cho hội viên mới.</p>
              </div>

              <form className="member-register-form" onSubmit={handleSubmit}>
                <div className="member-register-field">
                  <label htmlFor="member-full-name">Họ và tên</label>
                  <div className="member-register-input">
                    <span className="material-symbols-outlined">person</span>
                    <input id="member-full-name" name="fullName" value={form.fullName} onChange={handleChange} placeholder="Ví dụ: Nguyễn Văn Hoàng" autoComplete="name" required />
                  </div>
                </div>

                <div className="member-register-field">
                  <label htmlFor="member-phone">Số điện thoại</label>
                  <div className="member-register-input">
                    <span className="material-symbols-outlined">call</span>
                    <input id="member-phone" name="phone" type="tel" value={form.phone} onChange={handleChange} placeholder="09xx xxx xxx" pattern="[0-9]{10,11}" autoComplete="tel" title="Nhập số điện thoại gồm 10 hoặc 11 chữ số" required />
                  </div>
                </div>

                <div className="member-register-field">
                  <label htmlFor="member-email">Email</label>
                  <div className="member-register-input">
                    <span className="material-symbols-outlined">mail</span>
                    <input id="member-email" name="email" type="email" value={form.email} onChange={handleChange} placeholder="ten@email.com" autoComplete="email" required />
                  </div>
                </div>

                <div className="member-register-field">
                  <label htmlFor="member-password">Mật khẩu</label>
                  <div className="member-register-input">
                    <span className="material-symbols-outlined">lock</span>
                    <input id="member-password" name="password" type={showPassword ? "text" : "password"} value={form.password} onChange={handleChange} placeholder="Tối thiểu 8 ký tự" autoComplete="new-password" minLength="8" required />
                    <button type="button" className="member-register-password-toggle" aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"} onClick={() => setShowPassword((visible) => !visible)}>
                      <span className="material-symbols-outlined">{showPassword ? "visibility_off" : "visibility"}</span>
                    </button>
                  </div>
                </div>

                <div className="member-register-field">
                  <label htmlFor="member-confirm-password">Xác nhận mật khẩu</label>
                  <div className="member-register-input">
                    <span className="material-symbols-outlined">lock_reset</span>
                    <input id="member-confirm-password" name="confirmPassword" type={showConfirmPassword ? "text" : "password"} value={form.confirmPassword} onChange={handleChange} placeholder="Nhập lại mật khẩu" autoComplete="new-password" minLength="8" required />
                    <button type="button" className="member-register-password-toggle" aria-label={showConfirmPassword ? "Ẩn mật khẩu xác nhận" : "Hiện mật khẩu xác nhận"} onClick={() => setShowConfirmPassword((visible) => !visible)}>
                      <span className="material-symbols-outlined">{showConfirmPassword ? "visibility_off" : "visibility"}</span>
                    </button>
                  </div>
                </div>

                <label className="member-register-terms">
                  <input type="checkbox" required />
                  <span>Tôi đồng ý với <a href="#terms" onClick={(event) => event.preventDefault()}>điều khoản sử dụng</a> và chính sách bảo mật.</span>
                </label>

                {error && <p className="member-register-error" role="alert">{error}</p>}

                <button className="member-register-submit" type="submit" disabled={loading}>
                  {loading ? "Đang tạo tài khoản..." : "Tạo tài khoản hội viên"}
                  <span className="material-symbols-outlined">{loading ? "progress_activity" : "arrow_forward"}</span>
                </button>
              </form>

              <p className="member-register-footer">Đã là hội viên? <Link to="/login">Đăng nhập</Link></p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default RegisterMember;
