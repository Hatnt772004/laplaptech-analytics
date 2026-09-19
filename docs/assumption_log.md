# Assumption Log — Mục lục

Toàn bộ assumption log chi tiết được ghi trực tiếp vào `docs/project_notes.md` theo thời gian
thực trong lúc phân tích (dùng hàm `append_note()`), để giữ liền mạch giữa code và quyết định.
File này là mục lục điều hướng nhanh tới các quyết định quan trọng nhất.

## Các quyết định pivot quan trọng

| Quyết định | Lý do | Vị trí trong project_notes.md |
|---|---|---|
| H1 → H1' (bỏ CPU_Battery_Ratio) | laptop_benchmark_result chỉ 3/157 dòng đủ Geekbench | Mục "[Giai đoạn 2]" |
| Loại laptop_catalog khỏi phân tích | Phát hiện collision/fanout khi match tên | Mục "[Giai đoạn 0] Quyết định CUỐI CÙNG về laptop_catalog" |
| Loại 24 thiết bị nhiễm (không phải laptop) | Lẫn iPad/iPhone vào laptop_model | Mục "[Giai đoạn 2 - 2.3.4]" |
| interest_score': bỏ thành phần video | Không có event/page_name cho video review | Mục "[Giai đoạn 3 - 0]" |
| interest_score': chọn select_device_for_comparison, không dùng add_to_comparison | Containment 78.3% vs 27.5% | Mục "[Giai đoạn 3 - 0.4]" |
| Golden Ratio/H9 → dùng battery_density | office_battery_result_minutes chỉ 1/135 dòng | Mục "[Giai đoạn 3 - Pivot]" |
| H5: đính chính chiều kết quả | Kết quả ngược giả thuyết ban đầu | Mục "[Giai đoạn 3 - Trục 2] Đính chính" |
| H9': tách 2/5 laptop là tín hiệu thật | Confound với H1' | Mục "[Giai đoạn 3 - Trục 3] Đính chính" |

Xem toàn văn từng quyết định (bối cảnh điều tra, số liệu, code liên quan) trực tiếp trong
`docs/project_notes.md`.