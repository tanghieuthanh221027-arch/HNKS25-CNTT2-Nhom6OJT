import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((currentForm) => ({ ...currentForm, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      const user = await login(form);
      const role = user.role?.toUpperCase();

      if (role === "ADMIN") navigate("/admin");
      else if (role === "PT") navigate("/pt");
      else navigate("/member");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Đăng nhập thất bại!");
    }
  };

  return (
    <div className="login-page">
      <header className="login-header">
        <Link className="login-brand" to="/" aria-label="Ducky Gym">
          <span className="login-brand-icon material-symbols-outlined">fitness_center</span>
          <span>Ducky Gym</span>
        </Link>
        <Link className="login-back" to="/">
          <span className="material-symbols-outlined">arrow_back</span>
          Quay lại trang chủ
        </Link>
      </header>

      <main className="login-main">
        <section className="login-card">
          <div className="login-hero">
            <div className="login-hero-top">
              <span className="login-status"><i /> Ducky Gym Performance Club</span>
              <span className="login-access"><span className="material-symbols-outlined">bolt</span>24/7 ACCESS</span>
            </div>
            <div className="login-hero-copy">
              <p className="login-eyebrow">Chào mừng trở lại</p>
              <h2>Kỷ luật là cầu nối giữa mục tiêu và thành tựu.</h2>
              <div className="login-highlights">
                <span><span className="material-symbols-outlined">award_star</span> Cơ sở vật chất 5 sao</span>
                <span><span className="material-symbols-outlined">speed</span> Huấn luyện cá nhân</span>
              </div>
            </div>
          </div>

          <div className="login-form-panel">
            <div className="login-form-wrap">
              <div className="login-title">
                <h1>Đăng nhập</h1>
                <p>Nhập thông tin hội viên của bạn để tiếp tục tập luyện</p>
              </div>

              <form className="login-form" onSubmit={handleSubmit}>
                <div className="login-field">
                  <label htmlFor="login-email">Tài khoản</label>
                  <div className="login-input-wrap">
                    <span className="material-symbols-outlined">alternate_email</span>
                    <input
                      id="login-email"
                      name="email"
                      type="email"
                      placeholder="Email của bạn"
                      value={form.email}
                      onChange={handleChange}
                      autoComplete="username"
                      required
                    />
                  </div>
                </div>

                <div className="login-field">
                  <label htmlFor="login-password">Mật khẩu</label>
                  <div className="login-input-wrap">
                    <span className="material-symbols-outlined">lock</span>
                    <input
                      id="login-password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Nhập mật khẩu của bạn"
                      value={form.password}
                      onChange={handleChange}
                      autoComplete="current-password"
                      required
                    />
                    <button
                      className="login-show-password"
                      type="button"
                      aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                      onClick={() => setShowPassword((visible) => !visible)}
                    >
                      <span className="material-symbols-outlined">{showPassword ? "visibility_off" : "visibility"}</span>
                    </button>
                  </div>
                </div>

                <div className="login-options">
                  <label className="login-remember"><input type="checkbox" /> Ghi nhớ đăng nhập</label>
                  <button className="login-forgot" type="button" onClick={() => setError("Vui lòng liên hệ phòng gym để đặt lại mật khẩu.")}>Quên mật khẩu?</button>
                </div>

                {error && <p className="login-error" role="alert">{error}</p>}

                <button className="login-submit" type="submit">
                  Đăng nhập <span className="material-symbols-outlined">arrow_forward</span>
                </button>
              </form>

              <div className="login-divider"><span>Hoặc</span></div>
              <div className="login-social" aria-label="Đăng nhập mạng xã hội">
                <button type="button" disabled><b className="login-google">G</b> Google</button>
                <button type="button" disabled><span className="material-symbols-outlined">phone_iphone</span> Apple ID</button>
              </div>
              <p className="login-register">Chưa có tài khoản? <Link to="/register">Đăng ký hội viên ngay <span className="material-symbols-outlined">north_east</span></Link></p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Login;
