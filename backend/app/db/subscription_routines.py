import logging

from sqlalchemy import Engine
from sqlalchemy.exc import DBAPIError

logger = logging.getLogger(__name__)


def install_subscription_database_objects(engine: Engine) -> None:
    """Tạo các thủ tục MySQL để kiểm tra và cập nhật trạng thái thẻ hội viên."""
    if engine.dialect.name != "mysql":
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP PROCEDURE IF EXISTS sp_get_valid_subscription_for_checkin"
        )
        connection.exec_driver_sql(
            """
            CREATE PROCEDURE sp_get_valid_subscription_for_checkin(
                IN p_member_id INT
            )
            BEGIN
                SELECT subscription_id
                FROM subscriptions
                WHERE member_id = p_member_id
                  AND status = 'ACTIVE'
                  AND start_date <= CURRENT_DATE()
                  AND end_date >= CURRENT_DATE()
                ORDER BY end_date DESC, subscription_id DESC
                LIMIT 1;
            END
            """
        )
        connection.exec_driver_sql(
            """
            CREATE EVENT IF NOT EXISTS ev_expire_subscriptions_daily
            ON SCHEDULE EVERY 1 DAY
            STARTS TIMESTAMP(CURRENT_DATE + INTERVAL 1 DAY)
            DO
                UPDATE subscriptions
                SET status = 'EXPIRED'
                WHERE status = 'ACTIVE'
                  AND end_date < CURRENT_DATE()
            """
        )

        scheduler_state = connection.exec_driver_sql(
            "SELECT @@GLOBAL.event_scheduler"
        ).scalar_one()
        if str(scheduler_state).upper() != "ON":
            try:
                connection.exec_driver_sql("SET GLOBAL event_scheduler = ON")
            except DBAPIError:
                logger.warning(
                    "MySQL event_scheduler đang ở trạng thái %s. Hãy bật "
                    "event_scheduler để ev_expire_subscriptions_daily chạy tự động.",
                    scheduler_state,
                )
