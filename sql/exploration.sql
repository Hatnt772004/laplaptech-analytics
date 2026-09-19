-- LƯU Ý: File này chỉ để lưu trữ/tham chiếu câu query.
-- KHÔNG chạy trực tiếp qua SQL extension của VSCode (dễ bị nhầm connection profile, VD: Postgres).
-- Việc thực thi thật sự luôn qua src/db.py -> query_cached() trong notebook.
-- ============================================================
-- Kiểm tra khả năng dùng laptop_catalog (không có cột ID để JOIN)
-- So khớp tên với laptop_model.name — logic matching thực hiện
-- bằng Python/pandas trong notebooks/01_cleaning_and_profiling.ipynb
-- vì cần normalize + fuzzy match, ClickHouse SQL thuần không tiện làm việc này.
-- ============================================================
SELECT name FROM laplaptech.laptop_catalog;
SELECT id, name FROM laplaptech.laptop_model;

-- ============================================================
-- [Giai đoạn 2 - 2.2.2] Tỷ lệ NULL của Geekbench 6 vs Geekbench 7 theo năm ra mắt
-- Dùng để quyết định COALESCE hay tách riêng theo thế hệ.
-- ============================================================
SELECT
    m.year_introduce,
    COUNT(*) AS total_laptops,
    SUM(b.geekbench_6_cpu_multi_core_plugged_in IS NULL) AS null_gb6,
    SUM(b.geekbench_7_cpu_multi_core_plugged_in IS NULL) AS null_gb7
FROM laplaptech.laptop_benchmark_result b
INNER JOIN laplaptech.laptop_model m ON b.laptop_model_id = m.id
GROUP BY m.year_introduce
ORDER BY m.year_introduce;

-- ============================================================
-- [Giai đoạn 2 - 2.5.1] Preview JSON_EXTRACT device_id trên user_event_tracking
-- Chỉ dùng để TEST/VALIDATE ở Giai đoạn 2, KHÔNG phải bản chính thức
-- (bản chính thức JOIN 5 bảng nằm ở sql/extraction.sql, làm ở Bước 1 kế tiếp).
-- ============================================================
SELECT
    id AS event_id,
    session_id,
    event_name,
    toInt64OrNull(JSONExtractString(event_data, 'device_id')) AS laptop_id_extracted,
    event_local_timestamp
FROM laplaptech.user_event_tracking
WHERE event_name = 'pageview'
  AND JSONExtractString(event_data, 'page_name') = 'DeviceDetail'
LIMIT 1000;

-- ============================================================
-- [Giai đoạn 3 - 0] Liệt kê toàn bộ event_name thực tế + số lượng, để xác định
-- ============================================================

SELECT
    event_name,
    COUNT(*) AS total_events,
    COUNT(DISTINCT session_id) AS distinct_sessions
FROM laplaptech.user_event_tracking
GROUP BY event_name
ORDER BY total_events DESC;

-- Liệt kê toàn bộ page_name trong event pageview,
-- để xác định có trang/hành động xem video review được log dưới dạng pageview hay không.
SELECT
    JSONExtractString(event_data, 'page_name') AS page_name,
    COUNT(*) AS total_events
FROM laplaptech.user_event_tracking
WHERE event_name = 'pageview'
GROUP BY page_name
ORDER BY total_events DESC;

-- Trong cùng session, add_to_comparison có luôn đi sau
-- select_device_for_comparison không? Giúp xác định event nào đại diện "click So sánh" thật.
SELECT
    session_id,
    COUNTIf(event_name = 'select_device_for_comparison') AS n_select,
    COUNTIf(event_name = 'add_to_comparison') AS n_add
FROM laplaptech.user_event_tracking
WHERE event_name IN ('select_device_for_comparison', 'add_to_comparison')
GROUP BY session_id
HAVING n_add > 0
ORDER BY n_add DESC
LIMIT 50;

