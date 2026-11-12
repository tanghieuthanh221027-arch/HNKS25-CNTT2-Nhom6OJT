import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import userApi from "../api/userAPI";
import subscriptionApi from "../api/subscriptionAPI";
import "./MemberPage.css";

const MemberPage = () => {
  const { user, logout } = useAuth();

  const [profile, setProfile] = useState({
    username: "",
    full_name: "",
    email: "",
    phone: "",
    role: "",
    status: "",
  });
  const [profileMsg, setProfileMsg] = useState({ type: "", text: "" });
  const [savingProfile, setSavingProfile] = useState(false);

  const [subscription, setSubscription] = useState(null);
  const [planId, setPlanId] = useState(1);
  const [subMsg, setSubMsg] = useState({ type: "", text: "" });
  const [loadingSub, setLoadingSub] = useState(false);

  useEffect(() => {
    fetchProfile();
    fetchMySubscription();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await userApi.getMe();
      setProfile(res.data);
    } catch (err) {
      setProfileMsg({
        type: "error",
        text: err.response?.data?.message || "Không tải được hồ sơ cá nhân",
      });
    }
  };

  const fetchMySubscription = async () => {
    try {
      const res = await subscriptionApi.getMySubscription();
      setSubscription(res.data);
    } catch (err) {
      // Chưa có thẻ tập còn hạn thì để null
      setSubscription(null);
    }
  };

  // Xử lý cập nhật hồ sơ 
  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMsg({ type: "", text: "" });

    try {
      const res = await userApi.updateMe({
        full_name: profile.full_name,
        email: profile.email,
        phone: profile.phone,
      });
      setProfile(res.data);
      setProfileMsg({
        type: "success",
        text: "Cập nhật hồ sơ cá nhân thành công!",
      });
    } catch (err) {
      setProfileMsg({
        type: "error",
        text: err.response?.data?.message || "Lỗi khi cập nhật hồ sơ",
      });
    } finally {
      setSavingProfile(false);
    }
  };

  // Xử lý đăng ký / gia hạn gói tập 
  const handleRegisterSubscription = async (e) => {
    e.preventDefault();
    setLoadingSub(true);
    setSubMsg({ type: "", text: "" });

    try {
      const res = await subscriptionApi.registerSubscription({
        plan_id: Number(planId),
      });
      setSubscription(res.data);
      setSubMsg({
        type: "success",
        text:
          res.data.subscription_type === "RENEW"
            ? "Gia hạn nối tiếp gói tập thành công!"
            : "Đăng ký gói tập mới thành công!",
      });
    } catch (err) {
      setSubMsg({
        type: "error",
        text: err.response?.data?.message || "Không thể đăng ký gói tập",
      });
    } finally {
      setLoadingSub(false);
    }
  };

  return (
    <div className="member-dashboard">
      <header className="member-header">
        <div>
          <h1>DuckyGym - Cổng Hội Viên</h1>
          <p>
            Xin chào, <strong>{profile.full_name || user?.full_name || user?.email}</strong> (
            {profile.role || "MEMBER"})
          </p>
        </div>
        <button className="btn-logout" onClick={logout}>
          Đăng xuất
        </button>
      </header>

      <div className="member-grid">
        {/* CỘT 1: HỒ SƠ CÁ NHÂN */}
        <section className="member-card">
          <h2>Hồ sơ cá nhân (/users/me)</h2>
          {profileMsg.text && (
            <div className={`alert ${profileMsg.type}`}>{profileMsg.text}</div>
          )}

          <form onSubmit={handleUpdateProfile} className="member-form">
            <div className="form-group">
              <label>Tên đăng nhập</label>
              <input type="text" value={profile.username || ""} disabled />
            </div>

            <div className="form-group">
              <label>Họ và tên</label>
              <input
                type="text"
                value={profile.full_name || ""}
                onChange={(e) =>
                  setProfile({ ...profile, full_name: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={profile.email || ""}
                onChange={(e) =>
                  setProfile({ ...profile, email: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label>Số điện thoại</label>
              <input
                type="text"
                value={profile.phone || ""}
                onChange={(e) =>
                  setProfile({ ...profile, phone: e.target.value })
                }
                required
              />
            </div>

            <button type="submit" className="btn-primary" disabled={savingProfile}>
              {savingProfile ? "Đang lưu..." : "Lưu thay đổi"}
            </button>
          </form>
        </section>

        {/* CỘT 2: THẺ TẬP & MÃ QR  */}
        <section className="member-card">
          <h2>Thẻ Hội Viên & Mã QR (/subscriptions/me)</h2>
          {subMsg.text && (
            <div className={`alert ${subMsg.type}`}>{subMsg.text}</div>
          )}

          {subscription ? (
            <div className="subscription-box">
              <div className="sub-info">
                <p>
                  <span>Gói tập:</span>{" "}
                  <strong>{subscription.plan?.plan_name || `Gói #${subscription.plan_id}`}</strong>
                </p>
                <p>
                  <span>Loại đăng ký:</span>{" "}
                  <span className="badge">{subscription.subscription_type}</span>
                </p>
                <p>
                  <span>Trạng thái:</span>{" "}
                  <span className="badge active">{subscription.status}</span>
                </p>
                <p>
                  <span>Ngày bắt đầu:</span> <strong>{subscription.start_date}</strong>
                </p>
                <p>
                  <span>Ngày hết hạn:</span> <strong>{subscription.end_date}</strong>
                </p>
                <p>
                  <span>Số ngày còn lại:</span>{" "}
                  <strong>{subscription.days_remaining} ngày</strong>
                </p>
                <p>
                  <span>Mã thẻ cố định:</span>{" "}
                  <code className="card-code">{subscription.card_code}</code>
                </p>
              </div>

              {subscription.qr_code && (
                <div className="qr-container">
                  <img
                    src={`data:image/png;base64,${subscription.qr_code}`}
                    alt="Mã QR Thẻ Tập"
                    className="qr-image"
                  />
                  <span>Quét mã QR để Check-in</span>
                </div>
              )}
            </div>
          ) : (
            <p className="empty-sub">
              Bạn chưa có thẻ tập nào đang hoạt động. Hãy đăng ký gói tập bên dưới!
            </p>
          )}

          <hr className="divider" />

          <h3>{subscription ? "Gia hạn nối tiếp gói tập" : "Đăng ký gói tập mới"}</h3>
          <form onSubmit={handleRegisterSubscription} className="sub-form">
            <div className="form-group">
              <label>Nhập ID Gói tập (plan_id trong bảng membership_plans)</label>
              <input
                type="number"
                min="1"
                value={planId}
                onChange={(e) => setPlanId(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-success" disabled={loadingSub}>
              {loadingSub
                ? "Đang xử lý..."
                : subscription
                ? "Gia hạn nối tiếp (+ cộng dồn ngày)"
                : "Đăng ký gói tập & Sinh QR"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
};

export default MemberPage;