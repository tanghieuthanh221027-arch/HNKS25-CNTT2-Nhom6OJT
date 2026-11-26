# KẾ HOẠCH KIỂM THỬ & BỘ TEST CASE TOÀN HỆ THỐNG — DUCKY GYM (11 PHÂN HỆ)

## 1. Tổng quan Kế hoạch Kiểm thử (System-Wide Test Plan)

| Hạng mục | Nội dung chi tiết |
|---|---|
| **Tên dự án** | **DuckyGym** — Hệ thống Quản lý Phòng Gym và Hội viên (Nhóm 6 - HN-KS25-CNTT2) |
| **Phiên bản kiểm thử** | v1.3.0 — Full System QA, 12 Red-Note Architectural Upgrades & Admin Test Lab (`/pages/test-lab`) |
| **Ngày thực hiện** | 25/11/2026 |
| **Mục tiêu kiểm thử** | Kiểm thử toàn diện **11 phân hệ Backend API + 10 màn hình Frontend SPA**, bao gồm: chuẩn hóa CSDL 3NF (`members`), ràng buộc khóa ngoại `ON DELETE RESTRICT`, quản lý hạn mức buổi PT (`total_sessions` / `sessions_remaining`), quy tắc nghiệp vụ `BR03`, `BR06`, `BR13–BR17`, khóa bi quan `SELECT ... FOR UPDATE` chống Race Condition, ca trực xuyên đêm, phân quyền RBAC 4 vai trò và cô lập tuyệt đối màn hình `/pages/test-lab` chỉ cho `ADMIN`. |
| **Công cụ kiểm thử** | 1. **Màn hình Chạy thử & Test Lab độc lập (Độc quyền Admin):** `/pages/test-lab` (**41 E2E Suites — 100% PASS** + 20+ API Presets)<br/>2. **Automated Backend Test Suite:** `pytest backend/tests/test_full_system.py` (**39 hàm kiểm thử — 100% PASS** trên MySQL 8.0) |
| **Môi trường kiểm thử** | - **OS:** Windows 64-bit · **Python:** 3.15 (`FastAPI 0.162.0`, `SQLAlchemy 2.1.6`, `pytest 9.2.0`)<br/>- **Frontend:** Node.js v24.21 · `React 18.3.1` · `Vite 6`<br/>- **Database:** MySQL 8.0 (`duckygym`) |
| **Phạm vi bao phủ** | **100% 11 API Routers (42 Endpoints) & 10 Màn hình UI** — Tổng cộng **93 Test Cases chi tiết** |

---

## 2. Danh sách 93 Test Cases Toàn Hệ Thống

### Phân hệ 01 — System, Health & OpenAPI (`TC-SYS-01` – `TC-SYS-02`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-SYS-01** | Kiểm tra Health Check & kết nối MySQL | `GUEST` | `GET /health` | `HTTP 200 OK`, `success=true`, `database="MySQL: connected"` | **PASS** |
| **TC-SYS-02** | Kiểm tra lược đồ Swagger OpenAPI 3.1 | `GUEST` | `GET /openapi.json` | `HTTP 200 OK`, xuất bản đầy đủ tất cả 11 nhóm router | **PASS** |

---

### Phân hệ 02 — Xác thực JWT & Phân quyền RBAC 4 Vai trò (`TC-AUTH-01` – `TC-AUTH-12`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-AUTH-01** | Đăng ký hội viên mới hợp lệ & tự sinh thẻ QR | `GUEST` | `POST /auth/register` (`name`, `email`, `phone`, `password >= 8`) | `HTTP 201 Created`, tự tạo `User(MEMBER)` + `Member` + `MemberCard` (`DG-XXXXXX` + SVG Base64) | **PASS** |
| **TC-AUTH-02** | Đăng ký trùng địa chỉ Email đã tồn tại (BR03) | `GUEST` | `POST /auth/register` (`email="member@duckygym.vn"`) | `HTTP 409 Conflict`, `"Email đã tồn tại trong hệ thống."` | **PASS** |
| **TC-AUTH-03** | Đăng ký trùng Số điện thoại đã tồn tại (BR03) | `GUEST` | `POST /auth/register` (`phone="0901000001"`) | `HTTP 409 Conflict`, `"Số điện thoại đã tồn tại trong hệ thống."` | **PASS** |
| **TC-AUTH-04** | Chặn đăng ký SĐT sai định dạng VN (Regression BUG-06) | `GUEST` | `POST /auth/register` (`phone="abcdefghij"`) | `HTTP 422 Unprocessable Entity`, `error_code="VALIDATION_ERROR"` | **PASS** |
| **TC-AUTH-05** | Chặn đăng ký mật khẩu ngắn hơn 8 ký tự | `GUEST` | `POST /auth/register` (`password="12345"`) | `HTTP 422 Unprocessable Entity` (FE & BE cùng chặn) | **PASS** |
| **TC-AUTH-06** | Đăng nhập vai trò Quản trị viên (`ADMIN`) | `ADMIN` | `POST /auth/login` (`admin@duckygym.vn` / `Admin123`) | `HTTP 200 OK`, trả về JWT Bearer Token, `role="ADMIN"`, điều hướng `/admin` | **PASS** |
| **TC-AUTH-07** | Đăng nhập vai trò Lễ tân POS (`STAFF`) | `STAFF` | `POST /auth/login` (`staff@duckygym.vn` / `Staff123`) | `HTTP 200 OK`, trả về JWT Bearer Token, `role="STAFF"`, điều hướng `/staff` | **PASS** |
| **TC-AUTH-08** | Đăng nhập vai trò Hội viên (`MEMBER`) | `MEMBER` | `POST /auth/login` (`member@duckygym.vn` / `Member123`) | `HTTP 200 OK`, trả về JWT Bearer Token, `member_code`, `badges`, điều hướng `/member` | **PASS** |
| **TC-AUTH-09** | Đăng nhập vai trò Huấn luyện viên (`TRAINER`) | `TRAINER` | `POST /auth/login` (`pt@duckygym.vn` / `Trainer123`) | `HTTP 200 OK`, trả về JWT Bearer Token, `role="TRAINER"`, điều hướng `/pt` | **PASS** |
| **TC-AUTH-10** | Đăng nhập linh hoạt bằng `username` hoặc `phone` | `MEMBER` | `POST /auth/login` (`hoivien` hoặc `0901000001`) | `HTTP 200 OK`, xác thực đúng cùng `user_id` của hội viên | **PASS** |
| **TC-AUTH-11** | Đăng nhập sai mật khẩu hoặc tài khoản không tồn tại | `GUEST` | `POST /auth/login` (`WrongPassword1`) | `HTTP 401 Unauthorized`, thông báo lỗi rõ ràng không lộ thông tin nhạy cảm | **PASS** |
| **TC-AUTH-12** | Kiểm tra chặn thiếu Token (`401`), Token giả mạo (`401`) & sai quyền RBAC (`403`) | Đa vai trò | `GET /users/me` (không token), `MEMBER -> POST /checkins/qr`, `STAFF -> GET /dashboard/export-csv` | Trả về đúng `401 Unauthorized` và `403 Forbidden`; trên UI chuyển hướng `/login` hoặc `/unauthorized` | **PASS** |

---

### Phân hệ 03 — Hồ sơ Người dùng, Đổi mật khẩu & Theo dõi BMI (`TC-USER-01` – `TC-USER-08`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-USER-01** | Xem hồ sơ cá nhân, thẻ QR, Streak & 3 mốc Huy hiệu | `MEMBER` | `GET /users/me` | `HTTP 200 OK`, đầy đủ `member_code`, `qr_base64`, `streak_days`, 3 phần tử `badges` | **PASS** |
| **TC-USER-02** | Cập nhật Chiều cao `175cm`, Cân nặng `70kg` -> Tự tính BMI | `MEMBER` | `PUT /users/me` (`height_cm=175`, `weight_kg=70`) | `HTTP 200 OK`, tự tính `bmi = 22.9` và tự động lưu thêm bản ghi `BodyMetric` | **PASS** |
| **TC-USER-03** | Chặn cập nhật trùng Email hoặc SĐT của tài khoản khác | `MEMBER` | `PUT /users/me` (`email="admin@duckygym.vn"` / `phone="0900000000"`) | `HTTP 409 Conflict` (Quy tắc BR03) | **PASS** |
| **TC-USER-04** | Chặn đổi mật khẩu khi nhập sai mật khẩu hiện tại | `MEMBER` | `PUT /users/me` (`current_password="Sai"`, `new_password="NewPassword123"`) | `HTTP 401 Unauthorized`, `"Mật khẩu hiện tại không chính xác."` | **PASS** |
| **TC-USER-05** | Đổi mật khẩu thành công & đăng nhập lại bằng mật khẩu mới | `MEMBER` | `PUT /users/me` -> `POST /auth/login` | `HTTP 200 OK`, mật khẩu mới băm `bcrypt` và đăng nhập thành công | **PASS** |
| **TC-USER-06** | Ghi nhận chỉ số InBody định kỳ & Xem chuỗi lịch sử BMI | `MEMBER` | `POST /users/body-metrics` & `GET /users/body-metrics` | `HTTP 201 Created` (`bmi` tính chuẩn) & `HTTP 200 OK` sắp xếp tăng dần theo ngày đo | **PASS** |
| **TC-USER-07** | Xem danh sách Huấn luyện viên (PT) đang hoạt động | `GUEST` | `GET /users/trainers` | `HTTP 200 OK`, trả về `>= 3` Master Trainer có `status="ACTIVE"` | **PASS** |
| **TC-USER-08** | Tìm kiếm hội viên theo SĐT/Tên/Mã thẻ & Phân quyền | `STAFF` / `MEMBER` | `GET /users/members?keyword=0901000001` | `STAFF` nhận `200 OK` kèm gói tập hiện tại; `MEMBER` bị chặn `403 Forbidden` | **PASS** |

---

### Phân hệ 04 — Quản lý Gói tập (Gym Plans CRUD) (`TC-PLAN-01` – `TC-PLAN-07`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-PLAN-01** | Xem danh sách gói tập đang mở bán có phân trang | `GUEST` | `GET /gym-plans?page=1&size=20` | `HTTP 200 OK`, chỉ trả về các gói `status="ACTIVE"` | **PASS** |
| **TC-PLAN-02** | Lọc gói tập theo khoảng giá `min_price` – `max_price` | `GUEST` | `GET /gym-plans?min_price=400000&max_price=1500000` | `HTTP 200 OK`, mọi gói trả về thỏa mãn `400.000 <= price <= 1.500.000` | **PASS** |
| **TC-PLAN-03** | Xem chi tiết gói tập hợp lệ & gói không tồn tại | `GUEST` | `GET /gym-plans/1` & `GET /gym-plans/999999` | Gói #1 trả `200 OK`; gói #999999 trả `404 Not Found` | **PASS** |
| **TC-PLAN-04** | Phân quyền tạo gói tập mới (Chỉ `ADMIN` được phép) | `ADMIN` / `STAFF` | `POST /gym-plans` | `ADMIN` tạo thành công (`201 Created`); `STAFF` hoặc `MEMBER` bị chặn `403 Forbidden` | **PASS** |
| **TC-PLAN-05** | Chặn tạo gói tập trùng tên (`409`) hoặc giá `<= 0` (`422`) | `ADMIN` | `POST /gym-plans` (`plan_name="Starter 1 Tháng"` hoặc `price=0`) | Trùng tên trả `409 Conflict`; giá bằng 0/âm trả `422 Validation Error` | **PASS** |
| **TC-PLAN-06** | Cập nhật thông tin gói tập & chặn body rỗng `{}` | `ADMIN` | `PUT /gym-plans/{id}` | Cập nhật giá thành công (`200 OK`); truyền `{}` trả `422 Validation Error` | **PASS** |
| **TC-PLAN-07** | Ngừng kinh doanh an toàn (`DISCONTINUED` - Soft Delete) | `ADMIN` | `DELETE /gym-plans/{id}` | `HTTP 200 OK`, chuyển `status="DISCONTINUED"`, ẩn khỏi trang khách nhưng giữ nguyên lịch sử hóa đơn | **PASS** |

---

### Phân hệ 05 — Quản lý Thiết bị & Bảo trì định kỳ (`TC-EQ-01` – `TC-EQ-07`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-EQ-01** | Danh sách thiết bị & Lọc theo khu vực (`zone`), trạng thái | `GUEST` | `GET /equipment?zone=Cardio&status=HOAT_DONG` | `HTTP 200 OK`, trả về đúng thiết bị khu Cardio đang hoạt động | **PASS** |
| **TC-EQ-02** | Cảnh báo thiết bị sắp/quá hạn bảo trì trong 7 ngày | `STAFF` | `GET /equipment/maintenance-due?days=7` | `HTTP 200 OK`, liệt kê thiết bị có `next_maintenance_date <= today + 7` | **PASS** |
| **TC-EQ-03** | Admin thêm thiết bị mới & Chặn trùng tên thiết bị | `ADMIN` / `STAFF` | `POST /equipment` | `ADMIN` tạo thành công (`201`); tên trùng trả `409`; `STAFF` tạo bị chặn `403` | **PASS** |
| **TC-EQ-04** | Chặn trạng thái thiết bị ngoài danh mục cho phép | `ADMIN` | `POST /equipment` (`status="UNKNOWN"`) | `HTTP 422 BusinessRuleException` (chỉ nhận `HOAT_DONG`, `BAO_TRI`, `HONG`) | **PASS** |
| **TC-EQ-05** | Admin cập nhật tình trạng thiết bị sang `BAO_TRI` | `ADMIN` | `PUT /equipment/{id}` (`status="BAO_TRI"`) | `HTTP 200 OK`, cập nhật trạng thái & ghi chú bảo trì | **PASS** |
| **TC-EQ-06** | Lễ tân/Admin xác nhận hoàn thành bảo trì hôm nay | `STAFF` | `POST /equipment/{id}/maintain` | `HTTP 200 OK`, tự động chuyển về `HOAT_DONG` và cộng `next_maintenance_date = today + interval` | **PASS** |
| **TC-EQ-07** | Admin xóa thiết bị & Kiểm tra truy vấn sau xóa (`404`) | `ADMIN` | `DELETE /equipment/{id}` -> `GET /equipment/{id}` | Xóa trả `200 OK`, gọi lại chi tiết trả `404 Not Found` | **PASS** |

---

### Phân hệ 06 — Đăng ký Gói tập, Tự nối tiếp hạn thẻ & Nhắc hạn Email (`TC-SUB-01` – `TC-SUB-08`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-SUB-01** | Hội viên mới chưa mua gói kiểm tra thẻ điện tử | `MEMBER` | `GET /subscriptions/me` | `HTTP 200 OK`, `has_subscription=false`, `card_status="NO_SUBSCRIPTION"` | **PASS** |
| **TC-SUB-02** | Đăng ký gói tập lần đầu (`NEW`) & tự sinh Hóa đơn | `MEMBER` | `POST /subscriptions` (`plan_id=1`) | `HTTP 201 Created`, `subscription_type="NEW"`, `start_date=today`, sinh `Invoice` + `Payment` | **PASS** |
| **TC-SUB-03** | Gia hạn khi thẻ còn hạn -> Tự động nối tiếp ngày (BR06) | `MEMBER` | `POST /subscriptions` (`plan_id=1` lần 2) | `HTTP 201 Created`, `subscription_type="RENEW"`, `start_date = end_date_cũ + 1 ngày` (không mất ngày cũ) | **PASS** |
| **TC-SUB-04** | Đăng ký gói tập trực tuyến có áp mã giảm giá `WELCOME20` | `MEMBER` | `POST /subscriptions` (`plan_id=1`, `discount_code="WELCOME20"`) | `HTTP 201 Created`, giảm `99.800đ` (20%), `final_amount=399.200đ`, tăng `used_count` | **PASS** |
| **TC-SUB-05** | Chặn đăng ký gói không tồn tại (`404`) hoặc tài khoản `ADMIN` tự mua (`422`) | `MEMBER` / `ADMIN` | `POST /subscriptions` (`plan_id=999999` / token `ADMIN`) | Trả về `404 Not Found` cho gói sai và `422 BusinessRuleException` cho tài khoản không phải hội viên | **PASS** |
| **TC-SUB-06** | Cảnh báo vàng khi thẻ hội viên còn `<= 7` ngày hết hạn | `MEMBER` | `GET /subscriptions/me` | Trả về `near_expiry_warning=true` kèm thông điệp nhắc gia hạn trên đầu trang `/member` | **PASS** |
| **TC-SUB-07** | Lễ tân xem danh sách hội viên sắp hết hạn thẻ | `STAFF` / `MEMBER` | `GET /subscriptions/expiring-soon?within_days=7` | `STAFF` nhận `200 OK`; `MEMBER` bị chặn `403 Forbidden` | **PASS** |
| **TC-SUB-08** | Gửi Email nhắc gia hạn ngầm qua `FastAPI BackgroundTasks` | `STAFF` | `POST /subscriptions/send-expiry-reminders?within_days=7` | `HTTP 200 OK`, tạo bản ghi `Notification` và đưa tác vụ gửi SMTP vào hàng đợi ngầm | **PASS** |

---

### Phân hệ 07 — Kiosk Quét Mã QR Check-in / Check-out & Streak (`TC-QR-01` – `TC-QR-08`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-QR-01** | Quét mã QR hợp lệ lần 1 -> Ghi nhận `CHECK_IN` (< 1000ms) | `STAFF` | `POST /checkins/qr` (`{"qr_code": "DG-..."}`) | `HTTP 200 OK`, `valid=true`, `action="CHECK_IN"`, `response_time_ms < 1000ms` (thực tế ~5–25ms) | **PASS** |
| **TC-QR-02** | Quét lại cùng mã QR lần 2 -> Ghi nhận `CHECK_OUT` & tính phút tập | `STAFF` | `POST /checkins/qr` (`{"qr_code": "DG-..."}`) | `HTTP 200 OK`, `valid=true`, `action="CHECK_OUT"`, `duration_minutes >= 1` | **PASS** |
| **TC-QR-03** | Quét thẻ hội viên chưa mua gói tập nào (`NO_SUBSCRIPTION`) | `STAFF` | `POST /checkins/qr` (Thẻ mới đăng ký chưa mua gói) | `HTTP 200 OK`, `valid=false`, `status="NO_SUBSCRIPTION"`, `action="REJECTED"` | **PASS** |
| **TC-QR-04** | Quét thẻ hội viên đã quá ngày hết hạn (`EXPIRED_CARD`) | `STAFF` | `POST /checkins/qr` (`member18@duckygym.vn`) | `HTTP 200 OK`, `valid=false`, `status="EXPIRED_CARD"`, tự khóa gói quá hạn sang `EXPIRED` | **PASS** |
| **TC-QR-05** | Quét mã QR giả mạo / không tồn tại (`INVALID_CODE`) | `STAFF` | `POST /checkins/qr` (`{"qr_code": "DG-999999-FAKE"}`) | `HTTP 200 OK`, `valid=false`, `status="INVALID_CODE"`, `action="REJECTED"` | **PASS** |
| **TC-QR-06** | Chặn Hội viên tự gọi API Kiosk Quét QR | `MEMBER` | `POST /checkins/qr` | `HTTP 403 Forbidden` (Kiosk độc quyền cho `STAFF`/`ADMIN`) | **PASS** |
| **TC-QR-07** | Cô lập dữ liệu Lịch sử Check-in giữa `MEMBER` và `STAFF` | `MEMBER` / `STAFF` | `GET /checkins/history?page=1&size=20` | `MEMBER` chỉ thấy lượt tập của mình; `STAFF` thấy toàn phòng gym + `active_in_gym_count` | **PASS** |
| **TC-QR-08** | Tự động tính Streak ngày tập & Mở khóa Huy hiệu (10, 30, 100 buổi) | `STAFF` | `POST /checkins/qr` | Cập nhật chính xác `streak_days`, `total_checkins` và phần trăm tiến độ 3 huy hiệu | **PASS** |

---

### Phân hệ 08 — Đặt lịch tập PT 1-1, Quota Buổi Tập & Nâng Cấp Kiến Trúc (`TC-PT-01` – `TC-DB-3NF`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-PT-01** | Xem lịch đặt PT 1-1 theo tuần (Eager Loading `joinedload` chống N+1) & đúng thứ ngày UTC+7 | `MEMBER` | `GET /pt-schedules` & UI `/member` | `HTTP 200 OK`, trả về `week_start`..`week_end`, `work_slots`, `bookings` kèm `subscription_id` & `sessions_remaining` | **PASS** |
| **TC-PT-02** | Hội viên đặt ca tập PT 1-1 nằm trong ca trực mở `TrainerSchedule` hợp lệ | `MEMBER` | `POST /pt-schedules` (`trainer_id`, `booking_date`, `start_time="15:00"`) | `HTTP 201 Created`, gắn `subscription_id`, `start_at`, `end_at`, `status="PENDING"` | **PASS** |
| **TC-PT-03** | Chặn đặt trùng khung giờ đã có học viên khác của cùng PT (BR13) | `MEMBER` | `POST /pt-schedules` (Cùng `trainer_id`, ngày, giờ) | `HTTP 409 Conflict`, `"Trùng lịch PT: HLV ... đã có lịch đặt trong khung giờ..."` | **PASS** |
| **TC-PT-04** | Chặn hội viên đặt 2 PT khác nhau trong cùng 1 khung giờ (BR14) | `MEMBER` | `POST /pt-schedules` (Khác `trainer_id`, cùng ngày & giờ) | `HTTP 409 Conflict`, `"Trùng lịch cá nhân: Bạn đã có một ca tập PT khác..."` | **PASS** |
| **TC-PT-05** | Chặn `end_time <= start_time` (ca ban ngày) hoặc tài khoản `STAFF` tự đặt lịch PT | `MEMBER` / `STAFF` | `POST /pt-schedules` (`15:00 -> 14:00` hoặc token `STAFF`) | `HTTP 422 BusinessRuleException` | **PASS** |
| **TC-PT-06** | Phân quyền duyệt lịch PT: Chặn `MEMBER` tự `confirm` & chặn PT khác duyệt hộ | `MEMBER` / `TRAINER2` | `PATCH /pt-schedules/{id}/confirm` | `HTTP 403 Forbidden` cho cả 2 trường hợp vi phạm quyền | **PASS** |
| **TC-PT-07** | Luồng RESTful `PATCH`: PT `confirm` -> `complete` (trừ 1 buổi `sessions_remaining`) & chặn sửa trạng thái kết thúc | `TRAINER` / `ADMIN` | `PATCH /pt-schedules/{id}/confirm` -> `PATCH /pt-schedules/{id}/complete` | `HTTP 200 OK`, `sessions_remaining` giảm `1`; gọi `cancel` sau `COMPLETED` bị chặn `400` | **PASS** |
| **TC-PAST-01** | Chặn đặt lịch vào khung giờ đã qua hoặc cách hiện tại `< 30 phút` (BR15 - Mục 4.4) | `MEMBER` | `POST /pt-schedules` (`booking_date=today`, `start_time="00:05"`) | `HTTP 400 Bad Request`, thông báo vi phạm `BR15` theo múi giờ `Asia/Ho_Chi_Minh` | **PASS** |
| **TC-QUOTA-01** | Chặn đặt lịch khi hội viên hết buổi tập PT (`sessions_remaining = 0`) hoặc chưa có gói PT (BR16 - Mục 4.4) | `MEMBER` | `POST /pt-schedules` (Tài khoản mua gói `pt_sessions=0`) | `HTTP 403 Forbidden`, thông báo vi phạm `BR16` | **PASS** |
| **TC-CANCEL-LATE** | Chặn hội viên tự hủy lịch sát giờ `< 2 tiếng` trước `start_time` (BR17 - Mục 4.4) | `MEMBER` | `PATCH /pt-schedules/{id}/cancel` (Ca bắt đầu sau `65 phút`) | `HTTP 400 Bad Request`, thông báo vi phạm `BR17` | **PASS** |
| **TC-ADJACENT-01** | Cho phép đặt 2 khung giờ liền kề (`08:00–09:00` và `09:00–10:00`) không báo nhầm trùng lịch (Mục 7.3) | `MEMBER` | `POST /pt-schedules` (`08:00-09:00` & `09:00-10:00`) | Cả 2 request đều trả `HTTP 201 Created` (`start_at_1 < end_at_2 AND end_at_1 > start_at_2` chuẩn) | **PASS** |
| **TC-PT-NOSHOW** | PT đánh dấu học viên vắng mặt không phép (`NO_SHOW`) & trừ 1 buổi tập (Mục 4.5 & 5.6) | `TRAINER` | `PATCH /pt-schedules/{id}/no-show` | `HTTP 200 OK`, `status="NO_SHOW"`, `sessions_remaining` giảm `1` buổi | **PASS** |
| **TC-PT-EXPIRE** | Tự động chuyển ca `PENDING` quá 2 giờ chưa duyệt sang `EXPIRED` & giải phóng slot (Mục 4.5) | Hệ thống / `MEMBER` | Đặt mới vào slot có ca `PENDING` tạo cách đây `> 2 giờ` | Ca cũ tự động chuyển `status="EXPIRED"`, ca mới đặt thành công `HTTP 201 Created` | **PASS** |
| **TC-PT-WORKSLOT** | Bỏ cơ chế tự tạo `TrainerSchedule` ngầm: Đặt ngoài ca trực mở bị chặn `400` (Mục 5.3) | `MEMBER` | `POST /pt-schedules` vào ngày PT chưa mở `TrainerSchedule` | `HTTP 400 Bad Request`, yêu cầu chọn khung giờ nằm trong ca trực mở của HLV | **PASS** |
| **TC-PT-OVERNIGHT** | Hỗ trợ mở ca trực & đặt lịch tập xuyên đêm `23:00 -> 01:00` hôm sau cho Gym 24/7 (Mục 5.2) | `TRAINER` / `MEMBER` | `POST /pt-schedules/work-slots` (`overnight=true`) -> `POST /pt-schedules` | Cả 2 trả `HTTP 201 Created`, `end_at = ngày_hôm_sau 01:00 > start_at` | **PASS** |
| **TC-PT-NODEL** | Thu hồi hoàn toàn quyền xóa vật lý ca tập (`DELETE`) với mọi vai trò kể cả PT & Admin (Mục 1.4 & 5.6) | `TRAINER` / `ADMIN` | `DELETE /pt-schedules/{booking_id}` | `HTTP 403 Forbidden`, bảo toàn tuyệt đối lịch sử đối soát lương/KPI | **PASS** |
| **TC-PT-WEEK53** | Xử lý an toàn tham số ISO `week=53` cho năm chỉ có 52 tuần không văng lỗi 500 (Mục 5.5) | `MEMBER` | `GET /pt-schedules?week=53&year=2025` | `HTTP 400 Bad Request` kèm thông báo rõ ràng thay vì `500 Internal Server Error` | **PASS** |
| **TC-PT-RACE** | Chống Race Condition khi 2 request đồng thời đặt cùng 1 slot PT bằng `SELECT ... FOR UPDATE` (Mục 5.2) | Đa luồng `MEMBER` | 2 luồng song song gọi `create_pt_booking` cùng `trainer_id` + khung giờ | Đúng **1 luồng thành công (`201`)** và **1 luồng bị chặn (`409 Conflict`)**, không lọt Double-Booking | **PASS** |
| **TC-DB-RESTRICT** | Ràng buộc khóa ngoại `ON DELETE RESTRICT` chặn xóa nhầm `User` / `Member` đã có lịch sử giao dịch (Mục 6.1) | Database MySQL | Thực thi `DELETE FROM users WHERE user_id = <pt_có_lịch>` | MySQL chặn bằng `IntegrityError (1451 Cannot delete or update a parent row)`, không mất dữ liệu dây chuyền | **PASS** |
| **TC-DB-3NF** | Chuẩn hóa 3NF bảng `members`: Xóa cột dư thừa `full_name`, `phone`, `email` & ép `user_id NOT NULL UNIQUE` (Mục 3.2.1–3.2.2) | Database MySQL | Kiểm tra `INFORMATION_SCHEMA.COLUMNS` bảng `members` & cập nhật `PUT /users/me` | Bảng `members` không còn cột lặp, đồng bộ tức thì thông tin định danh từ `users` | **PASS** |

---

### Phân hệ 09 — Quầy Thu Ngân POS Lễ Tân & Hóa Đơn ACID (`TC-POS-01` – `TC-POS-06`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-POS-01** | Tra cứu nhanh SĐT hội viên tại quầy POS (< 1 giây) | `STAFF` | `GET /pos/member-lookup?phone=0901000001` & `0999000111` | `HTTP 200 OK`, trả `found=true` (kèm hạn thẻ) cho HV cũ và `found=false` cho khách mới | **PASS** |
| **TC-POS-02** | Thanh toán POS gia hạn thẻ + áp mã `WELCOME20` | `STAFF` | `POST /pos/checkout` (`plan_id=1`, `discount_code="WELCOME20"`, `CASH`) | `HTTP 201 Created`, xuất mã hóa đơn `INV-XXXXXX`, `final_amount=399.200đ`, nối tiếp hạn thẻ | **PASS** |
| **TC-POS-03** | Chặn thanh toán khách mới tại POS nếu bỏ trống Họ tên | `STAFF` | `POST /pos/checkout` (SĐT mới, không truyền `full_name`) | `HTTP 422 BusinessRuleException` yêu cầu nhập Họ và tên để tạo hồ sơ tại quầy | **PASS** |
| **TC-POS-04** | Đăng ký nhanh khách vãng lai + Thu tiền POS trong 1 Transaction | `STAFF` | `POST /pos/checkout` (SĐT mới + `full_name` + `plan_id=1`) | `HTTP 201 Created`, khởi tạo đồng bộ `User + Member + MemberCard + Subscription + Invoice + Payment` | **PASS** |
| **TC-POS-05** | Kiểm chứng Rollback ACID khi mã giảm giá lỗi lúc thanh toán POS | `STAFF` | `POST /pos/checkout` (SĐT mới + `full_name` + `discount_code="EXPIRED10"`) | `HTTP 422`, toàn bộ transaction được `rollback()` — không sinh bản ghi `Member` hay `Invoice` rác! | **PASS** |
| **TC-POS-06** | Xem & tìm kiếm danh sách Hóa đơn POS có phân trang | `STAFF` | `GET /pos/invoices?keyword=...&page=1&size=10` | `HTTP 200 OK`, hiển thị đúng hóa đơn vừa thu ngân | **PASS** |

---

### Phân hệ 10 — Quản lý Mã Giảm Giá / Vouchers (`TC-DISC-01` – `TC-DISC-06`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-DISC-01** | Xem danh sách tất cả mã giảm giá & nhãn trạng thái tự động | `GUEST` | `GET /discounts` | `HTTP 200 OK`, hiển thị `remaining_uses` và `status_label` (`ĐANG HOẠT ĐỘNG` / `HẾT HẠN`) | **PASS** |
| **TC-DISC-02** | Kiểm tra tính giảm giá chuẩn cho cả `PERCENT` và `FIXED` | `MEMBER` | `POST /discounts/validate` (`WELCOME20` & `SUMMER100K` cho đơn `499.000đ`) | `WELCOME20` giảm `99.800đ`; `SUMMER100K` giảm `100.000đ` | **PASS** |
| **TC-DISC-03** | Chặn mã hết hạn (`EXPIRED10`), chưa đủ đơn tối thiểu (`DUCKYVIP`) & mã sai (`404`) | `MEMBER` | `POST /discounts/validate` | `EXPIRED10` -> `422`; `DUCKYVIP` (499k < 2M) -> `422`; `NOTEXIST999` -> `404` | **PASS** |
| **TC-DISC-04** | Admin tạo mã giảm giá mới & chặn tạo `PERCENT > 100%` | `ADMIN` | `POST /discounts` | Tạo hợp lệ -> `201 Created`; truyền `discount_value=120` cho `PERCENT` -> `422` | **PASS** |
| **TC-DISC-05** | Cập nhật Voucher & chặn sửa `PERCENT > 100%` (Regression BUG-05) | `ADMIN` | `PUT /discounts/{id}` (`discount_value=150` vs `30`) | Sửa lên `150%` bị chặn `422`; sửa `30%` thành công `200 OK` | **PASS** |
| **TC-DISC-06** | Phân quyền xóa Voucher (`ADMIN` được xóa, `STAFF` bị chặn) | `ADMIN` / `STAFF` | `DELETE /discounts/{id}` | `STAFF` nhận `403 Forbidden`; `ADMIN` xóa thành công `200 OK` | **PASS** |

---

### Phân hệ 11 — Dashboard SQL Views, Xuất CSV & Lớp Tập Nhóm (`TC-DASH-01` – `TC-CLASS-06`)
| Mã TC | Kịch bản kiểm thử | Vai trò | Đầu vào / Endpoint | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| **TC-DASH-01** | Tổng hợp KPI Dashboard từ 4 SQL Views thống kê | `ADMIN` | `GET /dashboard/summary` | `HTTP 200 OK`, trả về `kpis`, `monthly_revenue_chart`, `daily_revenue`, `plan_breakdown_chart`, `monthly_new_members` | **PASS** |
| **TC-DASH-02** | Lọc doanh thu Dashboard theo khoảng ngày `from_date` – `to_date` | `STAFF` | `GET /dashboard/summary?from_date=2026-01-01&to_date=2026-12-31` | `HTTP 200 OK`, tính đúng `filtered_revenue` trong khoảng thời gian | **PASS** |
| **TC-DASH-03** | Xuất báo cáo doanh thu & hóa đơn ra file `.csv` chuẩn Excel UTF-8 BOM | `ADMIN` | `GET /dashboard/export-csv` | `HTTP 200 OK` (`text/csv`), bắt đầu bằng ký tự BOM `\ufeff`, không lỗi font tiếng Việt | **PASS** |
| **TC-CLASS-01** | Xem danh sách các Lớp tập nhóm (Yoga, Zumba, HIIT, Boxing) | `MEMBER` | `GET /group-classes` | `HTTP 200 OK`, trả về sĩ số `enrolled_count`, `available_slots`, `is_enrolled` | **PASS** |
| **TC-CLASS-02** | Tạo lịch lớp tập nhóm mới & kiểm tra ràng buộc giờ học | `STAFF` / `MEMBER` | `POST /group-classes` | `STAFF` tạo -> `201`; `MEMBER` tạo -> `403`; `end_time <= start_time` -> `422` | **PASS** |
| **TC-CLASS-03** | Hội viên đăng ký lớp tập nhóm & chặn đăng ký trùng lặp | `MEMBER` | `POST /group-classes/{id}/enroll` (2 lần) | Lần 1 -> `200 OK` (`REGISTERED`); Lần 2 -> `409 Conflict` | **PASS** |
| **TC-CLASS-04** | Chặn đăng ký khi lớp tập nhóm đã đầy sĩ số tối đa (`max_capacity`) | `MEMBER` | `POST /group-classes/{id}/enroll` (Lớp `max_capacity=1` đã đủ người) | `HTTP 422 BusinessRuleException`, `"Lớp ... đã đủ sĩ số tối đa"` | **PASS** |
| **TC-CLASS-05** | Lễ tân xem danh sách học viên & Điểm danh lớp tập (`ATTENDED` / `ABSENT`) | `STAFF` | `GET /enrollments` & `PUT /attendance/{enrollment_id}` | `HTTP 200 OK`, ghi nhận `status="ATTENDED"` và dấu thời gian `attended_at` | **PASS** |
| **TC-CLASS-06** | Hội viên hủy đăng ký lớp tập nhóm & hoàn trả slot trống | `MEMBER` | `DELETE /group-classes/{id}/enroll` | Lần 1 hủy -> `200 OK` (`available_slots` tăng 1); hủy lại lần 2 -> `404 Not Found` | **PASS** |

---

## 3. Nhật ký Lỗi Phát hiện & Đã Khắc phục (Full Bug Log)

| Mã Bug | Phân hệ / File | Mức độ | Mô tả chi tiết lỗi | Trạng thái |
|---|---|---|---|---|
| **BUG-01** | `frontend/src/pages/MemberPage.jsx` | Critical | Dư ký tự `D` cuối dòng import gây lỗi trắng trang khi mở ứng dụng (Sprint 2). | **FIXED** |
| **BUG-02** | `frontend/package.json` & `vite.config.js` | High | Xung đột phiên bản `react` giữa thư mục gốc và `frontend` khi render QR Code (Sprint 2). | **FIXED** |
| **BUG-03** | `backend/app/schemas/user.py` | High | Thiếu export class `PasswordChange` khi mở rộng tính năng theo dõi BMI (Sprint 2). | **FIXED** |
| **BUG-04** | `frontend/src/pages/MemberPage.jsx` (`getMondayStr`, `addDaysStr`) | **High (Mới phát hiện)** | Sử dụng `new Date("${dateStr}T00:00:00").toISOString().slice(0, 10)` tại múi giờ Việt Nam (`UTC+7`) khiến 00:00 giờ địa phương bị đổi thành `17:00Z` ngày hôm trước — làm toàn bộ các cột ngày từ Thứ 2 đến Chủ Nhật trên bảng đặt lịch PT 1-1 bị **lệch lùi 1 ngày**. | **FIXED (Đã chuyển sang tính ngày Local chuẩn)** |
| **BUG-05** | `backend/app/routers/discounts.py` (`update_discount`) | **Medium (Mới phát hiện)** | API `POST /discounts` có kiểm tra chặn `PERCENT > 100%`, nhưng API `PUT /discounts/{id}` thiếu bước kiểm tra này khiến Admin có thể cập nhật voucher giảm quá `100%` (VD: `150%`). | **FIXED (Đã bổ sung kiểm tra `<= 100%` khi Update)** |
| **BUG-06** | `backend/app/schemas/auth.py` (`RegisterRequest`) | **Low (Mới phát hiện)** | Trường `phone` trong `RegisterRequest` chỉ kiểm tra độ dài chuỗi (`min_length=10`) mà chưa dùng chuẩn `PhoneStr` (`^(0\|\+84)\d{9,10}$`), dẫn tới API `POST /auth/register` chấp nhận cả chữ cái như `"abcdefghij"`. | **FIXED (Đã đồng bộ dùng `PhoneStr`)** |
| **RED-01..12** | `models/*`, `db/schema_upgrade.py`, `services/pt_schedule_service.py`, `routers/pt_schedules.py`, `core/timezone_utils.py`, `PTPage.jsx`, `MemberPage.jsx` | **Critical / Architectural (12 Chú ý Đỏ)** | Chuẩn hóa 3NF bảng `members` (gỡ bỏ lặp `full_name/phone/email`, ép `user_id NOT NULL UNIQUE`), đổi toàn bộ FK sang `ON DELETE RESTRICT`, bổ sung `total_sessions`/`sessions_remaining` & `subscription_id`, thêm trạng thái `NO_SHOW`/`EXPIRED` (tự động hết hạn `PENDING` > 2h), áp dụng `BR15` (> 30 phút), `BR16` (kiểm tra còn buổi PT), `BR17` (chặn hủy sát giờ < 2h), khóa bi quan `SELECT ... FOR UPDATE`, hỗ trợ ca đêm `23:00->01:00`, bỏ tự tạo ngầm `TrainerSchedule`, thu hồi quyền `DELETE` vật lý (`403`), xử lý an toàn ISO `week=53` + múi giờ `Asia/Ho_Chi_Minh` và tối ưu `joinedload`. | **FIXED & VERIFIED (100% PASS)** |
