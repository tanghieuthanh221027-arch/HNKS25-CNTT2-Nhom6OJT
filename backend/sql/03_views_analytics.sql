-- =====================================================================
-- Task T067D16: SQL Views thống kê doanh thu theo ngày/tháng, top gói tập & hội viên mới
-- Database: duckygym (MySQL 8.0+)
-- =====================================================================

USE duckygym;

-- 1. View doanh thu theo ngày (vw_daily_revenue)
CREATE OR REPLACE VIEW vw_daily_revenue AS
SELECT
    DATE(i.created_at) AS revenue_date,
    COUNT(i.invoice_id) AS invoice_count,
    COALESCE(SUM(i.total_amount), 0) AS gross_revenue,
    COALESCE(SUM(i.discount_amount), 0) AS total_discount,
    COALESCE(SUM(i.final_amount), 0) AS net_revenue
FROM invoices i
WHERE i.status = 'PAID'
GROUP BY DATE(i.created_at)
ORDER BY revenue_date DESC;

-- 2. View doanh thu theo tháng (vw_monthly_revenue)
CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    DATE_FORMAT(i.created_at, '%Y-%m') AS revenue_month,
    COUNT(i.invoice_id) AS invoice_count,
    COALESCE(SUM(i.total_amount), 0) AS gross_revenue,
    COALESCE(SUM(i.discount_amount), 0) AS total_discount,
    COALESCE(SUM(i.final_amount), 0) AS net_revenue
FROM invoices i
WHERE i.status = 'PAID'
GROUP BY DATE_FORMAT(i.created_at, '%Y-%m')
ORDER BY revenue_month DESC;

-- 3. View Top gói tập bán chạy nhất (vw_top_gym_plans)
CREATE OR REPLACE VIEW vw_top_gym_plans AS
SELECT
    mp.plan_id,
    mp.plan_name,
    mp.category,
    mp.duration_days,
    mp.price,
    COUNT(s.subscription_id) AS total_subscriptions,
    SUM(CASE WHEN s.status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_subscriptions,
    COALESCE(SUM(CASE WHEN i.status = 'PAID' THEN i.final_amount ELSE 0 END), 0) AS total_revenue
FROM membership_plans mp
LEFT JOIN subscriptions s ON s.plan_id = mp.plan_id
LEFT JOIN invoices i ON i.subscription_id = s.subscription_id
GROUP BY mp.plan_id, mp.plan_name, mp.category, mp.duration_days, mp.price
ORDER BY total_subscriptions DESC, total_revenue DESC;

-- 4. View số hội viên mới theo tháng (vw_monthly_new_members)
CREATE OR REPLACE VIEW vw_monthly_new_members AS
SELECT
    DATE_FORMAT(m.join_date, '%Y-%m') AS join_month,
    COUNT(m.member_id) AS new_members_count
FROM members m
GROUP BY DATE_FORMAT(m.join_date, '%Y-%m')
ORDER BY join_month DESC;

-- Truy vấn kiểm tra kết quả từ các SQL View:
-- SELECT * FROM vw_daily_revenue LIMIT 10;
-- SELECT * FROM vw_monthly_revenue LIMIT 12;
-- SELECT * FROM vw_top_gym_plans;
-- SELECT * FROM vw_monthly_new_members LIMIT 12;
