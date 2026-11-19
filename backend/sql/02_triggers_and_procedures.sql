-- =====================================================================
-- Task T067CF6: Trigger / Event tự động khoá thẻ hết hạn & Stored Procedure Check-in QR
-- Database: duckygym (MySQL 8.0+)
-- =====================================================================

USE duckygym;

-- 1. Scheduled Event chạy định kỳ tự động chuyển các thẻ quá hạn sang EXPIRED
DELIMITER $$

DROP PROCEDURE IF EXISTS sp_expire_overdue_subscriptions $$
CREATE PROCEDURE sp_expire_overdue_subscriptions()
BEGIN
    UPDATE subscriptions
    SET status = 'EXPIRED',
        updated_at = CURRENT_TIMESTAMP
    WHERE status = 'ACTIVE'
      AND end_date < CURDATE();
END $$

DROP TRIGGER IF EXISTS trg_before_attendance_insert_expire_check $$
CREATE TRIGGER trg_before_attendance_insert_expire_check
BEFORE INSERT ON attendance_records
FOR EACH ROW
BEGIN
    -- Tự động cập nhật gói tập hết hạn của hội viên sang EXPIRED trước khi ghi nhận check-in
    UPDATE subscriptions
    SET status = 'EXPIRED',
        updated_at = CURRENT_TIMESTAMP
    WHERE member_id = NEW.member_id
      AND status = 'ACTIVE'
      AND end_date < CURDATE();
END $$

-- 2. Stored Procedure kiểm tra thẻ hội viên còn hạn khi quét QR Check-in
DROP PROCEDURE IF EXISTS sp_validate_qr_checkin $$
CREATE PROCEDURE sp_validate_qr_checkin(IN p_qr_code VARCHAR(64))
BEGIN
    DECLARE v_user_id INT DEFAULT NULL;
    DECLARE v_member_id INT DEFAULT NULL;
    DECLARE v_full_name VARCHAR(100) DEFAULT NULL;
    DECLARE v_phone VARCHAR(20) DEFAULT NULL;
    DECLARE v_sub_id INT DEFAULT NULL;
    DECLARE v_plan_name VARCHAR(100) DEFAULT NULL;
    DECLARE v_end_date DATE DEFAULT NULL;
    DECLARE v_sub_status VARCHAR(20) DEFAULT NULL;

    -- Bước 1: Tự động khoá các gói đã quá hạn tính đến hôm nay
    CALL sp_expire_overdue_subscriptions();

    -- Bước 2: Tìm hội viên theo mã QR (card_code)
    SELECT mc.user_id, mc.member_id, u.full_name, u.phone
    INTO v_user_id, v_member_id, v_full_name, v_phone
    FROM member_cards mc
    INNER JOIN users u ON u.user_id = mc.user_id
    WHERE mc.card_code = p_qr_code
    LIMIT 1;

    IF v_user_id IS NULL THEN
        SELECT
            'INVALID_CODE' AS check_result,
            'Mã QR không tồn tại trong hệ thống' AS message,
            NULL AS user_id,
            NULL AS member_id,
            NULL AS full_name,
            NULL AS plan_name,
            NULL AS end_date;
    ELSE
        -- Bước 3: Kiểm tra gói tập mới nhất của hội viên
        SELECT s.subscription_id, mp.plan_name, s.end_date, s.status
        INTO v_sub_id, v_plan_name, v_end_date, v_sub_status
        FROM subscriptions s
        INNER JOIN membership_plans mp ON mp.plan_id = s.plan_id
        WHERE s.member_id = v_member_id
        ORDER BY (s.status = 'ACTIVE') DESC, s.end_date DESC
        LIMIT 1;

        IF v_sub_id IS NULL THEN
            SELECT
                'NO_SUBSCRIPTION' AS check_result,
                'Hội viên chưa đăng ký gói tập nào' AS message,
                v_user_id AS user_id,
                v_member_id AS member_id,
                v_full_name AS full_name,
                NULL AS plan_name,
                NULL AS end_date;
        ELSEIF v_sub_status = 'ACTIVE' AND v_end_date >= CURDATE() THEN
            SELECT
                'VALID' AS check_result,
                'Thẻ hội viên hợp lệ' AS message,
                v_user_id AS user_id,
                v_member_id AS member_id,
                v_full_name AS full_name,
                v_plan_name AS plan_name,
                v_end_date AS end_date;
        ELSE
            SELECT
                'EXPIRED_CARD' AS check_result,
                CONCAT('Thẻ hội viên đã hết hạn vào ngày ', DATE_FORMAT(v_end_date, '%d/%m/%Y')) AS message,
                v_user_id AS user_id,
                v_member_id AS member_id,
                v_full_name AS full_name,
                v_plan_name AS plan_name,
                v_end_date AS end_date;
        END IF;
    END IF;
END $$

DELIMITER ;

-- Ví dụ gọi Stored Procedure:
-- CALL sp_validate_qr_checkin('DG-000001');
