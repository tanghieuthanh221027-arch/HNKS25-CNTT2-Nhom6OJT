import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./HomePage.css";

const equipment = [
  {
    icon: "directions_run",
    tag: "Mỹ & Ý",
    title: "Cardio Technogym",
    text: "Màn hình Live 4K tích hợp lộ trình chạy giả lập và cảm biến nhịp tim chuẩn y khoa.",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuAIVnhqmBAhGVGw1u8GQ7vLArQNFiR8DSyEm-hXYOiNiiYj9NMKqaIIaG1K4kgerF0Sy8hczuxHIdOXHIMW79z_x2X9yKCynlDWLFXsgBis-K8Sf6MsIpBzcSPUtG87H-yTp13TamcVvbLujouWRFbN1JISHLbuSudXkxyI-ado4VICE3tQpoisePAmNoB48WHPBW1sHythqCILOY4LIDhgQoytYhXBghy3ocNElWA",
  },
  {
    icon: "fitness_center",
    tag: "Chuyên nghiệp",
    title: "Giàn tạ Rogue & Olympic",
    text: "Hệ khung thép chịu tải cao cùng đĩa tạ cao su chuẩn thi đấu thế giới.",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuB0KbP7UL3mdpGPRZGHCrEmV_yo2vIhGnarg4fILOejoIT50-kaS-JVy3k1dViAjLtitiEuaGXVSGS9sbPhOEfRQg2fDEX91kRibUlNTm6iEuUwaWshKc1gyg0D4CiPLTNSDngMuYfD3-m0OUvFv6Bdd7XCo9BNoRfR206eTF_rtA_4tDMr12TrqAXRUtyzssHpk5b5ld9k6_GdHcXI0HwL_5chdDynK7_JxdIPalY",
  },
  {
    icon: "spa",
    tag: "Phục hồi",
    title: "Xông hơi đá muối",
    text: "Thư giãn cơ thể và phục hồi năng lượng sau mỗi buổi tập luyện cường độ cao.",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuAXZYGpUjJvDom-lpjjiMLx9pH0IOE0UWbyFtlH-z1k3CCI7pRIpvkVP3qbkcu1SzKbdAe_h4rppWU200Slm19WNB2hcBqLO_FMt9rTs45LL5ZbYGZYwFe38PU214VCPxj1TOwrz_JK55vNiUeMHRBZXHHXV3aPOACL07sCiHmtgWdOfPX0x-TvtFko7SL385KWCkPH5-PUW-4it98x3lUt20FGB_eqcR7Y5DBuY5Q",
  },
];

const trainers = [
  { name: "Tuấn Anh", role: "Master Trainer · Thể hình cổ điển", experience: "8+ năm kinh nghiệm", students: "350+ học viên", image: "https://upgym.vn/wp-content/uploads/2023/09/UPGYM_RETOUCH5152.jpg.webp" },
  { name: "Mai Linh", role: "Chuyên gia dinh dưỡng & Yoga", experience: "6+ năm kinh nghiệm", students: "400+ học viên", image: "https://lh3.googleusercontent.com/aida-public/AB6AXuCvG-B4o46UjSP3Xfa6y21exnJMQ4GmpKkWljksQyOADTW1oYQBKU-H7MQ_-ny1lGwzYyvyo75aL4-Bzd-HwAXXDP71PxSui36aJAScaqLWkf48XaM2cNwIHGiYdzal9gCEasjC1W4YoVl8-_Dqdi1L8P2fiGg61_3BUaYLEiypXB472cKr_w_kMKnNl79sZ77V7rGJSPzYbga5T1h6EujgTrgEUTx_uA4lZSTH5mg" },
  { name: "Quốc Bảo", role: "Boxing & Conditioning", experience: "7+ năm kinh nghiệm", students: "280+ học viên", image: "https://lh3.googleusercontent.com/aida-public/AB6AXuBflDuovyeZVHsDbt2TS_MS4XIHREodqIDruYP6A5ZUh_WXevzlu0bStjf47xoYxVMQbolgKl680rmbVT3loseb4LUYJsK2Zx9Hbp4JSljJqtELafV9z9XHXJi1Vr6wSXcTyaRw8qmPEKKT26vaVGy8pRjrL__c-irYMXyDrBZRrsAg_i79dUQfnUpQJfKnOgayEk3JOr6h8W2RRnpoi5BxbOgPsxLzlDTTkNusbu0" },
];

const membershipPlans = [
  { id: "starter", name: "Starter", price: "499.000", duration: "1 tháng", features: ["PT hướng dẫn 3 ngày", "Truy cập phòng gym", "Tủ đồ cá nhân"] },
  { id: "pro", name: "Pro Fitness", price: "399.000", duration: "6 tháng", popular: true, features: ["PT hướng dẫn 7 ngày", "Lớp Yoga, HIIT mỗi tuần", "Khu Sauna cao cấp"] },
  { id: "vip", name: "VIP Elite", price: "320.000", duration: "12 tháng", features: ["Toàn bộ quyền lợi Pro", "Dẫn theo bạn tập miễn phí", "Khăn tập & đồ uống mỗi buổi"] },
];

const HomePage = () => {
  const location = useLocation();

  return (
    <div className="home-page">
      {location.state?.message && <div className="home-toast" role="status">{location.state.message}</div>}
    <header className="home-header">
      <div className="home-nav">
        <Link className="home-brand" to="/" aria-label="Ducky Gym trang chủ" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}><span className="material-symbols-outlined">fitness_center</span> Ducky Gym</Link>
        <nav className="home-nav-links" aria-label="Điều hướng chính">
          <a href="#equipment">Thiết bị</a><a href="#trainers">Huấn luyện viên</a><a href="#plans">Bảng giá</a>
        </nav>
        <div className="home-nav-actions"><Link className="home-login" to="/login">Đăng nhập</Link><Link className="home-join" to="/register">Đăng ký</Link></div>
      </div>
    </header>

    <main>
      <section className="home-hero">
        <div className="home-hero-image" />
        <div className="home-hero-content">
          <p className="home-eyebrow"><span /> Hệ thống Fitness tiên phong 2025</p>
          <h1>Kiến tạo vóc dáng <em>đỉnh cao</em></h1>
          <p className="home-hero-text">Nâng tầm giới hạn bản thân cùng thiết bị chuẩn quốc tế, huấn luyện viên tận tâm và cộng đồng Ducky Gym đầy năng lượng.</p>
          <div className="home-hero-actions"><Link className="home-join" to="/membership">Đăng ký gói tập <span className="material-symbols-outlined">arrow_forward</span></Link><a className="home-outline-button" href="#equipment">Khám phá Ducky Gym</a></div>
          <div className="home-stats"><div><b>24/7</b><span>Giờ tập linh hoạt</span></div><div><b>40+</b><span>Lớp tập mỗi tuần</span></div><div><b>5.0</b><span>Trải nghiệm hội viên</span></div></div>
        </div>
        <a className="home-scroll" href="#equipment"><span className="material-symbols-outlined">south</span> Khám phá thêm</a>
      </section>

      <section className="home-section home-equipment" id="equipment">
        <div className="home-section-heading"><div><p className="home-eyebrow">Tiện nghi vượt trội</p><h2>Hệ sinh thái thiết bị</h2></div><p>Không gian tập luyện hiện đại, được trang bị để bạn tập trung vào từng mục tiêu.</p></div>
        <div className="home-equipment-grid">
          {equipment.map((item) => <article className="home-equipment-card" key={item.title}>
            <img src={item.image} alt={item.title} loading="lazy" />
            <div className="home-equipment-info"><span className="home-tag">{item.tag}</span><span className="material-symbols-outlined home-equipment-icon">{item.icon}</span><h3>{item.title}</h3><p>{item.text}</p></div>
          </article>)}
        </div>
      </section>

      <section className="home-trainers" id="trainers">
        <div className="home-section">
          <div className="home-section-heading"><div><p className="home-eyebrow">Đội ngũ tinh hoa</p><h2>HLV Master đồng hành</h2></div><p>Huấn luyện viên có chứng chỉ quốc tế và kinh nghiệm thực chiến, sẵn sàng xây dựng lộ trình phù hợp cho bạn.</p></div>
          <div className="home-trainer-grid">
            {trainers.map((trainer) => <article className="home-trainer-card" key={trainer.name}>
              <div className="home-trainer-photo"><img src={trainer.image} alt={`Huấn luyện viên ${trainer.name}`} loading="lazy" /><span className="material-symbols-outlined">verified</span></div>
              <div className="home-trainer-info"><h3>{trainer.name}</h3><p>{trainer.role}</p><div className="home-rating"><span>★★★★★</span> 5.0</div><div className="home-trainer-stats"><span>{trainer.experience}</span><span>{trainer.students}</span></div></div>
            </article>)}
          </div>
        </div>
      </section>

      <section className="home-section home-pricing" id="plans">
        <div className="home-section-heading"><div><p className="home-eyebrow">Đầu tư xứng đáng</p><h2>Bảng giá gói tập</h2></div><p>Minh bạch, linh hoạt và không phát sinh phụ phí.</p></div>
        <div className="home-plan-grid">
          {membershipPlans.map((plan) => <article className={`home-plan-card${plan.popular ? " is-popular" : ""}`} key={plan.name}>
            {plan.popular && <span className="home-popular">Được yêu thích</span>}
            <h3>{plan.name}</h3><p className="home-plan-duration">Gói hội viên · {plan.duration}</p>
            <p className="home-plan-price">{plan.price}<small> đ / tháng</small></p>
            <ul>{plan.features.map((feature) => <li key={feature}><span className="material-symbols-outlined">check_circle</span>{feature}</li>)}</ul>
            <Link className={plan.popular ? "home-join" : "home-plan-button"} to={`/membership?plan=${plan.id}`}>Đăng ký gói</Link>
          </article>)}
        </div>
      </section>

      <section className="home-contact">
        <div className="home-contact-inner"><div className="home-contact-icon material-symbols-outlined">call</div><div><h2>Cần tư vấn lịch tập phù hợp?</h2><p>Hotline 1900 6868 hoạt động 24/7, chuyên viên tư vấn miễn phí.</p></div><a href="tel:19006868">Gọi tư vấn <span className="material-symbols-outlined">arrow_forward</span></a></div>
      </section>
    </main>

    <footer className="home-footer">
      <div className="home-footer-grid">
        <div><Link className="home-brand" to="/"><span className="material-symbols-outlined">fitness_center</span> Ducky Gym</Link><p>Hệ thống phòng tập thể hình chuẩn quốc tế, định hình phong cách sống kỷ luật và hiệu suất tối đa.</p></div>
        <div><h3>Địa điểm</h3><p>123 Hà Đông, Hà Nội</p></div>
        <div><h3>Khám phá</h3><a href="#equipment">Hệ sinh thái thiết bị</a><a href="#trainers">Đội ngũ huấn luyện viên</a><a href="#plans">Gói hội viên</a></div>
        <div><h3>Liên hệ</h3><p>Hotline: 1900 6868 (24/7)</p><p>Email: contact@duckygym.com.vn</p><p>05:30 – 23:00 hàng ngày</p></div>
      </div>
      <div className="home-footer-bottom"><span>© 2025 Ducky Gym &amp; Fitness</span><Link to="/register">Điều khoản hội viên</Link></div>
    </footer>
    </div>
  );
};

export default HomePage;

