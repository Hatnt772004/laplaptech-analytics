"""
src/cleaning.py — Các hàm làm sạch dữ liệu dùng chung cho Giai đoạn 2.
"""
import re
import numpy as np
import pandas as pd
from scipy.stats import skew as scipy_skew
import json

# ── 2.1 Data Profiling ──────────────────────────────────────────────
def profile_column(df: pd.DataFrame, col: str) -> dict:
    """Trả về % null, min/max, số outlier (IQR), độ lệch (skew) cho 1 cột số."""
    s = pd.to_numeric(df[col], errors="coerce")
    null_pct = s.isna().mean()
    valid = s.dropna()
    if len(valid) == 0:
        return {"column": col, "null_pct": null_pct, "min": None, "max": None,
                "outlier_count": None, "skew": None}
    q1, q3 = valid.quantile(0.25), valid.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outlier_count = ((valid < lower) | (valid > upper)).sum()
    return {
        "column": col, "null_pct": round(null_pct, 4),
        "min": valid.min(), "max": valid.max(),
        "outlier_count": int(outlier_count),
        "skew": round(float(scipy_skew(valid)), 3),
    }


def profile_dataframe(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Chạy profile_column cho danh sách cột, trả về 1 bảng tổng hợp."""
    return pd.DataFrame([profile_column(df, c) for c in columns])


# ── 2.2.1 Parse cpu_tdp / gpu_tdp (String -> số) ────────────────────
def parse_tdp(raw: str) -> float:
    """
    Chuyển chuỗi TDP dạng '45W', '15-28W', '15 W' thành số (float).
    Với dải giá trị (VD '15-28W'), lấy TRUNG BÌNH của dải (quyết định ghi trong assumption log).
    Trả về np.nan nếu không parse được hoặc input rỗng.
    """
    if pd.isna(raw) or str(raw).strip() == "":
        return np.nan
    s = str(raw).lower().replace(" ", "").replace("w", "")
    numbers = re.findall(r"\d+\.?\d*", s)
    if not numbers:
        return np.nan
    numbers = [float(n) for n in numbers]
    return sum(numbers) / len(numbers)  # 1 số -> chính nó; 2 số (dải) -> trung bình


def parse_tdp_column(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col].apply(parse_tdp)


# ── 2.3.1 Ngưỡng outlier vật lý ──────────────────────────────────────
def flag_physical_outliers(df: pd.DataFrame, col: str, max_valid: float) -> pd.DataFrame:
    """
    Gắn cờ (không xóa) các dòng vượt ngưỡng vật lý hợp lý.
    Trả về bảng con các dòng bị flag, để đưa vào bảng 'anomaly' riêng.
    """
    s = pd.to_numeric(df[col], errors="coerce")
    flagged = df[s > max_valid].copy()
    flagged["anomaly_type"] = f"{col}_exceeds_physical_limit"
    flagged["anomaly_value"] = s[s > max_valid]
    flagged["anomaly_threshold"] = max_valid
    return flagged


# ── 2.3.2 Rule phân biệt NULL "chưa test" vs "không áp dụng" ────────
def classify_null_reason(df: pd.DataFrame, target_col: str,
                          gaming_col: str = "is_gaming_laptop",
                          workstation_col: str = "is_workstation") -> pd.Series:
    """
    Với các dòng NULL ở target_col (VD gaming_battery_result_minutes):
    - is_workstation = True  -> 'not_applicable' (máy không định hướng gaming, không test)
    - is_gaming_laptop = True -> 'missing_test' (nhiều khả năng chưa test, cần loại khỏi mẫu)
    - còn lại -> 'unclear' (cần rà thủ công)
    Trả về Series cùng index với df, chỉ có giá trị ở các dòng NULL, các dòng còn lại là 'not_null'.
    """
    is_null = df[target_col].isna()
    reason = pd.Series("not_null", index=df.index)
    reason[is_null & (df[workstation_col] == True)] = "not_applicable"
    reason[is_null & (df[gaming_col] == True)] = "missing_test"
    reason[is_null & (df[workstation_col] != True) & (df[gaming_col] != True)] = "unclear"
    return reason


# ── 2.5.1 / 2.5.3 Event tracking ─────────────────────────────────────
def build_session_journey(df_events: pd.DataFrame,
                           session_col: str = "session_id",
                           ts_col: str = "event_local_timestamp") -> pd.DataFrame:
    """
    Sắp xếp sự kiện trong cùng 1 session theo thời gian, đánh số thứ tự bước (step).
    df_events cần có: session_col, ts_col, event_name, và các cột đã JSON_EXTRACT khác.
    """
    df = df_events.sort_values([session_col, ts_col]).copy()
    df["step_in_session"] = df.groupby(session_col).cumcount() + 1
    return df

def inventory_json_keys(df: pd.DataFrame, json_col: str,
                         event_name_col: str = "event_name",
                         version_col: str = "app_version") -> pd.DataFrame:
    """
    Liệt kê toàn bộ key xuất hiện trong cột JSON, nhóm theo event_name + app_version.
    Giúp phát hiện key bị đổi tên/thiếu giữa các phiên bản app.
    Trả về bảng: event_name | app_version | keys_found | n_rows
    """
    records = []
    for (event_name, version), group in df.groupby([event_name_col, version_col]):
        keys_in_group = set()
        for raw in group[json_col].dropna():
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    keys_in_group.update(parsed.keys())
            except (json.JSONDecodeError, TypeError):
                continue
        records.append({
            "event_name": event_name, "app_version": version,
            "keys_found": sorted(keys_in_group), "n_rows": len(group),
        })
    return pd.DataFrame(records)


def find_key_inconsistencies(df_inventory: pd.DataFrame) -> pd.DataFrame:
    """
    Với mỗi event_name, so sánh tập key giữa các app_version.
    Trả về các event_name có key KHÔNG đồng nhất giữa các version (nghi ngờ đổi tên/thiếu key).
    """
    issues = []
    for event_name, group in df_inventory.groupby("event_name"):
        key_sets = [set(k) for k in group["keys_found"]]
        union_keys = set.union(*key_sets) if key_sets else set()
        intersection_keys = set.intersection(*key_sets) if key_sets else set()
        if union_keys != intersection_keys:
            issues.append({
                "event_name": event_name,
                "keys_common_all_versions": sorted(intersection_keys),
                "keys_inconsistent": sorted(union_keys - intersection_keys),
                "n_versions": len(group),
            })
    return pd.DataFrame(issues)

def detect_contaminated_devices(df_laptop: pd.DataFrame,
                                  name_col: str = "name",
                                  weight_col: str = "laptop_weight",
                                  id_col: str = "id",
                                  min_weight_g: float = 700,
                                  max_weight_g: float = 6000) -> list:
    """
    Phát hiện các dòng không phải laptop trong laptop_model, dùng 2 quy tắc độc lập:
    (1) tên gọi chứa từ khóa iPhone/iPad/dòng test...
    (2) trọng lượng nằm ngoài khoảng hợp lý của laptop.
    """
    pattern = (r"\b(?:iphone|ipad|tablet|test|dummy)\b|\bphone\b"
           r"|galaxy\s+(?:s\d|z\b|a\d|tab|note)|thử|mới test")
    suspects_by_name = df_laptop[
        df_laptop[name_col].str.lower().str.contains(pattern, na=False, regex=True)
    ][id_col].tolist()

    weight_g = normalize_laptop_weight(df_laptop, weight_col=weight_col)
    implausible = df_laptop[(weight_g < min_weight_g) | (weight_g > max_weight_g)]
    suspects_by_weight = implausible[id_col].tolist()

    return sorted(set(suspects_by_name + suspects_by_weight) & set(df_laptop[id_col]))


def filter_non_laptop_devices(df: pd.DataFrame, id_col: str = "id",
                                name_col: str = "name", weight_col: str = "laptop_weight") -> pd.DataFrame:
    """
    Loại bỏ thiết bị không phải laptop thật, phát hiện LẠI mỗi lần gọi (không dùng danh sách
    ID cứng), để tự thích ứng với dữ liệu mới khi bảng nguồn được cập nhật.
    """
    contaminated_ids = detect_contaminated_devices(df, name_col=name_col, weight_col=weight_col, id_col=id_col)
    return df[~df[id_col].isin(contaminated_ids)].copy()


def normalize_laptop_weight(df: pd.DataFrame, weight_col: str = "laptop_weight") -> pd.Series:
    """
    Chuẩn hóa laptop_weight về đơn vị gram. Một số dòng bị ghi nhầm đơn vị kg (giá trị < 10).
    Phát hiện ở Giai đoạn 2: 5 dòng laptop thật bị lỗi đơn vị này.
    """
    raw = pd.to_numeric(df[weight_col], errors="coerce")
    mask_kg = raw < 10
    return raw.where(~mask_kg, raw * 1000)


# ── Giai đoạn 3/5 — Chuẩn hóa cột output cuối cùng (tránh rò rỉ cột thô từ SELECT *) ──
REPORT_CORE_COLUMNS = [
    "id", "name", "brand_id", "cpu_model_id", "gpu_model_id",
    "is_gaming_laptop", "is_workstation", "year_introduce",
    "battery_capacity_whr", "laptop_weight_g", "cpu_tdp_parsed", "gpu_tdp_parsed",
    "battery_density", "office_battery_result_minutes", "office_battery_per_whr",
    "cpu_battery_ratio", "pageview_count", "compare_count", "interest_score",
]

def select_report_columns(df: pd.DataFrame, extra_cols: list = None) -> pd.DataFrame:
    """
    Chọn lọc cột chuẩn cho các file output cuối cùng (dùng cho Power BI/báo cáo),
    loại bỏ cột nghiệp vụ thô từ SELECT * (created_on, cpu_note, thumbnail_image_url...)
    và cột trùng do merge (laptop_model_id_x/_y). Chỉ giữ cột có thật trong df để tránh lỗi
    KeyError nếu một số cột phái sinh chưa được tính ở bước gọi hàm.
    """
    cols = REPORT_CORE_COLUMNS + (extra_cols or [])
    cols_present = [c for c in cols if c in df.columns]
    missing = set(cols) - set(cols_present)
    if missing:
        print(f"[select_report_columns] Cảnh báo: các cột sau không có trong df, đã bỏ qua: {missing}")
    return df[cols_present].copy()