import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import RegisterMember from "./pages/RegisterMember";
import AdminPage from "./pages/AdminPage";
import MemberPage from "./pages/MemberPage";
import MemberProfilePage from "./pages/MemberProfilePage";
import PTPage from "./pages/PTPage";
import Unauthorized from "./pages/Unauthorized";
import HomePage from "./pages/HomePage";
import MembershipPage from "./pages/MembershipPage";

import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      {/* Các trang công khai */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<RegisterMember />} />
      <Route path="/membership" element={<MembershipPage />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      {/* Các trang cần đăng nhập */}
      <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
        <Route path="/admin" element={<AdminPage />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["MEMBER"]} />}>
        <Route path="/member" element={<MemberPage />} />
        <Route path="/member/profile" element={<MemberProfilePage />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["PT"]} />}>
        <Route path="/pt" element={<PTPage />} />
      </Route>

      <Route path="/" element={<HomePage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
