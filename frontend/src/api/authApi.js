import axiosClient from "./axiosClient";

const authApi = {
  login(data) {
    return axiosClient.post("/auth/login", data);
  },

  register(data) {
    return axiosClient.post("/auth/register", data);
  },

  getMe() {
    return axiosClient.get("/users/me");
  },
};

export default authApi;