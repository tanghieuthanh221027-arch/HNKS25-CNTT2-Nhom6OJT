import React from "react";
import { QRCodeSVG } from "qrcode.react";

/**
 * Component hiển thị mã QR chuẩn ISO/IEC 18004 (SVG) & hỗ trợ tải ảnh QR về máy (Task T067F69).
 * Import trực tiếp từ ESM nội bộ của frontend để tránh cache cũ của Vite.
 */
export const QRCodeDisplay = ({
  value = "DG-000001",
  size = 160,
  bgColor = "#ffffff",
  fgColor = "#0b1326",
  level = "H",
  includeMargin = false,
  qrBase64 = null,
}) => {
  if (qrBase64 && qrBase64.startsWith("data:image/png;base64,")) {
    return (
      <img
        src={qrBase64}
        alt={`QR ${value}`}
        width={size}
        height={size}
        style={{ display: "block", width: size, height: size, borderRadius: 6 }}
      />
    );
  }

  return (
    <QRCodeSVG
      value={value || "DG-000001"}
      size={size}
      bgColor={bgColor}
      fgColor={fgColor}
      level={level}
      includeMargin={includeMargin}
    />
  );
};

export const downloadQRCodeImage = (containerId, memberCode = "DG-000001", qrBase64 = null) => {
  if (qrBase64 && qrBase64.startsWith("data:image/")) {
    const a = document.createElement("a");
    a.href = qrBase64;
    a.download = `DuckyGym_QR_${memberCode}.png`;
    a.click();
    return;
  }

  const container = document.getElementById(containerId);
  const svgEl = container?.querySelector("svg");
  if (!svgEl) return;

  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svgEl);
  const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(svgBlob);

  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, 400, 400);
      ctx.drawImage(img, 24, 24, 352, 352);
      const pngUrl = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.href = pngUrl;
      link.download = `DuckyGym_QR_${memberCode}.png`;
      link.click();
    }
    URL.revokeObjectURL(url);
  };
  img.src = url;
};

export default QRCodeDisplay;
