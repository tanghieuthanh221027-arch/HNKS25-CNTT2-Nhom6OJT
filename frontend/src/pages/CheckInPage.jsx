import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import gymApi from "../api/gymApi";
import "./CheckInPage.css";

const playBeep = (isSuccess = true) => {
  try {
    const AudioCtx = window.AudioContext || window.AudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = isSuccess ? "sine" : "sawtooth";
    osc.frequency.setValueAtTime(isSuccess ? 880 : 240, ctx.currentTime);
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + (isSuccess ? 0.18 : 0.35));
  } catch {
    // Ignore audio context restrictions
  }
};

const CheckInPage = () => {
  const { user } = useAuth();
  const videoRef = useRef(null);
  const scannedRef = useRef(false);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState(
    "Đưa mã QR hội viên vào giữa khung camera hoặc nhập mã thẻ bên dưới."
  );
  const [scanResult, setScanResult] = useState(null);
  const [manualCode, setManualCode] = useState(
    user?.member_code || "DG-000003"
  );
  const [cameraError, setCameraError] = useState("");

  const verifyQRCode = useCallback(async (rawCode) => {
    if (!rawCode || !rawCode.trim()) return;
    const code = rawCode.trim();
    scannedRef.current = true;
    setStatus("checking");
    setMessage(`Đã nhận mã ${code}. Đang kiểm tra thẻ hội viên...`);

    try {
      const res = await gymApi.scanQRCheckIn(code);
      const data = res.data;
      setScanResult(data);
      if (data.valid) {
        setStatus("success");
        setMessage(data.message);
        playBeep(true);
      } else {
        setStatus("error");
        setMessage(data.message);
        playBeep(false);
      }
    } catch (err) {
      setStatus("error");
      setMessage(
        err.response?.data?.message ||
          "Không thể kết nối máy chủ Check-in. Vui lòng thử lại."
      );
      playBeep(false);
    }
  }, []);

  useEffect(() => {
    let stream;
    let detector;
    let active = true;
    let frame;

    const scan = async () => {
      if (!active || !videoRef.current || !detector || scannedRef.current)
        return;
      try {
        const codes = await detector.detect(videoRef.current);
        if (codes.length && codes[0].rawValue) {
          verifyQRCode(codes[0].rawValue);
          return;
        }
      } catch {
        // Ignore transient frame read error
      }
      frame = window.requestAnimationFrame(scan);
    };

    const startCamera = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError(
          "Trình duyệt không có camera. Bạn có thể nhập mã thẻ thủ công ở ô bên dưới."
        );
        return;
      }
      try {
        if ("BarcodeDetector" in window) {
          detector = new window.BarcodeDetector({ formats: ["qr_code"] });
        }
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        if (!active) return;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        if (detector) {
          frame = window.requestAnimationFrame(scan);
        }
      } catch {
        setCameraError(
          "Camera chưa được cấp quyền hoặc thiết bị không có webcam. Hãy dùng ô nhập mã QR bên dưới để test."
        );
      }
    };

    startCamera();
    return () => {
      active = false;
      if (frame) window.cancelAnimationFrame(frame);
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [verifyQRCode]);

  const fullName =
    user?.full_name || user?.name || user?.username || "Kiosk Lễ Tân";

  const reset = () => {
    scannedRef.current = false;
    setStatus("idle");
    setScanResult(null);
    setMessage("Đưa mã QR hội viên vào giữa khung để bắt đầu.");
  };

  return (
    <main className="checkin-page">
      <header className="checkin-header">
        <Link to="/staff" className="checkin-brand">
          <span className="material-symbols-outlined">fitness_center</span>
          <span>
            <b>DUCKY GYM · POS LỄ TÂN</b>
            <small>KIOSK QUÉT QR CHECK-IN / CHECK-OUT</small>
          </span>
        </Link>
        <div className="checkin-user">
          <span className="material-symbols-outlined">badge</span>
          Lễ tân: {fullName}
        </div>
      </header>
      <div className="checkin-content">
        <Link className="checkin-back" to="/staff">
          <span className="material-symbols-outlined">arrow_back</span>
          Quay lại Màn POS Lễ tân
        </Link>
        <section className="checkin-layout">
          <div className="checkin-scanner-card">
            <div className="checkin-title">
              <span className="material-symbols-outlined">qr_code_scanner</span>
              <div>
                <h1>Kiosk Quét QR Check-in / Check-out</h1>
                <p>
                  Quét lần 1 để Check-in · Quét lần 2 để Check-out (Phản hồi
                  &lt; 1 giây)
                </p>
              </div>
            </div>

            <div className={`checkin-viewfinder is-${status}`}>
              <video
                ref={videoRef}
                muted
                playsInline
                aria-label="Camera quét mã QR"
              />
              <div className="checkin-corners" />
              <div className="checkin-laser" />
              {status !== "idle" && (
                <div className={`checkin-result is-${status}`}>
                  <span className="material-symbols-outlined">
                    {status === "success"
                      ? "check_circle"
                      : status === "error"
                      ? "error"
                      : "hourglass_top"}
                  </span>
                  <b>
                    {status === "success"
                      ? scanResult?.action === "CHECK_OUT"
                        ? "CHECK-OUT HỢP LỆ"
                        : "CHECK-IN HỢP LỆ"
                      : status === "error"
                      ? scanResult?.status === "EXPIRED_CARD"
                        ? "THẺ HẾT HẠN"
                        : "MÃ KHÔNG HỢP LỆ"
                      : "ĐANG XÁC MINH"}
                  </b>
                </div>
              )}
            </div>

            {cameraError && (
              <p className="checkin-camera-error" role="status">
                {cameraError}
              </p>
            )}

            <div
              className={`checkin-status is-${status}`}
              style={{
                padding: "16px",
                borderRadius: "12px",
                background:
                  status === "success"
                    ? "rgba(34, 197, 94, 0.2)"
                    : status === "error"
                    ? "rgba(239, 68, 68, 0.2)"
                    : undefined,
                border:
                  status === "success"
                    ? "2px solid #22c55e"
                    : status === "error"
                    ? "2px solid #ef4444"
                    : undefined,
              }}
            >
              <span className="material-symbols-outlined">
                {status === "success"
                  ? "task_alt"
                  : status === "error"
                  ? "warning"
                  : "sensors"}
              </span>
              <div>
                <p style={{ fontWeight: 700, fontSize: "15px" }}>{message}</p>
                {scanResult && (
                  <p style={{ fontSize: "12px", marginTop: "4px", opacity: 0.9 }}>
                    Mã thẻ: <b>{scanResult.member_code || manualCode}</b> · Thời
                    gian phản hồi: <b>{scanResult.response_time_ms} ms</b>
                  </p>
                )}
              </div>
            </div>

            {/* Nhập mã thủ công dự phòng (Task T067F99) */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                verifyQRCode(manualCode);
              }}
              style={{
                display: "flex",
                gap: "8px",
                marginTop: "14px",
                flexWrap: "wrap",
              }}
            >
              <input
                type="text"
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                placeholder="Nhập mã QR thủ công (VD: DG-000003)..."
                style={{
                  flex: 1,
                  minWidth: "180px",
                  padding: "11px 14px",
                  borderRadius: "10px",
                  border: "1px solid rgba(255,255,255,0.16)",
                  background: "#131b2e",
                  color: "#dae2fd",
                  fontSize: "14px",
                }}
              />
              <button
                type="submit"
                style={{
                  padding: "11px 18px",
                  borderRadius: "10px",
                  border: "none",
                  background: "#f97316",
                  color: "#351400",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Kiểm tra mã QR
              </button>
              {status !== "idle" && (
                <button
                  className="checkin-retry"
                  type="button"
                  onClick={reset}
                  style={{ margin: 0 }}
                >
                  Quét mã khác
                </button>
              )}
            </form>

            {/* Nút test nhanh 3 trường hợp theo yêu cầu Task T067E27 */}
            <div
              style={{
                display: "flex",
                gap: "8px",
                marginTop: "12px",
                flexWrap: "wrap",
              }}
            >
              <button
                type="button"
                onClick={() => {
                  setManualCode("DG-000006");
                  verifyQRCode("DG-000006");
                }}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  background: "rgba(34,197,94,0.15)",
                  color: "#86efac",
                  border: "1px solid rgba(34,197,94,0.35)",
                  cursor: "pointer",
                }}
              >
                Test 1: Thẻ Hợp lệ (Check-in/Check-out)
              </button>
              <button
                type="button"
                onClick={() => {
                  setManualCode("DG-000023");
                  verifyQRCode("DG-000023");
                }}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  background: "rgba(245,158,11,0.15)",
                  color: "#fde68a",
                  border: "1px solid rgba(245,158,11,0.35)",
                  cursor: "pointer",
                }}
              >
                Test 2: Thẻ Đã hết hạn
              </button>
              <button
                type="button"
                onClick={() => {
                  setManualCode("DG-999999");
                  verifyQRCode("DG-999999");
                }}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  background: "rgba(239,68,68,0.15)",
                  color: "#fca5a5",
                  border: "1px solid rgba(239,68,68,0.35)",
                  cursor: "pointer",
                }}
              >
                Test 3: Mã Không tồn tại
              </button>
            </div>
          </div>

          <aside className="checkin-help-card">
            <span className="material-symbols-outlined">lightbulb</span>
            <h2>Quy trình Check-in / Check-out</h2>
            <ol>
              <li>
                <b>Quét lần 1</b> khi vào phòng tập: Hệ thống kiểm tra hạn thẻ
                và ghi nhận giờ <b>Check-in</b>.
              </li>
              <li>
                <b>Quét lần 2</b> khi ra về: Hệ thống tự động ghi nhận giờ{" "}
                <b>Check-out</b>, tính thời lượng buổi tập và cộng chuỗi ngày
                tập (Streak).
              </li>
              <li>
                Trường hợp camera bị che hoặc mờ, có thể nhập trực tiếp mã thẻ{" "}
                <b>DG-XXXXXX</b> vào ô bên dưới.
              </li>
            </ol>
            <div className="checkin-help-note">
              <span className="material-symbols-outlined">support_agent</span>
              <span>
                Hỗ trợ 24/7 tại quầy lễ tân Ducky Gym (Hotline: 1900 6868).
              </span>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
};

export default CheckInPage;
