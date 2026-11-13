import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./MembershipPage.css";

const plans = [
  { id: "starter", name: "Starter", monthlyPrice: 499000, months: 1, highlight: "Linh hoạt", badge: "Trải nghiệm", ptGift: "Tặng 1 buổi PT đánh giá khởi đầu" },
  { id: "pro", name: "Pro Fitness", monthlyPrice: 399000, months: 6, highlight: "Tiết kiệm 20%", badge: "Tối ưu kết quả", popular: true, ptGift: "Tặng 3 buổi PT 1:1 riêng biệt" },
  { id: "vip", name: "VIP Elite", monthlyPrice: 320000, months: 12, highlight: "Tặng 5 buổi PT", badge: "Đẳng cấp tối đa", ptGift: "Tặng 5 buổi PT 1:1 riêng biệt" },
];

const formatPrice = (price) => `${new Intl.NumberFormat("vi-VN").format(price)} đ`;

const getToday = () => {
  const today = new Date();
  const localDate = new Date(today.getTime() - today.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 10);
};

const MembershipPage = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const initialPlan = plans.some((plan) => plan.id === searchParams.get("plan"))
    ? searchParams.get("plan")
    : "pro";
  const [selectedPlanId, setSelectedPlanId] = useState(initialPlan);
  const [phone, setPhone] = useState(user?.phone || "");
  const [startDate, setStartDate] = useState(getToday);
  const [paymentMethod, setPaymentMethod] = useState("qr");
  const [error, setError] = useState("");
  const [showCheckout, setShowCheckout] = useState(false);
  const [agreed, setAgreed] = useState(true);
  const selectedPlan = plans.find((plan) => plan.id === selectedPlanId) || plans[1];
  const totalPrice = selectedPlan.monthlyPrice * selectedPlan.months;

  const handleCheckout = (event) => {
    event.preventDefault();
    setError("");

    if (!user) {
      setError("Bạn cần có tài khoản hội viên trước khi đăng ký gói tập.");
      return;
    }
    if (user.role && user.role.toUpperCase() !== "MEMBER") {
      setError("Chức năng đăng ký gói tập dành cho hội viên.");
      return;
    }
    if (!phone.trim()) {
      setError("Vui lòng nhập số điện thoại hội viên.");
      return;
    }
    if (!agreed) {
      setError("Vui lòng đồng ý với điều khoản dịch vụ.");
      return;
    }

    setShowCheckout(true);
  };

  return (
    <div className="membership-page">
      <header className="membership-header">
        <div className="membership-nav">
          <Link className="membership-brand" to="/"><span className="material-symbols-outlined">fitness_center</span>Ducky Gym</Link>
          <nav aria-label="Điều hướng chính"><Link to="/">Trang chủ</Link><a href="/#plans">Gói tập</a><a href="/#trainers">Huấn luyện viên</a></nav>
          <div className="membership-nav-actions">
            {user ? <Link to="/member">Tài khoản</Link> : <Link to="/login">Đăng nhập</Link>}
            {!user && <Link className="membership-register-link" to="/register">Đăng ký</Link>}
          </div>
        </div>
      </header>

      <main className="membership-main">
        <div className="membership-intro">
          <div>
            <p className="membership-eyebrow">Ducky Gym · Hội viên</p>
            <h1>Đăng ký gói tập</h1>
            <p>Lựa chọn gói rèn luyện phù hợp và bắt đầu hành trình khỏe mạnh của bạn.</p>
          </div>
          <div className="membership-trust">
            <div><span className="material-symbols-outlined">verified</span><span><b>Cam kết 100%</b><small>Hỗ trợ hội viên tận tâm</small></span></div>
            <i />
            <div><span className="material-symbols-outlined">bolt</span><span><b>Kích hoạt nhanh</b><small>Hỗ trợ mỗi ngày</small></span></div>
          </div>
        </div>

        <form className="membership-layout" onSubmit={handleCheckout}>
          <section className="membership-plan-side" aria-labelledby="membership-plan-title">
            <div className="membership-section-label"><span>1</span><h2 id="membership-plan-title">Chọn chu kỳ tập luyện</h2></div>
            <div className="membership-plan-options">
              {plans.map((plan) => (
                <button
                  className={`membership-plan${selectedPlanId === plan.id ? " is-selected" : ""}`}
                  key={plan.id}
                  type="button"
                  aria-pressed={selectedPlanId === plan.id}
                  onClick={() => setSelectedPlanId(plan.id)}
                >
                  {plan.popular && <span className="membership-popular">Phổ biến · Tiết kiệm</span>}
                  <span className="membership-plan-badge">{plan.badge}</span>
                  <b className="membership-plan-name">{plan.name}</b>
                  <span className="membership-plan-price">{formatPrice(plan.monthlyPrice)}<small>/tháng</small></span>
                  <span className="membership-plan-duration">Thời hạn: {String(plan.months).padStart(2, "0")} tháng</span>
                  <span className="membership-plan-perk">{plan.highlight}</span>
                </button>
              ))}
            </div>

            <section className="membership-summary">
              <div className="membership-summary-head">
                <div><span>Tóm tắt quyền lợi gói</span><h2>{selectedPlan.name} ({selectedPlan.months} tháng)</h2></div>
                <div className="membership-total"><span>Tổng phí dự kiến</span><b>{formatPrice(totalPrice)}</b></div>
              </div>
              <div className="membership-perks">
                <div><span className="material-symbols-outlined">sports_gymnastics</span><p><b>{selectedPlan.ptGift}</b><small>Huấn luyện viên xây dựng giáo án cá nhân</small></p></div>
                <div><span className="material-symbols-outlined">monitoring</span><p><b>Đo InBody định kỳ</b><small>Theo dõi tiến độ và chỉ số cơ thể</small></p></div>
                <div><span className="material-symbols-outlined">hot_tub</span><p><b>Sauna và khu phục hồi</b><small>Thư giãn sau mỗi buổi tập</small></p></div>
                <div><span className="material-symbols-outlined">fingerprint</span><p><b>Digital Pass hội viên</b><small>Check-in nhanh tại phòng tập</small></p></div>
              </div>
            </section>

            <div className="membership-facility"><span className="material-symbols-outlined">location_on</span>Không gian tập luyện hiện đại tại Ducky Gym</div>
          </section>

          <section className="membership-checkout" aria-labelledby="membership-info-title">
            <div className="membership-section-label"><span>2</span><h2 id="membership-info-title">Thông tin đăng ký</h2></div>
            {user ? (
              <>
                <label className="membership-field" htmlFor="member-phone">Số điện thoại hội viên
                  <span><span className="material-symbols-outlined">badge</span><input id="member-phone" type="tel" inputMode="numeric" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Nhập số điện thoại" required /></span>
                </label>
                <label className="membership-field" htmlFor="membership-start-date">Ngày bắt đầu dự kiến
                  <span><span className="material-symbols-outlined">calendar_today</span><input id="membership-start-date" type="date" min={getToday()} value={startDate} onChange={(event) => setStartDate(event.target.value)} required /></span>
                  <small>Ngày kích hoạt có thể được điều chỉnh tại quầy.</small>
                </label>

                <fieldset className="membership-payment">
                  <legend>Phương thức thanh toán</legend>
                  <label className={paymentMethod === "qr" ? "is-selected" : ""}>
                    <input type="radio" name="payment-method" value="qr" checked={paymentMethod === "qr"} onChange={() => setPaymentMethod("qr")} />
                    <span><b>Quét mã QR</b><small>Thanh toán điện tử</small></span><span className="material-symbols-outlined">qr_code_2</span>
                  </label>
                  <label className={paymentMethod === "cash" ? "is-selected" : ""}>
                    <input type="radio" name="payment-method" value="cash" checked={paymentMethod === "cash"} onChange={() => setPaymentMethod("cash")} />
                    <span><b>Tiền mặt</b><small>Thanh toán tại quầy lễ tân</small></span><span className="material-symbols-outlined">payments</span>
                  </label>
                </fieldset>

                <label className="membership-terms"><input type="checkbox" checked={agreed} onChange={(event) => setAgreed(event.target.checked)} />
                  <span>Tôi đồng ý với <a href="#terms" onClick={(event) => event.preventDefault()}>điều khoản dịch vụ</a> và chính sách hội viên.</span>
                </label>
                {error && <p className="membership-error" role="alert">{error}</p>}
                <button className="membership-submit" type="submit">Tiếp tục đăng ký <span className="material-symbols-outlined">arrow_forward</span></button>
              </>
            ) : (
              <div className="membership-account-prompt">
                <span className="material-symbols-outlined">person_add</span>
                <h3>Bạn cần tài khoản hội viên</h3>
                <p>Hãy tạo tài khoản hoặc đăng nhập trước. Sau khi đăng ký tài khoản, bạn sẽ được đưa về trang chủ để chọn lại gói tập.</p>
                {error && <p className="membership-error" role="alert">{error}</p>}
                <Link className="membership-submit" to="/register">Tạo tài khoản <span className="material-symbols-outlined">arrow_forward</span></Link>
                <Link className="membership-login-link" to="/login" state={{ from: { pathname: "/membership", search: window.location.search } }}>Đã có tài khoản? Đăng nhập</Link>
              </div>
            )}
            <div className="membership-assurance"><span className="material-symbols-outlined">lock</span> Thông tin tài khoản của bạn được bảo vệ</div>
          </section>
        </form>
      </main>

      {showCheckout && (
        <div className="membership-modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setShowCheckout(false)}>
          <section className="membership-modal" role="dialog" aria-modal="true" aria-labelledby="checkout-title">
            <span className="membership-modal-icon material-symbols-outlined">{paymentMethod === "qr" ? "qr_code_2" : "payments"}</span>
            <h2 id="checkout-title">Xác nhận đăng ký gói</h2>
            <p>Gói <b>{selectedPlan.name} ({selectedPlan.months} tháng)</b></p>
            <strong>{formatPrice(totalPrice)}</strong>
            <div className="membership-demo-note">Giao dịch thanh toán chưa được kết nối với hệ thống. Chưa có khoản thanh toán hoặc gói hội viên nào được tạo.</div>
            <button type="button" onClick={() => setShowCheckout(false)}>Đóng</button>
          </section>
        </div>
      )}
    </div>
  );
};

export default MembershipPage;
