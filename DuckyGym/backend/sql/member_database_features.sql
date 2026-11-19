USE duckygym;

DELIMITER //
DROP PROCEDURE IF EXISTS migrate_member_search_indexes//
CREATE PROCEDURE migrate_member_search_indexes()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'members'
          AND column_name = 'qr_code'
    ) THEN
        SET @ddl = 'ALTER TABLE members ADD COLUMN qr_code VARCHAR(64) NULL';
        PREPARE migration_statement FROM @ddl;
        EXECUTE migration_statement;
        DEALLOCATE PREPARE migration_statement;
    END IF;

    UPDATE members
    SET qr_code = CONCAT('QR-MEMBER-', LPAD(member_id, 4, '0'))
    WHERE qr_code IS NULL OR qr_code = '';

    ALTER TABLE members MODIFY qr_code VARCHAR(64) NOT NULL;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'members'
          AND index_name = 'ix_members_phone'
    ) THEN
        SET @ddl = 'CREATE INDEX ix_members_phone ON members (phone)';
        PREPARE migration_statement FROM @ddl;
        EXECUTE migration_statement;
        DEALLOCATE PREPARE migration_statement;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'members'
          AND index_name = 'uq_members_qr_code'
    ) THEN
        SET @ddl = 'CREATE UNIQUE INDEX uq_members_qr_code ON members (qr_code)';
        PREPARE migration_statement FROM @ddl;
        EXECUTE migration_statement;
        DEALLOCATE PREPARE migration_statement;
    END IF;
END//

CALL migrate_member_search_indexes()//
DROP PROCEDURE migrate_member_search_indexes//

DROP PROCEDURE IF EXISTS sp_checkin_validate_qr//
CREATE PROCEDURE sp_checkin_validate_qr(IN p_qr_code VARCHAR(64))
BEGIN
    SELECT
        m.member_id,
        s.subscription_id,
        CASE
            WHEN m.status = 'ACTIVE' AND s.subscription_id IS NOT NULL THEN 1
            ELSE 0
        END AS membership_valid,
        CASE
            WHEN m.status <> 'ACTIVE' THEN 'MEMBER_INACTIVE'
            WHEN s.subscription_id IS NULL THEN 'NO_VALID_SUBSCRIPTION'
            ELSE 'VALID'
        END AS checkin_result
    FROM members AS m
    LEFT JOIN subscriptions AS s
        ON s.member_id = m.member_id
       AND s.status = 'ACTIVE'
       AND CURDATE() BETWEEN s.start_date AND s.end_date
    WHERE m.qr_code = p_qr_code
    ORDER BY s.end_date DESC
    LIMIT 1;
END//
DELIMITER ;

DROP EVENT IF EXISTS ev_expire_subscriptions;
CREATE EVENT ev_expire_subscriptions
    ON SCHEDULE EVERY 1 DAY
    STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
    DO
        UPDATE subscriptions
        SET status = 'EXPIRED'
        WHERE status = 'ACTIVE'
          AND end_date < CURDATE();

SET GLOBAL event_scheduler = ON;
