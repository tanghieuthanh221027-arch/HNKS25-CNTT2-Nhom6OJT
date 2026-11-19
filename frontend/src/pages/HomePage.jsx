import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import gymApi from "../api/gymApi";
import "./HomePage.css";

const defaultEquipment = [
  {
    icon: "directions_run",
    tag: "Mỹ & Ý",
    title: "Cardio Technogym",
    text: "Màn hình Live 4K tích hợp lộ trình chạy giả lập và cảm biến nhịp tim chuẩn y khoa.",
    image:
      "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?auto=format&fit=crop&w=900&q=80",
  },
  {
    icon: "fitness_center",
    tag: "Chuyên nghiệp",
    title: "Giàn tạ Rogue & Olympic",
    text: "Hệ khung thép chịu tải cao cùng đĩa tạ cao su chuẩn thi đấu thế giới.",
    image:
      "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=900&q=80",
  },
  {
    icon: "spa",
    tag: "Phục hồi",
    title: "Xông hơi đá muối Himalaya",
    text: "Thư giãn cơ thể và phục hồi năng lượng sau mỗi buổi tập luyện cường độ cao.",
    image:
      "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?auto=format&fit=crop&w=900&q=80",
  },
];

const defaultTrainers = [
  {
    name: "Trần Tuấn Anh",
    role: "Master Trainer · Thể hình & Tăng cơ",
    experience: "8+ năm kinh nghiệm",
    students: "350+ học viên",
    image:
      "https://images.unsplash.com/photo-1567013127542-490d757e51fc?auto=format&fit=crop&w=700&q=80",
  },
  {
    name: "Nguyễn Mai Linh",
    role: "Chuyên gia Dinh dưỡng, Yoga & Pilates",
    experience: "6+ năm kinh nghiệm",
    students: "400+ học viên",
    image:
      "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=700&q=80",
  },
  {
    name: "Lê Quốc Bảo",
    role: "Boxing, HIIT & Conditioning",
    experience: "7+ năm kinh nghiệm",
    students: "280+ học viên",
    image:
      "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=700&q=80",
  },
];

const fallbackPlans = [
  {
    plan_id: 1,
    plan_name: "Starter 1 Tháng",
    price: 499000,
    duration_days: 30,
    features: ["PT hướng dẫn 3 ngày", "Truy cập phòng gym 24/7", "Tủ đồ cá nhân miễn phí"],
  },
  {
    plan_id: 3,
    plan_name: "Pro Fitness 6 Tháng",
    price: 2394000,
    duration_days: 180,
    popular: true,
    features: ["PT hướng dẫn 7 ngày", "Lớp Yoga, Zumba & HIIT mỗi tuần", "Khu Sauna đá muối cao cấp"],
  },
  {
    plan_id: 4,
    plan_name: "VIP Elite 12 Tháng",
    price: 3840000,
    duration_days: 365,
    features: ["Toàn bộ quyền lợi Pro", "Dẫn theo bạn tập miễn phí cuối tuần", "Khăn tập & đồ uống mỗi buổi"],
  },
];

const formatCurrency = (val) =>
  new Intl.NumberFormat("vi-VN").format(Number(val) || 0);

const HomePage = () => {
  const location = useLocation();
  const { user } = useAuth();
  const [plans, setPlans] = useState(fallbackPlans);

  useEffect(() => {
    gymApi
      .getPlans({ size: 6 })
      .then((res) => {
        const items = res.data?.items || [];
        if (items.length > 0) {
          setPlans(
            items.map((p, idx) => ({
              ...p,
              popular: idx === 1 || p.duration_days === 180,
              features: p.description
                ? p.description.split(",").map((s) => s.trim())
                : ["Tập luyện không giới hạn", "Đo InBody định kỳ", "Huấn luyện viên hỗ trợ"],
            }))
          );
        }
      })
      .catch(() => {});
  }, []);

  const getDashboardLink = () => {
    if (!user) return "/login";
    const r = user.role?.toUpperCase();
    if (r === "ADMIN") return "/admin";
    if (r === "STAFF" || r === "CASHIER") return "/staff";
    if (r === "PT" || r === "TRAINER") return "/pt";
    return "/member";
  };

  return (
    <div className="home-page">
      {location.state?.message && (
        <div className="home-toast" role="status">
          {location.state.message}
        </div>
      )}
      <header className="home-header">
        <div className="home-nav">
          <Link
            className="home-brand"
            to="/"
            aria-label="Ducky Gym trang chủ"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          >
            <span className="material-symbols-outlined">fitness_center</span>{" "}
            Ducky Gym
          </Link>
          <nav className="home-nav-links" aria-label="Điều hướng chính">
            <a href="#equipment">Thiết bị</a>
            <a href="#trainers">Huấn luyện viên</a>
            <a href="#plans">Bảng giá</a>
          </nav>
          <div className="home-nav-actions">
            {user ? (
              <Link className="home-join" to={getDashboardLink()}>
                <span className="material-symbols-outlined">account_circle</span>{" "}
                {user.full_name || "Trang cá nhân"}
              </Link>
            ) : (
              <>
                <Link className="home-login" to="/login">
                  Đăng nhập
                </Link>
                <Link className="home-join" to="/register">
                  Đăng ký
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="home-hero">
          <div className="home-hero-image" />
          <div className="home-hero-content">
            <p className="home-eyebrow">
              <span /> Hệ thống Fitness tiên phong 2026
            </p>
            <h1>
              Kiến tạo vóc dáng <em>đỉnh cao</em>
            </h1>
            <p className="home-hero-text">
              Nâng tầm giới hạn bản thân cùng thiết bị chuẩn quốc tế, huấn luyện
              viên tận tâm và cộng đồng Ducky Gym đầy năng lượng.
            </p>
            <div className="home-hero-actions">
              <Link className="home-join" to="/membership">
                Đăng ký gói tập{" "}
                <span className="material-symbols-outlined">arrow_forward</span>
              </Link>
              <a className="home-outline-button" href="#equipment">
                Khám phá Ducky Gym
              </a>
            </div>
            <div className="home-stats">
              <div>
                <b>24/7</b>
                <span>Giờ tập linh hoạt</span>
              </div>
              <div>
                <b>40+</b>
                <span>Lớp tập mỗi tuần</span>
              </div>
              <div>
                <b>5.0</b>
                <span>Trải nghiệm hội viên</span>
              </div>
            </div>
          </div>
          <a className="home-scroll" href="#equipment">
            <span className="material-symbols-outlined">south</span> Khám phá
            thêm
          </a>
        </section>

        <section className="home-section home-equipment" id="equipment">
          <div className="home-section-heading">
            <div>
              <p className="home-eyebrow">Tiện nghi vượt trội</p>
              <h2>Hệ sinh thái thiết bị</h2>
            </div>
            <p>
              Không gian tập luyện hiện đại, được trang bị để bạn tập trung vào
              từng mục tiêu.
            </p>
          </div>
          <div className="home-equipment-grid">
            {defaultEquipment.map((item) => (
              <article className="home-equipment-card" key={item.title}>
                <img src={item.image} alt={item.title} loading="lazy" />
                <div className="home-equipment-info">
                  <span className="home-tag">{item.tag}</span>
                  <span className="material-symbols-outlined home-equipment-icon">
                    {item.icon}
                  </span>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="home-trainers" id="trainers">
          <div className="home-section">
            <div className="home-section-heading">
              <div>
                <p className="home-eyebrow">Đội ngũ tinh hoa</p>
                <h2>HLV Master đồng hành</h2>
              </div>
              <p>
                Huấn luyện viên có chứng chỉ quốc tế và kinh nghiệm thực chiến,
                sẵn sàng xây dựng lộ trình phù hợp cho bạn.
              </p>
            </div>
            <div className="home-trainer-grid">
              {defaultTrainers.map((trainer) => (
                <article className="home-trainer-card" key={trainer.name}>
                  <div className="home-trainer-photo">
                    <img
                      src={trainer.image}
                      alt={`Huấn luyện viên ${trainer.name}`}
                      loading="lazy"
                    />
                    <span className="material-symbols-outlined">verified</span>
                  </div>
                  <div className="home-trainer-info">
                    <h3>{trainer.name}</h3>
                    <p>{trainer.role}</p>
                    <div className="home-rating">
                      <span>★★★★★</span> 5.0
                    </div>
                    <div className="home-trainer-stats">
                      <span>{trainer.experience}</span>
                      <span>{trainer.students}</span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="home-section home-pricing" id="plans">
          <div className="home-section-heading">
            <div>
              <p className="home-eyebrow">Đầu tư xứng đáng</p>
              <h2>Bảng giá gói tập (Từ API)</h2>
            </div>
            <p>Minh bạch, linh hoạt và tích hợp thẻ hội viên QR tự động.</p>
          </div>
          <div className="home-plan-grid">
            {plans.map((plan) => (
              <article
                className={`home-plan-card${plan.popular ? " is-popular" : ""}`}
                key={plan.plan_id || plan.plan_name}
              >
                {plan.popular && (
                  <span className="home-popular">Được yêu thích</span>
                )}
                <h3>{plan.plan_name}</h3>
                <p className="home-plan-duration">
                  Thời hạn · {plan.duration_days} ngày
                </p>
                <p className="home-plan-price">
                  {formatCurrency(plan.price)}
                  <small> đ / gói</small>
                </p>
                <ul>
                  {(plan.features || []).map((feature) => (
                    <li key={feature}>
                      <span className="material-symbols-outlined">
                        check_circle
                      </span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  className={plan.popular ? "home-join" : "home-plan-button"}
                  to={`/membership?plan=${plan.plan_id}`}
                >
                  Đăng ký gói
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section className="home-contact">
          <div className="home-contact-inner">
            <div className="home-contact-icon material-symbols-outlined">
              call
            </div>
            <div>
              <h2>Cần tư vấn lịch tập phù hợp?</h2>
              <p>
                Hotline 1900 6868 hoạt động 24/7, chuyên viên tư vấn miễn phí.
              </p>
            </div>
            <a href="tel:19006868">
              Gọi tư vấn{" "}
              <span className="material-symbols-outlined">arrow_forward</span>
            </a>
          </div>
        </section>
      </main>

      <footer className="home-footer">
        <div className="home-footer-grid">
          <div>
            <Link className="home-brand" to="/">
              <span className="material-symbols-outlined">fitness_center</span>{" "}
              Ducky Gym
            </Link>
            <p>
              Hệ thống phòng tập thể hình chuẩn quốc tế, định hình phong cách
              sống kỷ luật và hiệu suất tối đa.
            </p>
          </div>
          <div>
            <h3>Địa điểm</h3>
            <p>123 Hà Đông, Hà Nội</p>
          </div>
          <div>
            <h3>Khám phá</h3>
            <a href="#equipment">Hệ sinh thái thiết bị</a>
            <a href="#trainers">Đội ngũ huấn luyện viên</a>
            <a href="#plans">Gói hội viên</a>
          </div>
          <div>
            <h3>Liên hệ</h3>
            <p>Hotline: 1900 6868 (24/7)</p>
            <p>Email: contact@duckygym.com.vn</p>
            <p>05:30 – 23:00 hàng ngày</p>
          </div>
        </div>
        <div className="home-footer-bottom">
          <span>© 2026 Ducky Gym &amp; Fitness</span>
          <Link to="/register">Điều khoản hội viên</Link>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
