import React from "react";
import { useAuth } from "../context/AuthContext";

const PTPage = () => {
  const { user, logout } = useAuth();

  return (
    <div>
      <h1>Trang huấn luyện viên PT</h1>
      <p>Xin chào: {user?.name || user?.email}</p>
      <button onClick={logout}>Đăng xuất</button>
    </div>
  );
};

export default PTPage;
