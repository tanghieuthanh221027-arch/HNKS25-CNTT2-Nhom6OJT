import axios from "axios";

export const resolveApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (typeof window !== "undefined") {
    const currentHost = window.location.hostname;
    const isLocalHost =
      currentHost === "localhost" || currentHost === "127.0.0.1";
    const envPointsToLocal =
      !envUrl ||
      envUrl.includes("localhost") ||
      envUrl.includes("127.0.0.1");

    // Khi truy cập từ điện thoại hoặc thiết bị khác qua IP mạng LAN (192.168.x.x, 172.20.x.x...)
    if (!isLocalHost && envPointsToLocal) {
      return `${window.location.protocol}//${currentHost}:8000`;
    }
  }
  return envUrl || "http://127.0.0.1:8000";
};

const axiosClient = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: {
    "Content-Type": "application/json",
  },
});

// Tự động lấy token và gắn vào Header
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export default axiosClient;
