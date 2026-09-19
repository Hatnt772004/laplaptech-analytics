# LapLap Tech Analytics

Phân tích dữ liệu thực chiến từ website Laplap Tech (ClickHouse) — hành vi người dùng và
thông số kỹ thuật laptop — nhằm rút ra insight phục vụ Sản phẩm, Nội dung, và Kinh doanh/Affiliate.

## Problem

Website bán/so sánh laptop Laplap Tech cần trả lời 3 câu hỏi kinh doanh chính (chi tiết:
`docs/project_notes.md`, mục 1.1):
- **Sản phẩm/UX:** người dùng quan tâm chỉ số nào nhất, tính năng nào thu hút nhất?
- **Nội dung/Review:** mẫu laptop/CPU/GPU nào đang hot, có "điểm số thất vọng" nào làm content?
- **Kinh doanh/Affiliate:** trade-off nào người dùng chấp nhận, mẫu nào nên đẩy mạnh?

## Data

- **Nguồn:** ClickHouse (`laplaptech` database) — dữ liệu sống, cập nhật liên tục.
- **Bảng chính:** `user_event_tracking` (clickstream, ~256K pageview events), `laptop_model`
  (thông số kỹ thuật, 159 dòng gốc), `laptop_benchmark_result`, `brand`/`cpu_model`/`gpu_model`
  (dimension đã chuẩn hóa).
- **Quy mô sau làm sạch:** 135/159 laptop (đã loại 24 thiết bị không phải laptop và chuẩn hóa
  đơn vị trọng lượng — chi tiết `src/cleaning.py`).
- **Giới hạn dữ liệu quan trọng:** `laptop_benchmark_result` rất thưa — chỉ 3/157 dòng đủ
  dữ liệu Geekbench, chỉ 1/135 dòng có `office_battery_result_minutes` trên population sạch.
  Điều này buộc pivot 2 hypothesis (H1→H1', Golden Ratio/H9 đổi sang dùng `battery_density`
  thay vì đo hiệu năng pin thực tế) — xem đầy đủ lý do trong `docs/project_notes.md`.

## Methodology

Pipeline: `sql/exploration.sql` (profiling + validation) → `sql/extraction.sql` (JOIN 5 bảng)
→ `src/cleaning.py` (làm sạch, phát hiện contamination) → `notebooks/01-04` (EDA + kiểm định
thống kê) → `notebooks/05` (chuẩn bị dữ liệu Dashboard).

- Toàn bộ giả định, quyết định pivot, và log điều tra chi tiết: `docs/project_notes.md`.
- Kiểm định dùng Mann-Whitney (dữ liệu lệch phân phối) kèm effect size (rank-biserial r), không
  chỉ p-value đơn lẻ.
- `interest_score'` (chỉ số mức độ quan tâm) được xây dựng qua điều tra thực nghiệm nhiều bước
  (không đoán tên event), containment validation đạt 78.3% khi đối chiếu với bảng QA độc lập.

## Key Findings

1. **Ultrabook mỏng nhẹ chiếm ưu thế mật độ pin; gaming là ngoại lệ hiếm** — 24 laptop đạt
   "Golden Ratio" (nhẹ nhất + mật độ pin cao nhất), effect size lớn (r=0.566, p≈10⁻⁷).
2. **Người dùng thực ra quan tâm laptop văn phòng NHIỀU HƠN gaming** — ngược với giả thuyết
   ban đầu (p=0.024), đã kiểm tra loại trừ biến nhiễu năm ra mắt.
3. **2 model gaming "hot nhưng mật độ pin kém bất thường"** — Lenovo LOQ 15ARP9, ASUS
   VivoBook K3605ZF-RP634W — outlier thật ngay cả trong nội bộ phân khúc gaming.

Chi tiết đầy đủ kèm biểu đồ: `reports/insight_summary.md`.

## Business Recommendation

| Insight | Đề xuất | Đội ngũ |
|---|---|---|
| Golden Ratio ultrabook | Bộ lọc "Mật độ pin cao" trên app; content "Top ultrabook pin khỏe" | Sản phẩm, Nội dung |
| Văn phòng > Gaming interest | Rà lại tỷ trọng hiển thị gaming vs văn phòng | Product/UX, Affiliate |
| 2 model hot nhưng pin kém | Content dạng cảnh báo/review sâu cho 2 model cụ thể | Nội dung, Affiliate |

## Impact (ước tính, có giả định)

Các ước tính dưới đây là **minh họa cách tư duy định lượng**, không phải số đo thực tế
(dataset không có dữ liệu doanh thu/CTR thật). Công thức và giả định chi tiết: xem từng
insight trong `reports/insight_summary.md`.

## Dashboard

> 🚧 Đang hoàn thiện — Power BI dashboard (`laplaptech_dashboard.pbix`) gồm 4 trang: Overview,
> Hardware Benchmark Matrix, User Funnel, Data Quality Monitor. Link/ảnh chụp sẽ cập nhật sau.

## Repo Structure
laplaptech-analytics/
├── sql/ # exploration.sql (profiling+validation), extraction.sql (JOIN), metrics.sql (interest_score, CPU ratio)
├── src/ # db.py (connect+cache+note), cleaning.py, metrics.py (stats), viz.py (chart)
├── notebooks/ # 01 cleaning/profiling, 02-04 EDA theo 3 trục, 05 dashboard data prep
├── docs/ # project_notes.md (assumption log đầy đủ), erd.md
├── reports/ # insight_summary.md, figures/
├── data/ # raw/ (cache), processed/ (output pipeline — không commit, xem .gitignore)
└── laplaptech_dashboard.pbix


## Time-box

| Giai đoạn | Nội dung | Thời gian thực tế |
|---|---|---|
| 0 | Chuẩn bị kỹ thuật, ERD | 3 ngày |
| 1 | Bối cảnh kinh doanh, hypotheses | 2 ngày |
| 2 | Làm sạch dữ liệu, Data Quality Audit | 3 ngày |
| 3 | EDA, kiểm định thống kê | 2 ngày |
| 4 | Đúc kết insight & đề xuất | 1 ngày |
| 5 | Dashboard | 3 ngày |
| 6 | Documentation & Deliverable | 1 ngày |
| **Tổng** | | 15 ngày |

## Reproducibility

Chạy lại toàn bộ: `notebooks/01 → 02 → 03 → 04 → 05` theo thứ tự (cần file `.env` theo mẫu
`.env.example`, xem `requirements.txt`). Mọi giả định, threshold, và quyết định pivot đều được
code hóa (không có bước thủ công ẩn) — chi tiết: `docs/project_notes.md`.