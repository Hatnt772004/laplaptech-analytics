## [Giai đoạn 0] Quyết định về cách xử lý các bảng int_* / stg_*

- Vẫn TỰ viết SQL JOIN 5 bảng (laptop_model, brand, cpu_model, gpu_model, laptop_benchmark_result)
  và TỰ viết JSON_EXTRACT thủ công từ user_event_tracking.event_data để luyện tập (Hướng A).
- int_dim_laptop / int_events_enriched / int_comparison_chart_device chỉ dùng làm nguồn đối chiếu
  (QA) sau khi tự làm xong, không dùng làm nguồn chính.

## [Giai đoạn 0] Quyết định CUỐI CÙNG về laptop_catalog

Match tên: 100.0% (159 dòng, exact: 100.0%, fuzzy: 0.0%).
Sanity-check: 17 dòng laptop_model bị trùng name_norm,
8 dòng laptop_catalog match >1 id, là tập con của laptop_model: True.

QUYẾT ĐỊNH: phát hiện collision/fanout → 100% match ban đầu KHÔNG đáng tin cậy.
→ Loại laptop_catalog khỏi phạm vi phân tích chính thức (sql/extraction.sql), không dùng để JOIN dưới bất kỳ hình thức nào.

## [Flag cho Giai đoạn 2 - Data Quality Audit] laptop_model có tên trùng lặp

17 dòng trong laptop_model có name_norm trùng dòng khác (id khác nhau,
không ảnh hưởng JOIN qua id, nhưng cần rà lại khi viết báo cáo/content theo tên ở Giai đoạn 4).
Id liên quan: [9, 11, 59, 65, 68, 69, 83, 95, 96, 97, 98, 105, 108, 116, 117, 134, 153]

## [Giai đoạn 1] 1.1 Bối cảnh kinh doanh

| Bối cảnh / Đơn vị             | Câu hỏi kinh doanh cần giải quyết                                                         |
|:------------------------------|:------------------------------------------------------------------------------------------|
| Đội ngũ Sản phẩm (Product/UX) | Người dùng quan tâm chỉ số nào nhất (pin hay điểm Geekbench)? Tính năng nào thu hút nhất? |
| Đội ngũ Nội dung/Review       | Mẫu laptop/CPU/GPU nào đang hot? Có 'điểm số thất vọng' nào làm chủ đề content không?     |
| Đội ngũ Kinh doanh/Affiliate  | Trade-off nào người dùng chấp nhận? Mẫu nào hiệu năng/giá trị tốt nhất để đẩy mạnh?       |

## [Giai đoạn 1] 1.2 Biến trọng yếu (đã đối chiếu schema thật)

| Nhóm                       | Bảng                        | Biến                                                                      | Vai trò                                | Đối chiếu schema thật   |
|:---------------------------|:----------------------------|:--------------------------------------------------------------------------|:---------------------------------------|:------------------------|
| I. Hiệu năng & Năng lượng  | laptop_benchmark_result     | geekbench_6_cpu_multi_core_plugged_in, geekbench_6_cpu_multi_core_battery | Đo mức sụt giảm hiệu năng khi dùng pin | OK                      |
| I. Hiệu năng & Năng lượng  | laptop_benchmark_result     | office_battery_result_minutes, gaming_battery_result_minutes              | Thời lượng pin theo tác vụ             | OK                      |
| I. Hiệu năng & Năng lượng  | laptop_model                | battery_capacity_whr                                                      | Dung lượng pin danh định               | OK                      |
| II. Thiết kế & Di động     | laptop_model                | laptop_weight, charger_weight                                             | Tổng trọng lượng di chuyển             | OK                      |
| II. Thiết kế & Di động     | laptop_model                | cpu_tdp, gpu_tdp                                                          | Công suất tản nhiệt thiết kế           | OK                      |
| III. Phân khúc & Định danh | laptop_model                | is_gaming_laptop, is_workstation                                          | Phân loại phân khúc                    | OK                      |
| III. Phân khúc & Định danh | laptop_model                | year_introduce                                                            | Vòng đời sản phẩm                      | OK                      |
| III. Phân khúc & Định danh | brand, cpu_model, gpu_model | name                                                                      | Tên thương hiệu/chip để gom nhóm       | OK                      |
| IV. Hành vi & Nhu cầu      | user_event_tracking         | event_name, event_data                                                    | Nhận diện hành động/nội dung quan tâm  | OK                      |
| IV. Hành vi & Nhu cầu      | user_event_tracking         | session_id, user_psuedo_id                                                | Hành trình người dùng                  | OK                      |
| IV. Hành vi & Nhu cầu      | laptop_benchmark_result     | review_video_url                                                          | Điểm chạm nội dung                     | OK                      |

## [Giai đoạn 1] 1.3 Hypotheses

| ID   | Trục   | Hypothesis                                                                        | Kiểm định                                |
|:-----|:-------|:----------------------------------------------------------------------------------|:-----------------------------------------|
| H1   | Trục 1 | Hãng CPU/GPU giữ hiệu năng khi dùng pin tốt hơn hẳn hãng khác (CPU_Battery_Ratio) | ANOVA/Kruskal-Wallis theo nhóm chip      |
| H2   | Trục 1 | TDP cao → CPU_Battery_Ratio thấp hơn đáng kể                                      | Spearman correlation                     |
| H3   | Trục 1 | Pin/Whr khác biệt có ý nghĩa giữa các hãng CPU                                    | ANOVA/Kruskal-Wallis                     |
| H4   | Trục 1 | Tồn tại nhóm 'Golden Ratio': top 25% pin/Whr đồng thời top 25% nhẹ                | Descriptive, percentile 2 chiều          |
| H5   | Trục 2 | Laptop gaming nhận interest_score cao hơn laptop văn phòng                        | Mann-Whitney                             |
| H6   | Trục 2 | Session xem review_video_url có session dài hơn                                   | Mann-Whitney                             |
| H7   | Trục 2 | Mobile có tỷ lệ bounce cao hơn desktop                                            | Chi-square                               |
| H8   | Trục 3 | Pin >8h nhận interest_score cao hơn gaming top 25% Geekbench                      | Mann-Whitney, sensitivity 420/480/540    |
| H9   | Trục 3 | Tồn tại nhóm 'click nhiều nhưng benchmark kém'                                    | Descriptive, liệt kê danh sách           |
| H10  | Trục 3 | Gaming pin tốt (>300') nhận interest_score cao hơn gaming pin kém                 | Mann-Whitney trong cùng phân khúc gaming |

**Điểm sửa quan trọng đã áp dụng:**
- H1/H3: group theo "hãng CPU" phải JOIN cpu_model.brand_id → brand.id, lọc is_chip_brand = true.
- interest_score (dùng cho H5, H8, H9, H10) = 1×pageview DeviceDetail + 2×click "So sánh" + 3×click review_video_url,
  tính theo laptop_model_id. Đối chiếu thành phần "click So sánh" với int_comparison_chart_device.

## [Giai đoạn 1] 1.4 Prioritization

| ID   |   Impact |   Effort |   Data Confidence |   Priority Score |
|:-----|---------:|---------:|------------------:|-----------------:|
| H1   |        4 |        2 |                 4 |             8    |
| H2   |        3 |        2 |                 4 |             6    |
| H3   |        4 |        2 |                 3 |             6    |
| H4   |        3 |        3 |                 4 |             4    |
| H5   |        5 |        3 |                 3 |             5    |
| H6   |        3 |        3 |                 3 |             3    |
| H7   |        2 |        3 |                 3 |             2    |
| H8   |        5 |        4 |                 3 |             3.75 |
| H9   |        5 |        3 |                 3 |             5    |
| H10  |        4 |        3 |                 3 |             4    |

**Quyết định: bộ 3 insight chính = H1, H5, H9** (thay vì H1, H9, H10).

Lý do: H1+H9+H10 khiến Trục 2 (User Engagement) không có đại diện nào, trong khi dashboard
(Trang 3 - User Funnel) và cấu trúc 3-trục của cả kế hoạch cần đủ 3 trục. H5 dùng chung
interest_score với H9/H10 nên không tốn thêm effort đáng kể. H10 giữ trong backlog, làm nếu còn thời gian.

Backlog (làm nếu còn thời gian): H2, H3, H4, H6, H7, H8, H10.

*(Lưu ý: quyết định này dựa trên Data Confidence ước tính tại Giai đoạn 1. Đã được xác minh
lại và điều chỉnh ở Giai đoạn 2 — xem mục "[Giai đoạn 2] Chốt population sạch & H1'" bên dưới,
trong đó H1 được thay bằng H1' do laptop_benchmark_result không đủ dữ liệu.)*

## [Giai đoạn 2 - 2.0] Kết luận về laptop_model trùng tên

- Nhiều khả năng RE-RELEASE (cùng tên, khác year_introduce): ['Acer Nitro V 15', 'Asus Vivobook S 14', 'Asus Zenbook A14', 'Asus Zenbook S 16']
- Nhiều khả năng LỖI NHẬP LIỆU (cùng tên, cùng year_introduce): ['ASUS Vivobook S14', 'Asus ZenBook Test device', 'Laptop mới test thôi', 'Titan 18 HX Dragon Edition Norse Myth']
- Quyết định: giữ nguyên tất cả các id này trong phân tích (không xóa), vì id vẫn là khóa duy nhất
  hợp lệ để JOIN; chỉ cẩn trọng khi viết báo cáo/content theo TÊN ở Giai đoạn 4.

## [Giai đoạn 2 - 2.1] Data Profiling

### laptop_benchmark_result

| column                                |   null_pct |   min |   max |   outlier_count |    skew |
|:--------------------------------------|-----------:|------:|------:|----------------:|--------:|
| geekbench_6_cpu_multi_core_plugged_in |        0.4 |  7949 | 22252 |               0 |   0.617 |
| geekbench_6_cpu_multi_core_battery    |        0   |  6895 | 21259 |               1 |   0.723 |
| office_battery_result_minutes         |        0   |   525 |   706 |               1 |  -0.894 |
| gaming_battery_result_minutes         |        1   |   nan |   nan |             nan | nan     |

### laptop_model

| column               |   null_pct |   min |    max |   outlier_count |   skew |
|:---------------------|-----------:|------:|-------:|----------------:|-------:|
| battery_capacity_whr |     0.0314 |     0 |  121.3 |              16 | -0.726 |
| laptop_weight        |     0.0314 |     0 | 3620   |               9 |  0.002 |
| charger_weight       |     0.3962 |     0 | 1199   |               0 |  0.874 |

## [Giai đoạn 2 - 2.2.1] Parse cpu_tdp/gpu_tdp

Quyết định: với TDP dạng dải (VD "15-28W"), lấy TRUNG BÌNH của dải làm giá trị đại diện
(không lấy min hoặc max riêng lẻ) vì đây là ước lượng cân bằng, phù hợp cho correlation ở H2.
Logic parse: hàm parse_tdp() trong src/cleaning.py.

## [Giai đoạn 2 - 2.2.2] Quyết định Geekbench 6 vs 7

|   year_introduce |   total_laptops |   null_gb6 |   null_gb7 |
|-----------------:|----------------:|-----------:|-----------:|
|             2026 |               3 |          2 |          3 |

Quyết định: COALESCE. Toàn bộ hypothesis liên quan (H1, H2) chỉ dùng geekbench_6_*
theo phạm vi đã chốt ở Giai đoạn 1, KHÔNG mở rộng sang geekbench_7 trong bản đầu (giữ trong backlog nếu cần).

## [Giai đoạn 2 - 2.3.4] Audit population (snapshot hiện tại: laptop_model = 159 dòng)

Phát hiện 26 thiết bị KHÔNG phải laptop (logic phát hiện tự động,
So với snapshot Giai đoạn 2 gốc (159 dòng, 22 ID nhiễm):
- ID nhiễm MỚI: [80, 135, 158, 159]
- ID không còn bị coi là nhiễm: Không có
Population sạch hiện tại: 133/159 dòng.

## [Giai đoạn 2 - 2.4b] Kiểm tra đồng nhất JSON key theo app_version

Số event_name có key lệch giữa các version: 0
Không phát hiện lệch key — an toàn để JSON_EXTRACT trực tiếp ở Bước 2.5.1/sql/extraction.sql.

## [Giai đoạn 2 - 2.5.2] Đối chiếu JSON_EXTRACT thủ công với int_events_enriched

Tỷ lệ mismatch: 0.0% trên 1000 dòng đối chiếu.
Quyết định: chấp nhận được, tiếp tục dùng cách tự extract cho sql/extraction.sql.

## [Giai đoạn 2] Tổng kết

Đã hoàn thành: profiling, parse TDP, quyết định Geekbench 6/7, Data Quality Audit đầy đủ
(outlier vật lý, rule NULL, validate CPU_Battery_Ratio, audit population — loại
26 thiết bị nhiễm + chuẩn hóa đơn vị laptop_weight), kiểm tra đồng nhất
JSON key, xử lý event tracking (JSON_EXTRACT, đối chiếu QA, session journey), unit test.

Phát hiện quan trọng: laptop_benchmark_result chỉ có 3/157 dòng -> H1 gốc không khả thi,
thay bằng H1' (trade-off trọng lượng/pin, dùng laptop_model, không phụ thuộc benchmark).

Output chính thức DUY NHẤT: data/processed/laptop_metrics.csv (đã loại contamination, đã chuẩn
hóa đơn vị). Sẵn sàng chuyển sang Bước 1: viết sql/extraction.sql.

## [Giai đoạn 3 - 0] event_name và page_name thực tế

### event_name

| event_name                                   |   total_events |   distinct_sessions |
|:---------------------------------------------|---------------:|--------------------:|
| search_for_device                            |         302119 |               37884 |
| pageview                                     |         258948 |               72301 |
| load_more_device_home                        |         180502 |               56178 |
| select_device_for_comparison                 |          29579 |                8557 |
| add_to_comparison                            |           6298 |                4740 |
| comparison_chart_sort_selection              |           3519 |                1339 |
| user_login                                   |            590 |                 289 |
| comparison_chart_geekbench_version_selection |            125 |                  34 |

### page_name (trong pageview)

| page_name            |   total_events |
|:---------------------|---------------:|
| Home                 |         122574 |
| DeviceDetail         |         108508 |
| DeviceComparisonHome |          18181 |
| DeviceComparison     |           9685 |

**Kết luận:** không có event_name hoặc page_name nào tương ứng với 'xem video review' -> thành phần này không có dữ liệu tracking, sẽ bị loại khỏi interest_score.

## [Giai đoạn 3 - 0.4] Quyết định cuối cùng — interest_score'

Containment ratio: select_device_for_comparison = 78.3%, add_to_comparison = 27.4%
-> select_device_for_comparison đại diện đúng cho hành động đưa máy vào bảng so sánh.

**Công thức CHÍNH THỨC (thay thế interest_score gốc ở Giai đoạn 1):**

    interest_score' = 1 × (số pageview DeviceDetail) + 2 × (số lần select_device_for_comparison)

Thay đổi so với gốc: (1) bỏ thành phần video review — không có dữ liệu tracking;
(2) dùng select_device_for_comparison, KHÔNG dùng add_to_comparison cho thành phần "So sánh".

**Giới hạn:** containment 78.3% nghĩa là ~21.7% thiết bị trong bảng
so sánh không khớp lần select gần nhất cùng session (có thể do độ trễ, do người dùng xóa bớt máy
trước khi sort). interest_score' là ước lượng, không phải phép đo tuyệt đối chính xác.
add_to_comparison (6.224 sự kiện) chưa rõ là hành động gì, không dùng ở đây, ghi vào backlog.

## [Giai đoạn 3 - Trục 1] H1' — Kết quả

Mann-Whitney battery_density (Gaming vs Văn phòng): {'n1': 47, 'n2': 80, 'median1': np.float64(0.0368852459016393), 'median2': np.float64(0.04769012082444915), 'u_stat': np.float64(779.0), 'p_value': np.float64(3.888769417046849e-08), 'effect_size_r': np.float64(0.5856)}

**Diễn giải:** median battery_density của gaming (0.0369) thấp hơn
văn phòng (0.0477), effect size r=0.5856
(khá lớn) -> xác nhận trade-off: laptop gaming thường nặng hơn so với dung lượng pin.

**Giới hạn:** battery_density đo dung lượng pin DANH ĐỊNH/trọng lượng, không phải hiệu năng
pin thực tế khi sử dụng (xem thêm mục Pivot bên dưới).

## [Giai đoạn 3 - Pivot] office_battery_per_whr không khả dụng -> chuyển sang battery_density

**Phát hiện:** trên analysis_base.csv (133 laptop, population đã lọc sạch),
office_battery_result_minutes chỉ có 1/133 dòng có dữ liệu
(99.2% NULL), kéo theo office_battery_per_whr
cũng chỉ có 1/133 dòng. battery_density (dựa trên battery_capacity_whr từ
laptop_model, KHÔNG phụ thuộc benchmark) có độ phủ tốt: 127/133
(95.5%).

**Quyết định:** thay office_battery_per_whr bằng battery_density cho cả Golden Ratio (H1')
và H9, áp dụng nguyên tắc tương tự lần pivot H1 -> H1' ở Giai đoạn 2.

**Giới hạn:** battery_density đo dung lượng pin DANH ĐỊNH/trọng lượng — KHÔNG phải hiệu suất
sử dụng điện thực tế. Insight rút ra phản ánh trade-off THIẾT KẾ, không phải HIỆU NĂNG PIN THỰC TẾ.

office_battery_result_minutes chỉ có 1 dòng -> KHÔNG đủ để chạy kiểm định thống kê
(kể cả Spearman H8 backlog). H8 coi như không khả thi, loại khỏi phạm vi.

## [Giai đoạn 3 - Trục 1] Golden Ratio' — Kết quả

Số laptop thuộc nhóm Golden Ratio' (top 25% battery_density + top 25% nhẹ nhất): 24
Danh sách: cột golden_group trong data/processed/dashboard_laptop.csv

## [Giai đoạn 3 - Trục 2] H5 — Kết quả

Mann-Whitney interest_score (Gaming vs Văn phòng): {'n1': 47, 'n2': 86, 'median1': np.float64(643.0), 'median2': np.float64(990.0), 'u_stat': np.float64(1480.5), 'p_value': np.float64(0.01102879890824362), 'effect_size_r': np.float64(0.2674)}

Kiểm tra biến nhiễu year_introduce theo phân khúc:
| is_gaming_laptop   |    mean |   median |   count |
|:-------------------|--------:|---------:|--------:|
| False              | 2024.62 |     2025 |      86 |
| True               | 2024.45 |     2024 |      47 |

**Diễn giải:** nếu 2 nhóm lệch nhau đáng kể về year_introduce, khác biệt interest_score
có thể do laptop mới ra mắt được xem nhiều hơn (recency bias) chứ không thuần do phân khúc gaming.
Cần nêu rõ giới hạn này khi trình bày insight, correlation != causation.

## [Giai đoạn 3 - Trục 2] Đính chính chiều kết quả H5

H5 gốc giả thuyết: "laptop gaming nhận nhiều interest_score hơn laptop văn phòng".
Kết quả thực tế: median interest_score của gaming (643.0) THẤP HƠN
văn phòng (990.0), khác biệt có ý nghĩa thống kê (p=0.0110,
effect size r=0.2674).

**Kết luận: bác bỏ giả thuyết H5 gốc theo đúng chiều đã đề ra — chiều thực tế NGƯỢC LẠI.**
Đây vẫn là một insight có giá trị (người dùng thực ra quan tâm/so sánh laptop văn phòng nhiều
hơn gaming), nhưng cần trình bày đúng bản chất ở Giai đoạn 4/6, không diễn đạt nhầm thành
"xác nhận gaming được quan tâm hơn".

## [Giai đoạn 3 - Trục 3] Đính chính: H9' không hoàn toàn độc lập với H1'

Kiểm tra density_percentile_within_gaming của 5 laptop trong nhóm H9':
- Lenovo LOQ 15ARP9 83JC0000US: percentile 8.5% trong nhóm gaming -> outlier THẬT (độc lập với H1')
- ASUS Gaming VivoBook K3605ZF-RP634W: percentile 23.4% -> outlier THẬT (độc lập với H1')
- Lenovo LOQ 15IAX9: percentile 29.8% -> hơi thấp, không rõ ràng
- Lenovo Legion Slim 5 16AHP9: percentile 46.8% -> BÌNH THƯỜNG trong nhóm gaming
- ASUS ROG Strix G16: percentile 48.9% -> BÌNH THƯỜNG trong nhóm gaming

**Kết luận:** H9' (dùng ngưỡng percentile trên TOÀN population) là hỗn hợp 2 hiệu ứng:
(1) hệ quả trực tiếp của H1' — gaming vốn có battery_density thấp hơn văn phòng nói chung,
nên dễ lọt vào "bottom 25% toàn population" dù bản thân không bất thường trong phân khúc gaming
(trường hợp Legion Slim 5, ROG Strix G16); (2) tín hiệu ĐỘC LẬP thật — 2/5 laptop
(Lenovo LOQ 15ARP9, ASUS VivoBook K3605ZF) có battery_density thấp bất thường NGAY CẢ so với
riêng phân khúc gaming, đây mới là phát hiện content/affiliate đáng giá nhất.

**Khuyến nghị cho Giai đoạn 4:** khi viết insight, nêu 2 laptop outlier thật (LOQ 15ARP9,
VivoBook K3605ZF) làm ví dụ chính cho "cơ hội cảnh báo nội dung", KHÔNG trình bày cả 5 laptop
như bằng chứng ngang hàng, để tránh overclaim. Có thể nhắc ngắn gọn 3 laptop còn lại là phản ánh
xu hướng chung của H1' hơn là phát hiện riêng.

## [Giai đoạn 3 - Trục 3] H9' — Kết quả

Số laptop 'click nhiều nhưng battery_density kém' (ngưỡng 25/75): 5
Danh sách: cột h9_quadrant/opportunity_type trong data/processed/dashboard_laptop.csv

Sensitivity check theo ngưỡng percentile:
|   percentile_threshold |   n_laptops_flagged |
|-----------------------:|--------------------:|
|                   0.2  |                   2 |
|                   0.25 |                   5 |
|                   0.3  |                   9 |

Lưu ý: H8 (backlog, Spearman office_battery_result_minutes vs interest_score) bị loại khỏi
phạm vi phân tích do office_battery_result_minutes chỉ có n=1 dòng dữ liệu (xem quyết định
pivot ở notebook 02) — không đủ điều kiện chạy bất kỳ kiểm định thống kê nào.

## [Giai đoạn 3] Tổng kết

Đã hoàn thành kiểm định cho 3 insight chính: H1' (Trục 1), H5 (Trục 2), H9 (Trục 3).
Mỗi kiểm định đều có effect size + p-value, ghi chú correlation != causation, và phần rủi ro/giới hạn.
Output: data/processed/dashboard_laptop.csv (golden_group, h9_quadrant),
reports/figures/*.png. Sẵn sàng chuyển sang Giai đoạn 4: đúc kết insight & đề xuất kinh doanh.

## [Giai đoạn 4] Đúc kết insight & đề xuất kinh doanh

Đã hoàn thành reports/insight_summary.md với 3 insight chính, mỗi insight có: pattern (dựa
đúng kết quả thống kê Giai đoạn 3, đã đính chính chiều H5 và tách bạch H9'), biểu đồ minh họa
nhúng trực tiếp, quyết định kinh doanh theo từng đơn vị (đối chiếu bảng bối cảnh mục 1.1),
ước tính tác động có công thức/giả định rõ ràng, và phần rủi ro/giới hạn.

Bảng ánh xạ Insight -> Đơn vị:
- Insight 1 (Golden Ratio ultrabook) -> Nội dung/Review (chính), Sản phẩm/UX (liên quan)
- Insight 2 (Văn phòng > Gaming interest, NGƯỢC giả thuyết ban đầu) -> Sản phẩm/UX (chính), Affiliate (liên quan)
- Insight 3 (2 model gaming hot nhưng pin kém) -> Nội dung/Review (chính), Affiliate (liên quan)

Đã bổ sung ghi chú đạo đức dữ liệu: mọi số liệu trong insight_summary.md đều đã tổng hợp theo
laptop_model_id, không xuất user_psuedo_id/session_id gốc ra báo cáo.

Output: reports/insight_summary.md (kèm ảnh từ reports/figures/). Sẵn sàng chuyển sang
Giai đoạn 5 (Dashboard) và Giai đoạn 6 (Deliverable & Documentation chuẩn cho CV).

## [Giai đoạn 5 - Trang 2] Ghi chú độ khả dụng dữ liệu

CPU_Battery_Ratio: chỉ 3 dòng đủ dữ liệu Geekbench -> KHÔNG dùng làm biểu đồ
chính (không xuất file). Thay thế: dashboard_battery_density_by_cpu.csv, độ phủ tốt
hơn nhiều, dùng cùng Scatter Trọng lượng vs Battery Density đã có trong analysis_base.csv.

## [Giai đoạn 5 - Trang 3] Kết luận chính thức về hiện tượng "Xem chi tiết" > "Tìm kiếm"

16394 session (36.7%) xem chi tiết KHÔNG qua tìm kiếm trước.
Trong nhóm này, 53.9% có bằng chứng đã duyệt qua Home/load_more_device_home —
MỘT PHẦN nguyên nhân, không phải toàn bộ (phần còn lại chưa xác định rõ nguồn gốc).

**Kết luận:** "Tìm kiếm -> Xem chi tiết -> Chọn So sánh" KHÔNG phải phễu chuyển đổi tuần tự bắt
buộc. Quyết định: Trang 3 dùng Bar chart "Mức độ tham gia theo từng hành động" thay vì Funnel
visual chuẩn (vốn ngụ ý quan hệ tập con giảm dần), kèm chú thích đúng mức độ bằng chứng.

## [Giai đoạn 5 - Trang 3] Ghi chú công thức funnel

Đếm số session PHÂN BIỆT có event tương ứng, không bắt buộc thứ tự thời gian trong cùng session.
Endpoint đổi từ "click video review" (kế hoạch gốc) sang "select_device_for_comparison", do
không có dữ liệu tracking cho hành vi xem video (xác nhận ở Giai đoạn 3).

## [Giai đoạn 5] Data Dictionary cho Dashboard

| Metric hiển thị | Nguồn file | Công thức/Định nghĩa |
|---|---|---|
| Total Active Users | dashboard_overview_kpi.csv | COUNT(DISTINCT user_psuedo_id) |
| Total Sessions | dashboard_overview_kpi.csv | COUNT(DISTINCT session_id) |
| Interest Score | dashboard_laptop.csv (cột interest_score) | 1*pageview(DeviceDetail) + 2*select_device_for_comparison |
| Battery Density | dashboard_laptop.csv (cột density_wh_kg) | battery_wh / weight_kg (Wh/kg) |
| Golden Ratio Group | dashboard_laptop.csv (cột golden_group) | Top 25% battery_density + top 25% nhẹ nhất |
| Discovery Path | dashboard_discovery_path.csv | Tỷ trọng session theo nguồn vào trang chi tiết (Search-led/Browse-confirmed/Unknown) |
| Data Quality % Null | dashboard_data_quality_history.csv | Tỷ lệ NULL theo cột, 1 snapshot/ngày |

## [Giai đoạn 5] Quyết định Data Refresh & Schema Change

Refresh: chạy lại notebook 01->05, sau đó Refresh All trong Power BI. Không có lịch tự động.
Schema đổi: get_schema() ở notebook 01 sẽ báo lỗi sớm; detect_contaminated_devices() tự thích
ứng dữ liệu mới, không hardcode ID.

## [Giai đoạn 5] Tổng kết

Đã chuẩn bị đầy đủ dữ liệu nguồn cho Power BI: dashboard_overview_kpi.csv,
dashboard_battery_density_by_cpu.csv (dùng chính), dashboard_data_quality_history.csv.

Phát hiện quan trọng trong quá trình chuẩn bị: "funnel" Tìm kiếm->Xem chi tiết->Chọn So sánh
KHÔNG phải phễu tuần tự (36.7% xem chi tiết không qua tìm kiếm), đã đổi cách trình bày trang 3
từ Funnel visual sang Bar chart "Mức độ tham gia", tránh gây hiểu lầm.

Output đã sẵn sàng để dựng laplaptech_dashboard.pbix (4 trang: Overview, Hardware Benchmark
Matrix, User Engagement, Data Quality Monitor). Sẵn sàng hoàn tất Giai đoạn 6 (6.3 One-pager,
6.4 Publish Dashboard) sau khi hoàn thành thao tác thủ công trên Power BI.
