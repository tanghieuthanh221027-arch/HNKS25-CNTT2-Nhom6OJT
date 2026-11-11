import React from "react";
import { useAuth } from "../context/AuthContext";

const MemberPage = () => {
  const { user, logout } = useAuth();

  return (
    <div>
      <h1>Trang thành viên MEMBER</h1>
      <p>Xin chào: {user?.name || user?.email}</p>
      <button onClick={logout}>Đăng xuất</button>
    </div>
  );
};

export default MemberPage;
