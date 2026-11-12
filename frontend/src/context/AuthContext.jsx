import React, { createContext, useContext, useEffect, useState } from "react";
import authApi from "../api/authApi";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Kiểm tra token khi mở website
  useEffect(() => {
    const checkLogin = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await authApi.getMe();
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem("token");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkLogin();
  }, []);

  // Đăng nhập
  const login = async (data) => {
    // 1. Tự động chuyển đổi 'email' từ form thành 'username' để gửi cho Backend
    const loginPayload = {
      username: data.email || data.username,
      password: data.password
    };

    const response = await authApi.login(loginPayload);

    // 2. Lấy token từ object lồng nhau theo đúng schema LoginResponse của nhóm
    const token = response.data.token.access_token;

    localStorage.setItem("token", token);

    // Backend nhóm đã trả về sẵn thông tin user trong response.data.user
    const userResponse = response.data.user
      ? { data: response.data.user }
      : await authApi.getMe();

    setUser(userResponse.data);

    return userResponse.data;
  };

  // Đăng ký
  const register = async (data) => {
    return await authApi.register(data);
  };

  // Đăng xuất
  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
