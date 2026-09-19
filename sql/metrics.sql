-- [Giai đoạn 3 - A] interest_score' theo laptop_model_id (đã sửa theo điều tra event thật)
-- interest_score' = 1*pageview(DeviceDetail) + 2*select_device_for_comparison
-- Đã loại thành phần video review: không tồn tại event/page_name tương ứng trong dữ liệu tracking
--   (xem project_notes.md, mục 0d).
-- Đã đổi event "So sánh" sang select_device_for_comparison (KHÔNG dùng add_to_comparison):
--   containment với int_comparison_chart_device = 78.3% (select) vs 27.5% (add) — xem mục 0c-v.

WITH pageview_cnt AS (
    SELECT
        toInt64OrNull(JSONExtractString(event_data, 'device_id')) AS laptop_id,
        COUNT(*) AS pageview_count
    FROM laplaptech.user_event_tracking
    WHERE event_name = 'pageview'
      AND JSONExtractString(event_data, 'page_name') = 'DeviceDetail'
    GROUP BY laptop_id
),
compare_cnt AS (
    SELECT
        toInt64OrNull(JSONExtractString(event_data, 'device_id')) AS laptop_id,
        COUNT(*) AS compare_count
    FROM laplaptech.user_event_tracking
    WHERE event_name = 'select_device_for_comparison'
    GROUP BY laptop_id
)
SELECT
    m.id AS laptop_model_id,
    COALESCE(p.pageview_count, 0) AS pageview_count,
    COALESCE(c.compare_count, 0)  AS compare_count,
    COALESCE(p.pageview_count, 0) * 1 + COALESCE(c.compare_count, 0) * 2 AS interest_score
FROM laplaptech.laptop_model m
LEFT JOIN pageview_cnt p ON p.laptop_id = m.id
LEFT JOIN compare_cnt  c ON c.laptop_id = m.id;

