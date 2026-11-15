import axiosClient from "./axiosClient";

const userApi = {
  getMe: () => axiosClient.get("/users/me"),
  updateMe: (data) => axiosClient.put("/users/me", data),
};

export default userApi;