# TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)


## ĐỀ TÀI: HỆ THỐNG QUẢN LÝ PHÒNG GYM VÀ HỘI VIÊN — DUCKYGYM

Lớp / Khóa: HN-KS25-CNTT2 · Thực tập doanh nghiệp (OJT) · Nhóm 6

Người biên soạn (TV6 – QA/Doc): Tăng Hiếu Thành (B25DTCN260) · Phiên bản: 2.0 (Hoàn thiện Chương 1 & Chương 2)

Ngày cập nhật: 19/11/2026


# CHƯƠNG 1. GIỚI THIỆU (INTRODUCTION)


## 1.1. Mục đích tài liệu (Purpose)

Tài liệu Đặc tả Yêu cầu Phần mềm (Software Requirements Specification - SRS) này mô tả đầy đủ các yêu cầu nghiệp vụ, phạm vi hệ thống, tác nhân (Actors), sơ đồ Use Case tổng thể, các quy tắc nghiệp vụ (Business Rules BR01 - BR15) và yêu cầu chức năng/phi chức năng của Hệ thống Quản lý Phòng Gym và Hội viên DuckyGym.

Tài liệu là cơ sở thống nhất giữa 6 thành viên Nhóm 6 (TV1 Database, TV2 Backend Lead, TV3 Backend Dev, TV4 Frontend Lead, TV5 Frontend Dev, TV6 QA/Doc) để thiết kế CSDL MySQL, xây dựng RESTful API với FastAPI, phát triển giao diện React (Vite) và thực hiện kiểm thử nghiệm thu.


## 1.2. Bối cảnh và Bài toán thực tế (Business Context)

Tại các phòng tập thể hình (Fitness & Gym Club) quy mô vừa và lớn, việc quản lý hội viên bằng sổ sách, bảng tính Excel hoặc thẻ nhựa truyền thống gặp nhiều bất cập:

- Quá trình kiểm tra hạn thẻ khi hội viên ra/vào phòng tập mất nhiều thời gian, dễ xảy ra tình trạng mượn thẻ hoặc thẻ đã hết hạn vẫn vào tập.
- Lễ tân khó tra cứu nhanh lịch sử đóng phí, tính toán ngày gia hạn nối tiếp hoặc áp dụng mã khuyến mãi (Voucher) tại quầy POS.
- Việc đặt lịch tập 1-1 với Huấn luyện viên cá nhân (PT) qua tin nhắn dễ gây trùng khung giờ của PT hoặc của chính hội viên.
- Chủ phòng gym (Admin) thiếu công cụ trực quan để theo dõi doanh thu theo ngày/tháng, tỷ lệ gia hạn thẻ, số người đang tập thực tế trong phòng và lịch bảo trì định kỳ của các thiết bị tập luyện.
Hệ thống DuckyGym được xây dựng nhằm số hóa toàn diện quy trình từ Đăng ký tài khoản -> Mua/Gia hạn gói tập -> Sinh thẻ hội viên điện tử có mã QR -> Lễ tân quét QR Check-in/Check-out tại quầy POS (< 1 giây) -> Đặt lịch PT 1-1 -> Báo cáo thống kê Dashboard.


## 1.3. Phạm vi hệ thống (Project Scope)

Hệ thống DuckyGym bao gồm 7 phân hệ chức năng chính và 6 tính năng mở rộng (Bonus):

- Phân hệ 1 — Xác thực & Phân quyền 4 vai trò (Auth & RBAC): Đăng ký, đăng nhập JWT, phân quyền ADMIN, STAFF (Lễ tân), MEMBER (Hội viên), PT/TRAINER (Huấn luyện viên), quản lý hồ sơ cá nhân và tự động tính chỉ số BMI.
- Phân hệ 2 — Quản lý Gói tập & Thiết bị (Gym Plans & Equipment): CRUD gói tập, ẩn/hiện gói tập; CRUD thiết bị theo khu vực, theo dõi trạng thái (HOẠT ĐỘNG / BẢO TRÌ / HỎNG) và cảnh báo lịch bảo trì định kỳ 7 ngày.
- Phân hệ 3 — Đăng ký Gói tập & Thẻ Hội viên Điện tử QR (Subscriptions & Digital QR Card): Hội viên đăng ký hoặc gia hạn gói tập (tự động cộng dồn nối tiếp ngày hết hạn nếu thẻ cũ còn hạn), sinh mã thẻ ngẫu nhiên và ảnh QR Base64/SVG, cảnh báo thẻ sắp hết hạn.
- Phân hệ 4 — Kiosk Quét QR Check-in / Check-out tại Màn POS Lễ tân (QR Attendance): Độc quyền trên màn POS của Lễ tân để quét mã QR thẻ hội viên bằng Camera hoặc đầu đọc mã. Quét lần 1 ghi nhận Check-in, quét lần 2 ghi nhận Check-out, phản hồi dưới 1 giây, thống kê số người đang tập thực tế trong phòng.
- Phân hệ 5 — Đặt lịch tập PT 1-1 theo Lịch tuần (PT 1-1 Scheduling): Hội viên xem lịch tuần và đặt ca tập 1-1 với PT; hệ thống chặn trùng khung giờ của cả PT và hội viên; PT xác nhận, hủy hoặc đánh dấu hoàn thành.
- Phân hệ 6 — Thanh toán tại Quầy POS Lễ tân & Quản lý Voucher (Reception POS & Discounts): Lễ tân tìm hội viên theo SĐT, đăng ký mới/gia hạn, kiểm tra & áp mã giảm giá, thu tiền mặt/chuyển khoản, lưu hóa đơn và cập nhật hạn thẻ trong một Transaction duy nhất, in phiếu hóa đơn (window.print).
- Phân hệ 7 — Dashboard Thống kê KPI & Lớp tập nhóm (Analytics & Group Classes): Biểu đồ doanh thu tháng, cơ cấu gói tập từ SQL Views, xuất báo cáo CSV (Admin), gửi email nhắc hạn thẻ qua BackgroundTasks và quản lý/điểm danh lớp tập nhóm (Yoga, Zumba, HIIT, Boxing).

## 1.4. Thuật ngữ và Từ viết tắt (Definitions, Acronyms, and Abbreviations)


| Thuật ngữ / Viết tắt | Giải thích ý nghĩa |
|---|---|
| SRS | Software Requirements Specification — Tài liệu đặc tả yêu cầu phần mềm |
| RBAC | Role-Based Access Control — Phân quyền truy cập dựa trên vai trò (ADMIN, STAFF, MEMBER, PT) |
| JWT | JSON Web Token — Chuẩn mã thông báo xác thực phiên đăng nhập (Bearer Token) |
| POS | Point of Sale — Màn hình quầy giao dịch, thu ngân và quét QR điểm danh dành cho Lễ tân |
| PT / TRAINER | Personal Trainer — Huấn luyện viên thể hình cá nhân hướng dẫn hội viên 1-1 |
| QR Check-in / Out | Điểm danh giờ vào tập và giờ ra về bằng mã phản hồi nhanh (Quick Response Code) trên thẻ hội viên |
| BMI | Body Mass Index — Chỉ số khối cơ thể, tính theo công thức: Cân nặng (kg) / [Chiều cao (m)]² |
| BR / NFR | Business Rule (Quy tắc nghiệp vụ) / Non-Functional Requirement (Yêu cầu phi chức năng) |


# CHƯƠNG 2. MÔ TẢ TỔNG THỂ HỆ THỐNG (OVERALL DESCRIPTION)


## 2.1. Kiến trúc tổng thể sản phẩm (Product Perspective)

Hệ thống DuckyGym được thiết kế theo kiến trúc Client - Server 3 tầng (3-Tier Architecture) hiện đại:

- Tầng Giao diện (Presentation Layer - Frontend): Single Page Application (SPA) xây dựng bằng React 18, Vite 6, React Router v6, Axios Interceptor tự động đính kèm JWT Token, tích hợp quét mã QR qua camera (BarcodeDetector / html5-qrcode), biểu đồ trực quan và in hóa đơn POS.
- Tầng Nghiệp vụ (Application Layer - Backend API): Xây dựng bằng Python FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2 Validation, mã hóa mật khẩu bằng bcrypt, xác thực JWT (HS256) và xử lý tác vụ gửi email ngầm qua FastAPI BackgroundTasks.
- Tầng Cơ sở dữ liệu (Data Layer - Database): Hệ quản trị CSDL quan hệ MySQL 8.0 đạt chuẩn 3NF, kết hợp B-Tree Indexes (tối ưu tìm kiếm SĐT & mã QR < 1s), Trigger/Stored Procedure tự động khóa thẻ hết hạn và 4 SQL Views tổng hợp số liệu doanh thu.

## 2.2. Các tác nhân của hệ thống (System Actors)


| Mã Actor | Tên vai trò (Role) | Mô tả trách nhiệm và quyền hạn chính |
|---|---|---|
| ACT-01 | Khách vãng lai (Guest) | Xem trang chủ giới thiệu phòng gym, hệ sinh thái thiết bị, đội ngũ HLV Master, bảng giá gói tập; thực hiện Đăng ký tài khoản mới hoặc Đăng nhập. |
| ACT-02 | Hội viên (MEMBER) | Đăng nhập, cập nhật hồ sơ & chiều cao/cân nặng (tự tính BMI), theo dõi biểu đồ cơ thể; đăng ký/gia hạn gói tập trực tuyến; xem & tải Thẻ hội viên điện tử QR (kèm chuỗi ngày tập & huy hiệu); đặt lịch PT 1-1 theo tuần; đăng ký lớp tập nhóm; xem lịch sử check-in cá nhân. |
| ACT-03 | Lễ tân / Thu ngân (STAFF) | Sử dụng Màn hình POS Lễ tân: độc quyền vận hành Kiosk Quét QR để Check-in / Check-out và theo dõi hội viên đang tập trong phòng; tra cứu hội viên theo SĐT, thanh toán đăng ký/gia hạn tại quầy có áp mã Voucher và in hóa đơn; điểm danh lớp tập nhóm; kích hoạt gửi email nhắc thẻ sắp hết hạn. |
| ACT-04 | Huấn luyện viên (PT / TRAINER) | Xem lịch hẹn tập 1-1 theo tuần do hội viên đặt; thực hiện Xác nhận (CONFIRMED), Đánh dấu hoàn thành (COMPLETED) hoặc Hủy (CANCELLED) buổi tập; cập nhật hồ sơ chuyên môn (bio, specialization). |
| ACT-05 | Quản trị viên (ADMIN) | Toàn quyền quản trị hệ thống: CRUD gói tập (ẩn/hiện), CRUD thiết bị & chu kỳ bảo trì định kỳ, CRUD mã giảm giá (Voucher), xem Dashboard biểu đồ doanh thu/gói tập và Xuất báo cáo doanh thu/hóa đơn ra file CSV. |


## 2.3. Danh sách Use Case theo từng tác nhân (Use Case Catalog)


| Mã UC | Tên Use Case | Tác nhân chính | Mức ưu tiên | Sprint |
|---|---|---|---|---|
| UC-01 | Đăng ký tài khoản hội viên & Tự động khởi tạo thẻ QR | Khách vãng lai | Must Have | Sprint 1 |
| UC-02 | Đăng nhập JWT & Điều hướng theo 4 vai trò | Tất cả Actors | Must Have | Sprint 1 |
| UC-03 | Quản lý hồ sơ cá nhân, đổi mật khẩu & Tự động tính BMI | MEMBER, PT, STAFF, ADMIN | Must Have | Sprint 1 |
| UC-04 | Xem Trang chủ & Bảng giá gói tập trực tuyến | Khách vãng lai, MEMBER | Must Have | Sprint 1 |
| UC-05 | Quản lý danh mục Gói tập (Thêm, Sửa, Ẩn/Hiện) | ADMIN | Must Have | Sprint 1 |
| UC-06 | Quản lý Thiết bị phòng gym & Lịch bảo trì định kỳ 7 ngày | ADMIN, STAFF | Must Have | Sprint 1 & 3 |
| UC-07 | Đăng ký / Gia hạn gói tập nối tiếp & Sinh mã QR thẻ hội viên | MEMBER | Must Have | Sprint 1 |
| UC-08 | Xem Thẻ hội viên điện tử QR, Tải ảnh QR & Cảnh báo sắp hết hạn | MEMBER | Must Have | Sprint 1 |
| UC-09 | Quét mã QR Check-in / Check-out tại Màn POS Lễ tân (< 1 giây) | STAFF, ADMIN | Must Have | Sprint 2 |
| UC-10 | Theo dõi hội viên đang tập & Xem lịch sử Check-in phân trang, lọc ngày | STAFF, ADMIN, MEMBER | Must Have | Sprint 2 |
| UC-11 | Đặt lịch tập PT 1-1 trên lưới lịch tuần (Chặn trùng giờ) | MEMBER | Must Have | Sprint 2 |
| UC-12 | Xác nhận, Hoàn thành hoặc Hủy lịch hẹn tập 1-1 | PT / TRAINER, ADMIN | Must Have | Sprint 2 |
| UC-13 | Thanh toán đăng ký/gia hạn tại Quầy POS Lễ tân & In hóa đơn | STAFF, ADMIN | Must Have | Sprint 3 |
| UC-14 | Quản lý Mã giảm giá (Voucher) & Kiểm tra mã cho POS | ADMIN, STAFF | Must Have | Sprint 3 |
| UC-15 | Xem Dashboard KPI, Biểu đồ doanh thu/gói tập & Xuất file CSV | ADMIN, STAFF | Must Have | Sprint 3 |
| UC-16 | Theo dõi biểu đồ Cân nặng/BMI, Huy hiệu Streak, Lớp tập nhóm & Email nhắc hạn | MEMBER, STAFF, ADMIN | Bonus | Sprint 3 |


## 2.4. Các quy tắc nghiệp vụ cốt lõi (Business Rules BR01 – BR15)


| Mã quy tắc | Tên quy tắc | Mô tả chi tiết ràng buộc nghiệp vụ trong hệ thống |
|---|---|---|
| BR01 | Mã hóa mật khẩu | Mật khẩu người dùng bắt buộc từ 8–72 ký tự và được băm một chiều bằng thuật toán bcrypt trước khi lưu vào CSDL. |
| BR02 | Kiểm soát trạng thái tài khoản | Chỉ tài khoản có status = 'ACTIVE' mới được phép đăng nhập và sử dụng hệ thống; tài khoản LOCKED hoặc INACTIVE bị từ chối (403). |
| BR03 | Định danh duy nhất | Mỗi Email, Số điện thoại và Username là duy nhất trên toàn hệ thống. Vi phạm trả về HTTP 409 Conflict. |
| BR04 | Bảo toàn dữ liệu lịch sử | Không xóa cứng (hard-delete) các gói tập đã phát sinh hóa đơn; sử dụng cơ chế ngừng kinh doanh (status = 'DISCONTINUED'). |
| BR05 | Ràng buộc gói tập | Tên gói tập không được trùng lặp, giá gói tập (price) và số ngày hiệu lực (duration_days) bắt buộc > 0. |
| BR06 | Nối tiếp thời hạn thẻ | Khi hội viên đăng ký thêm gói tập trong lúc thẻ hiện tại vẫn còn hạn (end_date >= hôm nay), ngày bắt đầu gói mới tự động bằng (end_date cũ + 1 ngày). |
| BR07 | Tự động khóa thẻ quá hạn | Trước mỗi lần kiểm tra thẻ hoặc quét QR, mọi gói tập có status = 'ACTIVE' nhưng end_date < CURDATE() tự động chuyển sang 'EXPIRED'. |
| BR08 | Cảnh báo thẻ sắp hết hạn | Khi thời hạn thẻ còn từ 0 đến 7 ngày, hệ thống hiển thị cảnh báo nhắc gia hạn trên trang Hội viên và cho phép Lễ tân gửi email nhắc hạn (<= 3 ngày). |
| BR09 | Cơ chế Quét QR 2 chiều | Tại Kiosk POS Lễ tân: Nếu hội viên chưa có lượt vào đang mở trong ngày -> Ghi nhận CHECK_IN. Nếu đã có lượt CHECK_IN chưa check-out -> Ghi nhận CHECK_OUT và tính số phút tập. |
| BR10 | Độc quyền Kiosk POS | Chức năng quét mã QR Check-in/Check-out chỉ được thực hiện bởi Lễ tân (STAFF/CASHIER) hoặc ADMIN trên màn hình POS để kiểm soát ra vào. |
| BR11 | Giới hạn xem lịch sử Check-in | Hội viên (MEMBER) chỉ được xem lịch sử check-in của bản thân; Lễ tân và Admin được xem và lọc lịch sử của toàn bộ hội viên. |
| BR12 | Chặn trùng lịch PT 1-1 | Một ca đặt lịch PT mới bị từ chối (409 Conflict) nếu giao thoa thời gian (start_time < existing.end_time AND end_time > existing.start_time) với lịch PENDING/CONFIRMED của PT đó hoặc của chính hội viên đó. |
| BR13 | Toàn vẹn giao dịch POS | Tại quầy POS Lễ tân, việc tạo/gia hạn Subscription, ghi nhận sử dụng Voucher, tạo Invoice (PAID) và tạo Payment phải thực hiện trong 1 DB Transaction duy nhất (commit hoặc rollback đồng thời). |
| BR14 | Điều kiện áp dụng Voucher | Voucher chỉ hợp lệ khi is_active = true, chưa quá ngày expiry_date, used_count < usage_limit và giá trị gói tập >= min_order_amount. |
| BR15 | Giới hạn sĩ số lớp tập nhóm | Mỗi lớp tập nhóm (Yoga, Zumba, HIIT) có max_capacity cố định; hệ thống chặn đăng ký mới khi số học viên REGISTERED/ATTENDED đã đạt max_capacity. |


## 2.5. Đặc tả chi tiết 3 Luồng nghiệp vụ chính (Core Functional Flows)


### 2.5.1. Luồng 1: Đăng ký, Đăng nhập JWT và Phân quyền 4 vai trò

- Đầu vào: Thông tin đăng ký (Họ tên, Email, SĐT, Mật khẩu) hoặc thông tin đăng nhập (Email/Username/SĐT, Mật khẩu).
- Xử lý tại Backend: Kiểm tra trùng lặp (BR03), băm mật khẩu bằng bcrypt (BR01), tự động khởi tạo hồ sơ Member + thẻ điện tử MemberCard. Khi đăng nhập, đối chiếu mật khẩu và ký JWT Access Token chứa user_id, role, exp.
- Xử lý tại Frontend: Lưu JWT vào localStorage, tự động đính kèm header Authorization: Bearer <token> qua Axios Interceptor. Component ProtectedRoute kiểm tra role để điều hướng: ADMIN -> /admin, STAFF -> /staff, PT/TRAINER -> /pt, MEMBER -> /member.

### 2.5.2. Luồng 2: Đăng ký / Gia hạn gói tập và Sinh mã QR thẻ hội viên điện tử

- Đầu vào: Hội viên chọn gói tập (plan_id), ngày bắt đầu dự kiến, mã giảm giá (nếu có) và phương thức thanh toán.
- Xử lý tại Backend (POST /subscriptions): Kiểm tra gói tập ACTIVE; kiểm tra gói đang còn hạn của hội viên để tính start_date nối tiếp (BR06); tính toán giảm giá Voucher (BR14); sinh mã thẻ khó đoán (DG-XXXXXX-XXXX) và ảnh QR dạng Base64 Data URI; lưu Subscription, Invoice và Payment.
- Đầu ra: Trả về thông tin thẻ hội viên điện tử và mã QR để hiển thị tại /member, cho phép tải ảnh QR (.png) về điện thoại.

### 2.5.3. Luồng 3: Quét mã QR Check-in / Check-out tại Màn POS Lễ tân

- Đầu vào: Lễ tân tại màn hình POS (/staff) dùng Camera hoặc máy quét đọc mã QR trên thẻ hội viên (POST /checkins/qr).
- Xử lý tại Backend & Database: Tự động cập nhật các gói tập quá hạn sang EXPIRED (BR07); tra cứu nhanh thẻ hội viên qua Index ix_member_cards_card_code; kiểm tra gói tập ACTIVE. Thực hiện chuyển đổi trạng thái CHECK_IN (lần 1) hoặc CHECK_OUT (lần 2), cập nhật chuỗi ngày tập (Streak) và huy hiệu (10, 30, 100 buổi).
- Đầu ra: Trả kết quả dưới 1 giây kèm âm thanh phản hồi trên màn POS Lễ tân, cập nhật bảng theo dõi hội viên đang tập trong phòng theo thời gian thực.

## 2.6. Yêu cầu phi chức năng (Non-Functional Requirements NFR01 – NFR06)


| Mã NFR | Nhóm yêu cầu | Chỉ tiêu kỹ thuật cụ thể |
|---|---|---|
| NFR01 | Hiệu năng (Performance) | Thời gian phản hồi API quét mã QR Check-in/Check-out (POST /checkins/qr) và tìm kiếm hội viên theo SĐT tại quầy POS đạt dưới 1 giây (< 1000ms, thực tế đạt < 20ms nhờ B-Tree Index). |
| NFR02 | Bảo mật (Security) | Mật khẩu băm bằng bcrypt; API bảo vệ bằng JWT Bearer Token; phân quyền chặt chẽ 4 vai trò (thiếu token trả 401, sai vai trò trả 403). |
| NFR03 | Toàn vẹn dữ liệu (Reliability) | Đảm bảo tính ACID cho giao dịch thanh toán POS; ràng buộc khóa ngoại (Foreign Key) và CheckConstraint trên MySQL 8.0. |
| NFR04 | Xử lý lỗi chuẩn hóa | Mọi lỗi nghiệp vụ và lỗi hệ thống đều được Global Exception Handler chuẩn hóa thành cấu trúc JSON thống nhất (success, error_code, message, details) mà không làm lộ cấu trúc bảng CSDL. |
| NFR05 | Tính khả dụng & Giao diện (Usability) | Giao diện Dark Mode hiện đại, tương thích Desktop, Tablet quầy POS và điện thoại di động của hội viên; hỗ trợ in hóa đơn trực tiếp qua trình duyệt. |
| NFR06 | Khả năng bảo trì (Maintainability) | Codebase tách biệt rõ tầng Router - Service - Schema - Model ở Backend và Component - Context - API Client ở Frontend; script seed dữ liệu đảm bảo tính Idempotent. |
