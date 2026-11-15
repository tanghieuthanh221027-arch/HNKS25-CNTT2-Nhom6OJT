import axiosClient from "./axiosClient";

const subscriptionApi = {
  getMySubscription: () => axiosClient.get("/subscriptions/me"),
  registerSubscription: (data) => axiosClient.post("/subscriptions", data),
};

export default subscriptionApi;