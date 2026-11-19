import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./CheckInPage.css";

const CheckInPage = () => {
  const { user } = useAuth();
  const videoRef = useRef(null);
  const scanAgainRef = useRef(null);
  const scannedRef = useRef(false);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("Đưa mã QR hội viên vào giữa khung để bắt đầu.");
  const [cameraError, setCameraError] = useState("");

  useEffect(() => {
    let stream;
    let detector;
    let active = true;
    let frame;

    const scan = async () => {
      if (!active || !videoRef.current || !detector || scannedRef.current) return;
      try {
        const codes = await detector.detect(videoRef.current);
        if (codes.length) {
          scannedRef.current = true;
          const value = codes[0].rawValue;
          setMessage(`Đã nhận mã ${value}. Đang xác minh...`);
          setStatus("checking");
          // Demo behavior adapted from the supplied kiosk page.
          window.setTimeout(() => {
            if (!active) return;
            if (value.endsWith("0") || value.endsWith("9")) {
              setStatus("error");
              setMessage("Mã check-in không hợp lệ hoặc gói tập đã hết hạn. Vui lòng liên hệ quầy lễ tân.");
            } else {
              setStatus("success");
              setMessage("Check-in thành công! Chúc bạn có buổi tập hiệu quả.");
            }
          }, 500);
          return;
        }
      } catch { /* Camera frames can be temporarily unreadable. */ }
      frame = window.requestAnimationFrame(scan);
    };
    scanAgainRef.current = scan;

    const startCamera = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError("Trình duyệt không hỗ trợ camera. Hãy thử trên Chrome hoặc Edge.");
        return;
      }
      if (!("BarcodeDetector" in window)) {
        setCameraError("Trình duyệt chưa hỗ trợ quét QR tự động. Hãy mở trang trên Chrome/Edge mới nhất.");
        return;
      }
      try {
        detector = new window.BarcodeDetector({ formats: ["qr_code"] });
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        if (!active) return;
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        frame = window.requestAnimationFrame(scan);
      } catch {
        setCameraError("Không thể mở camera. Hãy cấp quyền camera và truy cập trang qua HTTPS hoặc localhost.");
      }
    };

    startCamera();
    return () => {
      active = false;
      if (frame) window.cancelAnimationFrame(frame);
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const fullName = user?.full_name || user?.name || user?.username || "Hội viên";
  const reset = () => {
    scannedRef.current = false;
    setStatus("idle");
    setMessage("Đưa mã QR hội viên vào giữa khung để bắt đầu.");
    window.requestAnimationFrame(() => scanAgainRef.current?.());
  };

  return (
    <main className="checkin-page">
      <header className="checkin-header">
        <Link to="/member" className="checkin-brand"><span className="material-symbols-outlined">fitness_center</span><span><b>DUCKY GYM</b><small>ĐIỂM DANH HỘI VIÊN</small></span></Link>
        <div className="checkin-user"><span className="material-symbols-outlined">account_circle</span>{fullName}</div>
      </header>
      <div className="checkin-content">
        <Link className="checkin-back" to="/member"><span className="material-symbols-outlined">arrow_back</span>Quay lại trang hội viên</Link>
        <section className="checkin-layout">
          <div className="checkin-scanner-card">
            <div className="checkin-title"><span className="material-symbols-outlined">qr_code_scanner</span><div><h1>QR Check-in</h1><p>Đưa mã QR hội viên vào khung quét</p></div></div>
            <div className={`checkin-viewfinder is-${status}`}>
              <video ref={videoRef} muted playsInline aria-label="Camera quét mã QR" />
              <div className="checkin-corners" />
              <div className="checkin-laser" />
              {status !== "idle" && <div className={`checkin-result is-${status}`}><span className="material-symbols-outlined">{status === "success" ? "check_circle" : status === "error" ? "error" : "hourglass_top"}</span><b>{status === "success" ? "THÀNH CÔNG" : status === "error" ? "KHÔNG HỢP LỆ" : "ĐANG XÁC MINH"}</b></div>}
            </div>
            {cameraError && <p className="checkin-camera-error" role="status">{cameraError}</p>}
            <div className={`checkin-status is-${status}`}><span className="material-symbols-outlined">{status === "success" ? "task_alt" : status === "error" ? "warning" : "sensors"}</span><p>{message}</p></div>
            {status !== "idle" && <button className="checkin-retry" type="button" onClick={reset}>Quét mã khác</button>}
          </div>
          <aside className="checkin-help-card"><span className="material-symbols-outlined">lightbulb</span><h2>Hướng dẫn check-in</h2><ol><li>Mở thẻ hội viên điện tử trên ứng dụng.</li><li>Đặt mã QR vào giữa khung quét.</li><li>Giữ điện thoại ổn định cho đến khi xác minh xong.</li></ol><div className="checkin-help-note"><span className="material-symbols-outlined">support_agent</span><span>Cần hỗ trợ? Vui lòng liên hệ nhân viên tại quầy lễ tân.</span></div></aside>
        </section>
      </div>
    </main>
  );
};

export default CheckInPage;
