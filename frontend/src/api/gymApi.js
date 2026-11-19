import axiosClient from "./axiosClient";

const gymApi = {
  // Users & Profile & Body Metrics
  getMe: () => axiosClient.get("/users/me"),
  updateMe: (data) => axiosClient.put("/users/me", data),
  getBodyMetrics: () => axiosClient.get("/users/body-metrics"),
  addBodyMetric: (data) => axiosClient.post("/users/body-metrics", data),
  getTrainers: () => axiosClient.get("/users/trainers"),
  searchMembers: (keyword = "") =>
    axiosClient.get("/users/members", { params: { keyword } }),

  // Gym Plans
  getPlans: (params = {}) => axiosClient.get("/gym-plans", { params }),
  getPlanById: (id) => axiosClient.get(`/gym-plans/${id}`),
  createPlan: (data) => axiosClient.post("/gym-plans", data),
  updatePlan: (id, data) => axiosClient.put(`/gym-plans/${id}`, data),
  deletePlan: (id) => axiosClient.delete(`/gym-plans/${id}`),

  // Equipment & Maintenance
  getEquipment: (params = {}) => axiosClient.get("/equipment", { params }),
  getMaintenanceDue: (days = 7) =>
    axiosClient.get("/equipment/maintenance-due", { params: { days } }),
  createEquipment: (data) => axiosClient.post("/equipment", data),
  updateEquipment: (id, data) => axiosClient.put(`/equipment/${id}`, data),
  markEquipmentMaintained: (id) =>
    axiosClient.post(`/equipment/${id}/maintain`),
  deleteEquipment: (id) => axiosClient.delete(`/equipment/${id}`),

  // Subscriptions & QR Card
  createSubscription: (data) => axiosClient.post("/subscriptions", data),
  getMySubscription: () => axiosClient.get("/subscriptions/me"),
  getExpiringSubscriptions: (within_days = 7) =>
    axiosClient.get("/subscriptions/expiring-soon", { params: { within_days } }),
  sendExpiryReminders: (within_days = 3) =>
    axiosClient.post("/subscriptions/send-expiry-reminders", null, {
      params: { within_days },
    }),

  // QR Check-in / Check-out & History
  scanQRCheckIn: (qr_code) => axiosClient.post("/checkins/qr", { qr_code }),
  getCheckInHistory: (params = {}) =>
    axiosClient.get("/checkins/history", { params }),

  // PT 1-1 Schedules
  getPTSchedules: (params = {}) =>
    axiosClient.get("/pt-schedules", { params }),
  createPTBooking: (data) => axiosClient.post("/pt-schedules", data),
  updatePTBookingStatus: (bookingId, status) =>
    axiosClient.put(`/pt-schedules/${bookingId}/status`, { status }),

  // POS & Invoices
  lookupMemberByPhone: (phone) =>
    axiosClient.get("/pos/member-lookup", { params: { phone } }),
  posCheckout: (data) => axiosClient.post("/pos/checkout", data),
  getPosInvoices: (params = {}) =>
    axiosClient.get("/pos/invoices", { params }),

  // Discounts / Vouchers
  getDiscounts: () => axiosClient.get("/discounts"),
  validateDiscount: (code, order_amount) =>
    axiosClient.post("/discounts/validate", { code, order_amount }),
  createDiscount: (data) => axiosClient.post("/discounts", data),
  updateDiscount: (id, data) => axiosClient.put(`/discounts/${id}`, data),
  deleteDiscount: (id) => axiosClient.delete(`/discounts/${id}`),

  // Dashboard & CSV Export
  getDashboardSummary: (params = {}) =>
    axiosClient.get("/dashboard/summary", { params }),
  exportRevenueCSV: (params = {}) =>
    axiosClient.get("/dashboard/export-csv", {
      params,
      responseType: "blob",
    }),

  // Group Classes
  getGroupClasses: () => axiosClient.get("/group-classes"),
  createGroupClass: (data) => axiosClient.post("/group-classes", data),
  enrollGroupClass: (classId) =>
    axiosClient.post(`/group-classes/${classId}/enroll`),
  cancelGroupClass: (classId) =>
    axiosClient.delete(`/group-classes/${classId}/enroll`),
  getClassEnrollments: (classId) =>
    axiosClient.get(`/group-classes/${classId}/enrollments`),
  markClassAttendance: (classId, enrollmentId, status) =>
    axiosClient.put(
      `/group-classes/${classId}/attendance/${enrollmentId}`,
      { status }
    ),
};

export default gymApi;
