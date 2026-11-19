import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import gymApi from "../api/gymApi";
import "./MembershipPage.css";

const defaultPlans = [
  {
    plan_id: 1,
    plan_name: "Starter 1 Tháng",
    price: 499000,
    duration_days: 30,
    category: "Gói Cơ Bản",
    description: "Tặng 3 buổi PT định hướng, truy cập phòng gym 24/7",
  },
  {
    plan_id: 3,
    plan_name: "Pro Fitness 6 Tháng",
    price: 2394000,
    duration_days: 180,
    category: "Gói Phổ Biến",
    popular: true,
    description: "Tặng 7 buổi PT 1:1, lớp Yoga & HIIT, khu Sauna đá muối",
  },
  {
    plan_id: 4,
    plan_name: "VIP Elite 12 Tháng",
    price: 3840000,
    duration_days: 365,
    category: "Gói Cao Cấp",
    description: "Full quyền lợi VIP, dẫn bạn tập miễn phí, khăn & nước uống",
  },
];

const formatPrice = (price) =>
  `${new Intl.NumberFormat("vi-VN").format(Number(price) || 0)} đ`;

const getToday = () => {
  const today = new Date();
  const localDate = new Date(
    today.getTime() - today.getTimezoneOffset() * 60000
  );
  return localDate.toISOString().slice(0, 10);
};

const MembershipPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState(defaultPlans);
  const [selectedPlanId, setSelectedPlanId] = useState(
    Number(searchParams.get("plan")) || 3
  );
  const [phone, setPhone] = useState(user?.phone || "");
  const [startDate, setStartDate] = useState(getToday);
  const [paymentMethod, setPaymentMethod] = useState("BANK_TRANSFER");
  const [discountCode, setDiscountCode] = useState("");
  const [discountInfo, setDiscountInfo] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [checkoutResult, setCheckoutResult] = useState(null);
  const [agreed, setAgreed] = useState(true);

  useEffect(() => {
    if (user?.phone && !phone) setPhone(user.phone);
  }, [user, phone]);

  useEffect(() => {
    gymApi
      .getPlans({ size: 20 })
      .then((res) => {
        const items = res.data?.items || [];
        if (items.length > 0) {
          setPlans(
            items.map((p, i) => ({
              ...p,
              popular: i === 2 || p.duration_days === 180,
            }))
          );
          const paramPlan = Number(searchParams.get("plan"));
          if (paramPlan && items.some((p) => p.plan_id === paramPlan)) {
            setSelectedPlanId(paramPlan);
          } else {
            setSelectedPlanId(items[0].plan_id);
          }
        }
      })
      .catch(() => {});
  }, [searchParams]);

  const selectedPlan =
    plans.find((plan) => Number(plan.plan_id) === Number(selectedPlanId)) ||
    plans[0];
  const basePrice = Number(selectedPlan?.price || 0);
  const discountAmount = Number(discountInfo?.discount_amount || 0);
  const finalPrice = Math.max(0, basePrice - discountAmount);

  const handleApplyVoucher = async () => {
    if (!discountCode.trim()) return;
    setError("");
    try {
      const res = await gymApi.validateDiscount(
        discountCode.trim(),
        basePrice
      );
      setDiscountInfo(res.data);
    } catch (err) {
      setDiscountInfo(null);
      setError(
        err.response?.data?.message || "Mã giảm giá không hợp lệ hoặc đã hết hạn."
      );
    }
  };

  const handleCheckout = async (event) => {
    event.preventDefault();
    setError("");

    if (!user) {
      setError("Bạn cần đăng nhập tài khoản hội viên trước khi đăng ký gói tập.");
      return;
    }
    if (!agreed) {
      setError("Vui lòng đồng ý với điều khoản dịch vụ.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await gymApi.createSubscription({
        plan_id: selectedPlan.plan_id,
        payment_method: paymentMethod,
        discount_code: discountInfo ? discountInfo.code : discountCode.trim() || null,
        start_date: startDate,
      });
      setCheckoutResult(res.data);
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Đăng ký gói tập thất bại. Vui lòng thử lại."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="membership-page">
      <header className="membership-header">
        <div className="membership-nav">
          <Link className="membership-brand" to="/">
            <span className="material-symbols-outlined">fitness_center</span>
            Ducky Gym
          </Link>
          <nav aria-label="Điều hướng chính">
            <Link to="/">Trang chủ</Link>
            <a href="/#plans">Bảng giá</a>
            {user && <Link to="/member">Thẻ hội viên QR</Link>}
          </nav>
          <div className="membership-nav-actions">
            {user ? (
              <Link to="/member">Tài khoản ({user.full_name})</Link>
            ) : (
              <Link to="/login">Đăng nhập</Link>
            )}
            {!user && (
              <Link className="membership-register-link" to="/register">
                Đăng ký
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="membership-main">
        <div className="membership-intro">
          <div>
            <p className="membership-eyebrow">Ducky Gym · Hội viên</p>
            <h1>Đăng ký &amp; Gia hạn gói tập</h1>
            <p>
              Tự động nối tiếp ngày hết hạn nếu thẻ đang còn hạn và sinh mã QR
              thẻ hội viên điện tử ngay lập tức.
            </p>
          </div>
          <div className="membership-trust">
            <div>
              <span className="material-symbols-outlined">verified</span>
              <span>
                <b>Cộng dồn hạn thẻ</b>
                <small>Không mất ngày tập còn lại</small>
              </span>
            </div>
            <i />
            <div>
              <span className="material-symbols-outlined">qr_code_2</span>
              <span>
                <b>Sinh mã QR tức thì</b>
                <small>Check-in ngay tại cửa</small>
              </span>
            </div>
          </div>
        </div>

        <form className="membership-layout" onSubmit={handleCheckout}>
          <section
            className="membership-plan-side"
            aria-labelledby="membership-plan-title"
          >
            <div className="membership-section-label">
              <span>1</span>
              <h2 id="membership-plan-title">Chọn gói tập luyện</h2>
            </div>
            <div className="membership-plan-options">
              {plans.map((plan) => (
                <button
                  className={`membership-plan${
                    Number(selectedPlanId) === Number(plan.plan_id)
                      ? " is-selected"
                      : ""
                  }`}
                  key={plan.plan_id}
                  type="button"
                  aria-pressed={Number(selectedPlanId) === Number(plan.plan_id)}
                  onClick={() => {
                    setSelectedPlanId(plan.plan_id);
                    setDiscountInfo(null);
                  }}
                >
                  {plan.popular && (
                    <span className="membership-popular">
                      Phổ biến · Tiết kiệm
                    </span>
                  )}
                  <span className="membership-plan-badge">
                    {plan.category || "Gói Hội Viên"}
                  </span>
                  <b className="membership-plan-name">{plan.plan_name}</b>
                  <span className="membership-plan-price">
                    {formatPrice(plan.price)}
                  </span>
                  <span className="membership-plan-duration">
                    Thời hạn: {plan.duration_days} ngày
                  </span>
                  <span className="membership-plan-perk">
                    {plan.description || "Tập luyện không giới hạn"}
                  </span>
                </button>
              ))}
            </div>

            <section className="membership-summary">
              <div className="membership-summary-head">
                <div>
                  <span>Tóm tắt quyền lợi gói</span>
                  <h2>
                    {selectedPlan?.plan_name} ({selectedPlan?.duration_days}{" "}
                    ngày)
                  </h2>
                </div>
                <div className="membership-total">
                  <span>Thành tiền</span>
                  <b>{formatPrice(finalPrice)}</b>
                </div>
              </div>
              <div className="membership-perks">
                <div>
                  <span className="material-symbols-outlined">
                    sports_gymnastics
                  </span>
                  <p>
                    <b>Đặt lịch PT 1-1 trực tuyến</b>
                    <small>Chọn khung giờ tập cùng HLV trên lịch tuần</small>
                  </p>
                </div>
                <div>
                  <span className="material-symbols-outlined">monitoring</span>
                  <p>
                    <b>Theo dõi BMI &amp; Cân nặng</b>
                    <small>Biểu đồ tiến độ cơ thể theo thời gian</small>
                  </p>
                </div>
                <div>
                  <span className="material-symbols-outlined">groups</span>
                  <p>
                    <b>Đăng ký lớp tập nhóm</b>
                    <small>Yoga, Zumba, HIIT, Boxing hàng tuần</small>
                  </p>
                </div>
                <div>
                  <span className="material-symbols-outlined">fingerprint</span>
                  <p>
                    <b>Thẻ hội viên điện tử QR</b>
                    <small>Check-in/Check-out dưới 1 giây</small>
                  </p>
                </div>
              </div>
            </section>
          </section>

          <section
            className="membership-checkout"
            aria-labelledby="membership-info-title"
          >
            <div className="membership-section-label">
              <span>2</span>
              <h2 id="membership-info-title">Thông tin đăng ký</h2>
            </div>
            {user ? (
              <>
                <label className="membership-field" htmlFor="member-phone">
                  Số điện thoại hội viên
                  <span>
                    <span className="material-symbols-outlined">badge</span>
                    <input
                      id="member-phone"
                      type="tel"
                      value={phone}
                      onChange={(event) => setPhone(event.target.value)}
                      placeholder="Nhập số điện thoại"
                      required
                    />
                  </span>
                </label>

                <label
                  className="membership-field"
                  htmlFor="membership-start-date"
                >
                  Ngày bắt đầu dự kiến
                  <span>
                    <span className="material-symbols-outlined">
                      calendar_today
                    </span>
                    <input
                      id="membership-start-date"
                      type="date"
                      min={getToday()}
                      value={startDate}
                      onChange={(event) => setStartDate(event.target.value)}
                      required
                    />
                  </span>
                  <small>
                    Nếu bạn đang có thẻ còn hạn, gói mới sẽ tự động nối tiếp sau
                    ngày hết hạn hiện tại.
                  </small>
                </label>

                <div className="membership-field">
                  <label htmlFor="voucher-code">
                    Mã giảm giá / Voucher (Thử: WELCOME20, SUMMER100K)
                  </label>
                  <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
                    <input
                      id="voucher-code"
                      type="text"
                      value={discountCode}
                      onChange={(e) =>
                        setDiscountCode(e.target.value.toUpperCase())
                      }
                      placeholder="Nhập mã voucher..."
                      style={{
                        flex: 1,
                        padding: "10px 12px",
                        borderRadius: "8px",
                        border: "1px solid rgba(255,255,255,0.12)",
                        background: "#222a3d",
                        color: "#dae2fd",
                      }}
                    />
                    <button
                      type="button"
                      onClick={handleApplyVoucher}
                      style={{
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1px solid #f97316",
                        background: "rgba(249,115,22,0.15)",
                        color: "#ffb690",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Áp dụng
                    </button>
                  </div>
                  {discountInfo && (
                    <small style={{ color: "#4ade80", marginTop: "4px" }}>
                      ✓ {discountInfo.message} (Còn {formatPrice(finalPrice)})
                    </small>
                  )}
                </div>

                <fieldset className="membership-payment">
                  <legend>Phương thức thanh toán</legend>
                  <label
                    className={
                      paymentMethod === "BANK_TRANSFER" ? "is-selected" : ""
                    }
                  >
                    <input
                      type="radio"
                      name="payment-method"
                      value="BANK_TRANSFER"
                      checked={paymentMethod === "BANK_TRANSFER"}
                      onChange={() => setPaymentMethod("BANK_TRANSFER")}
                    />
                    <span>
                      <b>Chuyển khoản / QR</b>
                      <small>Kích hoạt thẻ ngay lập tức</small>
                    </span>
                    <span className="material-symbols-outlined">qr_code_2</span>
                  </label>
                  <label
                    className={paymentMethod === "CASH" ? "is-selected" : ""}
                  >
                    <input
                      type="radio"
                      name="payment-method"
                      value="CASH"
                      checked={paymentMethod === "CASH"}
                      onChange={() => setPaymentMethod("CASH")}
                    />
                    <span>
                      <b>Tiền mặt</b>
                      <small>Thanh toán tại quầy lễ tân</small>
                    </span>
                    <span className="material-symbols-outlined">payments</span>
                  </label>
                </fieldset>

                <label className="membership-terms">
                  <input
                    type="checkbox"
                    checked={agreed}
                    onChange={(event) => setAgreed(event.target.checked)}
                  />
                  <span>
                    Tôi đồng ý với điều khoản dịch vụ và chính sách hội viên.
                  </span>
                </label>

                {error && (
                  <p className="membership-error" role="alert">
                    {error}
                  </p>
                )}

                <button
                  className="membership-submit"
                  type="submit"
                  disabled={submitting}
                >
                  {submitting
                    ? "Đang xử lý đăng ký..."
                    : `Xác nhận đăng ký (${formatPrice(finalPrice)})`}{" "}
                  <span className="material-symbols-outlined">
                    arrow_forward
                  </span>
                </button>
              </>
            ) : (
              <div className="membership-account-prompt">
                <span className="material-symbols-outlined">person_add</span>
                <h3>Bạn cần tài khoản hội viên</h3>
                <p>
                  Hãy tạo tài khoản hoặc đăng nhập trước để hệ thống sinh thẻ
                  hội viên QR cho bạn.
                </p>
                <Link className="membership-submit" to="/register">
                  Tạo tài khoản{" "}
                  <span className="material-symbols-outlined">
                    arrow_forward
                  </span>
                </Link>
                <Link
                  className="membership-login-link"
                  to="/login"
                  state={{ from: "/membership" }}
                >
                  Đã có tài khoản? Đăng nhập
                </Link>
              </div>
            )}
          </section>
        </form>
      </main>

      {checkoutResult && (
        <div
          className="membership-modal-backdrop"
          role="presentation"
          onMouseDown={(event) =>
            event.target === event.currentTarget && setCheckoutResult(null)
          }
        >
          <section
            className="membership-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="checkout-title"
          >
            <span className="membership-modal-icon material-symbols-outlined">
              check_circle
            </span>
            <h2 id="checkout-title">{checkoutResult.message}</h2>
            <p>
              Gói: <b>{checkoutResult.plan_name}</b> · Mã thẻ:{" "}
              <b>{checkoutResult.card_code}</b>
            </p>
            <p>
              Hiệu lực: <b>{checkoutResult.start_date}</b> →{" "}
              <b>{checkoutResult.end_date}</b> ({checkoutResult.days_remaining}{" "}
              ngày)
            </p>
            <strong>{formatPrice(checkoutResult.final_amount)}</strong>
            <button
              type="button"
              onClick={() => navigate("/member")}
              style={{ marginTop: "12px" }}
            >
              Mở thẻ hội viên QR ngay
            </button>
          </section>
        </div>
      )}
    </div>
  );
};

export default MembershipPage;
