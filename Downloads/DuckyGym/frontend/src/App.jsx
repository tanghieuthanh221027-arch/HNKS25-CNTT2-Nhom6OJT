import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import AdminPage from "./pages/AdminPage";
import MemberPage from "./pages/MemberPage";
import PTPage from "./pages/PTPage";
import Unauthorized from "./pages/Unauthorized";
import HomePage from "./pages/HomePage";

import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      {/* Các trang công khai */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      {/* Các trang cần đăng nhập */}
      <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
        <Route path="/admin" element={<AdminPage />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["MEMBER"]} />}>
        <Route path="/member" element={<MemberPage />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["PT" , "TRAINER"]} />}>
        <Route path="/pt" element={<PTPage />} />
      </Route>

      <Route path="/" element={<HomePage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
