import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

const DEMO_ACCOUNTS = [
  { label: "Admin", email: "admin@duckygym.vn", password: "Admin123" },
  { label: "Lễ tân POS", email: "staff@duckygym.vn", password: "Staff123" },
  { label: "Hội viên", email: "member@duckygym.vn", password: "Member123" },
  { label: "HLV (PT)", email: "pt@duckygym.vn", password: "Trainer123" },
];

const Login = () => {
  const { login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((currentForm) => ({ ...currentForm, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const user = await login(form);
      const role = user.role?.toUpperCase();
      const returnTo = location.state?.from;

      if (returnTo) {
        navigate(returnTo);
        return;
      }

      if (role === "ADMIN") navigate("/admin");
      else if (role === "STAFF" || role === "CASHIER") navigate("/staff");
      else if (role === "PT" || role === "TRAINER") navigate("/pt");
      else navigate("/member");
    } catch (requestError) {
      if (!requestError.response) {
        setError(
          "Không kết nối được tới máy chủ Backend (http://127.0.0.1:8000). Hãy kiểm tra cửa sổ terminal đang chạy uvicorn app.main:app --reload!"
        );
      } else {
        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Đăng nhập thất bại! Vui lòng kiểm tra lại tài khoản hoặc mật khẩu."
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoAccount = (acc) => {
    setForm({ email: acc.email, password: acc.password });
    setError("");
  };

  return (
    <div className="login-page">
      <header className="login-header">
        <Link className="login-brand" to="/" aria-label="Ducky Gym">
          <span className="login-brand-icon material-symbols-outlined">
            fitness_center
          </span>
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
              <span className="login-status">
                <i /> Ducky Gym Performance Club
              </span>
              <span className="login-access">
                <span className="material-symbols-outlined">bolt</span>24/7
                ACCESS
              </span>
            </div>
            <div className="login-hero-copy">
              <p className="login-eyebrow">Chào mừng trở lại</p>
              <h2>Kỷ luật là cầu nối giữa mục tiêu và thành tựu.</h2>
              <div className="login-highlights">
                <span>
                  <span className="material-symbols-outlined">award_star</span>{" "}
                  Cơ sở vật chất 5 sao
                </span>
                <span>
                  <span className="material-symbols-outlined">speed</span> Huấn
                  luyện cá nhân 1-1
                </span>
              </div>
            </div>
          </div>

          <div className="login-form-panel">
            <div className="login-form-wrap">
              <div className="login-title">
                <h1>Đăng nhập</h1>
                <p>Nhập thông tin tài khoản của bạn để tiếp tục</p>
              </div>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                  marginBottom: "14px",
                }}
              >
                {DEMO_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.label}
                    type="button"
                    onClick={() => fillDemoAccount(acc)}
                    style={{
                      padding: "5px 10px",
                      fontSize: "11px",
                      borderRadius: "6px",
                      border: "1px solid rgba(249, 115, 22, 0.35)",
                      background: "rgba(249, 115, 22, 0.1)",
                      color: "#ffb690",
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    Demo {acc.label}
                  </button>
                ))}
              </div>

              {location.state?.message && (
                <p className="login-success" role="status">
                  {location.state.message}
                </p>
              )}

              <form className="login-form" onSubmit={handleSubmit}>
                <div className="login-field">
                  <label htmlFor="login-email">Tài khoản (Email / Username)</label>
                  <div className="login-input-wrap">
                    <span className="material-symbols-outlined">
                      alternate_email
                    </span>
                    <input
                      id="login-email"
                      name="email"
                      type="text"
                      placeholder="Email hoặc tên đăng nhập"
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
                      aria-label={
                        showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"
                      }
                      onClick={() => setShowPassword((visible) => !visible)}
                    >
                      <span className="material-symbols-outlined">
                        {showPassword ? "visibility_off" : "visibility"}
                      </span>
                    </button>
                  </div>
                </div>

                <div className="login-options">
                  <label className="login-remember">
                    <input type="checkbox" defaultChecked /> Ghi nhớ đăng nhập
                  </label>
                  <button
                    className="login-forgot"
                    type="button"
                    onClick={() =>
                      setError(
                        "Vui lòng liên hệ quầy lễ tân Ducky Gym (1900 6868) để đặt lại mật khẩu."
                      )
                    }
                  >
                    Quên mật khẩu?
                  </button>
                </div>

                {error && (
                  <p className="login-error" role="alert">
                    {error}
                  </p>
                )}

                <button
                  className="login-submit"
                  type="submit"
                  disabled={submitting}
                >
                  {submitting ? "Đang xác thực..." : "Đăng nhập"}{" "}
                  <span className="material-symbols-outlined">
                    arrow_forward
                  </span>
                </button>
              </form>

              <p className="login-register">
                Chưa có tài khoản?{" "}
                <Link to="/register">
                  Đăng ký hội viên ngay{" "}
                  <span className="material-symbols-outlined">north_east</span>
                </Link>
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Login;
