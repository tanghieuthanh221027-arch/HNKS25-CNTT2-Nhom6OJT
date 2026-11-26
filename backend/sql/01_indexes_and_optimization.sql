-- =====================================================================
-- Task T067CBB & T067CF6: Indexes tối ưu tìm kiếm hội viên theo SĐT & Mã QR (< 1s)
-- Database: duckygym (MySQL 8.0+)
-- =====================================================================

USE duckygym;

-- 1. Index tìm kiếm hội viên theo Số điện thoại (SĐT) trên bảng users & liên kết 3NF sang members
CREATE INDEX ix_users_phone_lookup ON users (phone);
CREATE INDEX ix_members_user_status ON members (user_id, status);

-- 2. Index tìm kiếm thẻ hội viên theo Mã QR (card_code) trên bảng member_cards
CREATE INDEX ix_member_cards_qr_lookup ON member_cards (card_code, user_id);

-- 3. Index tối ưu kiểm tra gói tập còn hạn khi quét QR check-in
CREATE INDEX ix_subscriptions_active_lookup ON subscriptions (member_id, status, start_date, end_date);

-- =====================================================================
-- Kiểm tra hiệu năng truy vấn với EXPLAIN (Thời gian thực thi < 1ms)
-- =====================================================================
EXPLAIN SELECT u.user_id, u.full_name, u.phone, m.member_id, m.status
FROM users u
LEFT JOIN members m ON m.user_id = u.user_id
WHERE u.phone = '0901000001';

EXPLAIN SELECT mc.card_id, mc.card_code, mc.user_id, mc.member_id, s.subscription_id, s.status, s.end_date
FROM member_cards mc
LEFT JOIN subscriptions s ON s.member_id = mc.member_id AND s.status = 'ACTIVE'
WHERE mc.card_code = 'DG-000001';
