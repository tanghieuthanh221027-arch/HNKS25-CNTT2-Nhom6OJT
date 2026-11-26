import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import gymApi from "../api/gymApi";

const PTPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [schedules, setSchedules] = useState({ bookings: [] });
  const [notice, setNotice] = useState("");

  const loadBookings = useCallback(() => {
    gymApi
      .getPTSchedules()
      .then((res) => setSchedules(res.data || { bookings: [] }))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadBookings();
  }, [loadBookings]);

  const handleUpdateStatus = async (bookingId, status) => {
    try {
      let res;
      if (status === "CONFIRMED") res = await gymApi.confirmPTBooking(bookingId);
      else if (status === "COMPLETED") res = await gymApi.completePTBooking(bookingId);
      else if (status === "NO_SHOW") res = await gymApi.markPTBookingNoShow(bookingId);
      else res = await gymApi.cancelPTBooking(bookingId, "PT hủy ca trên cổng quản lý");
      setNotice(res.data.message);
      loadBookings();
    } catch (err) {
      setNotice(
        err.response?.data?.message || "Không thể cập nhật trạng thái ca tập."
      );
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0b1326",
        color: "#dae2fd",
        fontFamily: "Inter, Arial, sans-serif",
      }}
    >
      <header
        style={{
          height: "72px",
          background: "#131b2e",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          padding: "0 36px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Link
          to="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            color: "#dae2fd",
            textDecoration: "none",
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{
              background: "#f97316",
              color: "#351400",
              padding: "8px",
              borderRadius: "8px",
            }}
          >
            fitness_center
          </span>
          <div>
            <b style={{ display: "block" }}>DUCKY GYM · PT PORTAL</b>
            <small style={{ color: "#ffb690", fontSize: "11px" }}>
              QUẢN LÝ LỊCH DẠY 1-1
            </small>
          </div>
        </Link>

        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <span>
            HLV: <b>{user?.full_name || user?.email}</b>
          </span>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate("/login");
            }}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              border: "1px solid rgba(239,68,68,0.4)",
              background: "rgba(239,68,68,0.16)",
              color: "#fca5a5",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Đăng xuất
          </button>
        </div>
      </header>

      <main
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "32px 24px",
        }}
      >
        <div
          style={{
            background: "#171f33",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "16px",
            padding: "24px",
          }}
        >
          <h1 style={{ margin: "0 0 6px", fontSize: "22px" }}>
            Danh sách Lịch hẹn Tập 1-1 cùng Hội viên (Task T067DB0 &amp; T067EF6)
          </h1>
          <p style={{ margin: "0 0 18px", color: "#a6adc2", fontSize: "14px" }}>
            Xác nhận (CONFIRMED), Hoàn thành (COMPLETED), Đánh dấu vắng mặt (NO_SHOW - vẫn trừ buổi &amp; tính công PT) hoặc Hủy (CANCELLED). Tuyệt đối không xóa vật lý để bảo toàn dữ liệu kiểm toán.
          </p>

          {notice && (
            <div
              style={{
                padding: "12px 16px",
                borderRadius: "10px",
                background: "rgba(34,197,94,0.18)",
                border: "1px solid #22c55e",
                color: "#86efac",
                marginBottom: "16px",
                fontSize: "13px",
              }}
            >
              {notice}
            </div>
          )}

          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "13px",
            }}
          >
            <thead>
              <tr
                style={{
                  background: "#131b2e",
                  color: "#a6adc2",
                  textAlign: "left",
                }}
              >
                <th style={{ padding: "12px" }}>Mã lịch</th>
                <th style={{ padding: "12px" }}>Hội viên</th>
                <th style={{ padding: "12px" }}>Số điện thoại</th>
                <th style={{ padding: "12px" }}>Ngày tập</th>
                <th style={{ padding: "12px" }}>Khung giờ</th>
                <th style={{ padding: "12px" }}>Trạng thái</th>
                <th style={{ padding: "12px" }}>Thao tác của PT</th>
              </tr>
            </thead>
            <tbody>
              {(schedules.bookings || []).length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{ padding: "24px", textAlign: "center" }}
                  >
                    Chưa có lịch hẹn nào trong tuần này.
                  </td>
                </tr>
              ) : (
                schedules.bookings.map((b) => (
                  <tr
                    key={b.booking_id}
                    style={{
                      borderBottom: "1px solid rgba(255,255,255,0.07)",
                    }}
                  >
                    <td style={{ padding: "12px" }}>#{b.booking_id}</td>
                    <td style={{ padding: "12px", fontWeight: 700 }}>
                      {b.member_name}
                    </td>
                    <td style={{ padding: "12px" }}>{b.member_phone}</td>
                    <td style={{ padding: "12px" }}>{b.booking_date}</td>
                    <td style={{ padding: "12px" }}>
                      {b.start_time} - {b.end_time}
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span
                        style={{
                          padding: "4px 8px",
                          borderRadius: "6px",
                          fontSize: "11px",
                          fontWeight: 700,
                          background:
                            b.status === "CONFIRMED"
                              ? "rgba(34,197,94,0.2)"
                              : b.status === "COMPLETED"
                              ? "rgba(59,130,246,0.2)"
                              : b.status === "NO_SHOW"
                              ? "rgba(168,85,247,0.25)"
                              : b.status === "CANCELLED" || b.status === "EXPIRED"
                              ? "rgba(239,68,68,0.2)"
                              : "rgba(245,158,11,0.2)",
                        }}
                      >
                        {b.status}
                      </span>
                    </td>
                    <td
                      style={{
                        padding: "12px",
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "8px",
                      }}
                    >
                      {b.status === "PENDING" && (
                        <button
                          type="button"
                          onClick={() =>
                            handleUpdateStatus(b.booking_id, "CONFIRMED")
                          }
                          style={{
                            padding: "6px 10px",
                            borderRadius: "6px",
                            border: "none",
                            background: "#22c55e",
                            color: "#052e16",
                            fontWeight: 700,
                            cursor: "pointer",
                          }}
                        >
                          ✓ Xác nhận
                        </button>
                      )}
                      {b.status === "CONFIRMED" && (
                        <>
                          <button
                            type="button"
                            onClick={() =>
                              handleUpdateStatus(b.booking_id, "COMPLETED")
                            }
                            style={{
                              padding: "6px 10px",
                              borderRadius: "6px",
                              border: "none",
                              background: "#3b82f6",
                              color: "#fff",
                              fontWeight: 700,
                              cursor: "pointer",
                            }}
                          >
                            ★ Hoàn thành
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              handleUpdateStatus(b.booking_id, "NO_SHOW")
                            }
                            style={{
                              padding: "6px 10px",
                              borderRadius: "6px",
                              border: "1px solid rgba(168,85,247,0.45)",
                              background: "rgba(168,85,247,0.2)",
                              color: "#e9d5ff",
                              fontWeight: 700,
                              cursor: "pointer",
                            }}
                          >
                            ⚠ Vắng mặt (NO_SHOW)
                          </button>
                        </>
                      )}
                      {(b.status === "PENDING" || b.status === "CONFIRMED") && (
                        <button
                          type="button"
                          onClick={() =>
                            handleUpdateStatus(b.booking_id, "CANCELLED")
                          }
                          style={{
                            padding: "6px 10px",
                            borderRadius: "6px",
                            border: "1px solid rgba(239,68,68,0.4)",
                            background: "rgba(239,68,68,0.16)",
                            color: "#fca5a5",
                            fontWeight: 600,
                            cursor: "pointer",
                          }}
                        >
                          ✕ Hủy ca
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
};

export default PTPage;
