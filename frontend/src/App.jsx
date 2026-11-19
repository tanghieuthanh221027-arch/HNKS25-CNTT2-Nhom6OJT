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
import CheckInPage from "./pages/CheckInPage";
import PTBookingPage from "./pages/PTBookingPage";

import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      {/* Các trang công khai */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<RegisterMember />} />
      <Route path="/membership" element={<MembershipPage />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      {/* Trang Quản trị ADMIN & Màn POS Lễ tân (STAFF / CASHIER) - Độc quyền sử dụng Kiosk Quét QR */}
      <Route
        element={
          <ProtectedRoute allowedRoles={["ADMIN", "STAFF", "CASHIER"]} />
        }
      >
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/staff" element={<AdminPage />} />
        <Route path="/staff/check-in" element={<CheckInPage />} />
        <Route path="/kiosk" element={<CheckInPage />} />
      </Route>

      {/* Trang Hội viên (MEMBER) - Chỉ xem thẻ QR cá nhân để đưa cho Lễ tân quét */}
      <Route element={<ProtectedRoute allowedRoles={["MEMBER", "ADMIN", "STAFF"]} />}>
        <Route path="/member" element={<MemberPage />} />
        <Route path="/member/profile" element={<MemberProfilePage />} />
      </Route>

      {/* Trang Huấn luyện viên (PT / TRAINER) */}
      <Route
        element={
          <ProtectedRoute allowedRoles={["PT", "TRAINER", "ADMIN"]} />
        }
      >
        <Route path="/pt" element={<PTPage />} />
      </Route>

      <Route path="/" element={<HomePage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
