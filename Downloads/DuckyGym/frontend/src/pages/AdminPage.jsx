import React from "react";
import { useAuth } from "../context/AuthContext";

const AdminPage = () => {
  const { user, logout } = useAuth();

  return (
    <div>
      <h1>Trang quản trị ADMIN</h1>
      <p>Xin chào: {user?.name || user?.email}</p>
      <button onClick={logout}>Đăng xuất</button>
    </div>
  );
};

export default AdminPage;
