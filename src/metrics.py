"""
src/metrics.py — Các hàm tính chỉ số/metric dùng chung.
Giai đoạn 2 dùng cho CPU_Battery_Ratio và các chỉ số phái sinh từ laptop_benchmark_result/laptop_model.
"""
import numpy as np
import pandas as pd

def compute_cpu_battery_ratio(df: pd.DataFrame,
                               battery_col: str = "geekbench_6_cpu_multi_core_battery",
                               plugged_col: str = "geekbench_6_cpu_multi_core_plugged_in") -> pd.Series:
    """
    CPU_Battery_Ratio = điểm khi dùng pin / điểm khi cắm điện.
    Trả về np.nan nếu plugged_col = 0 hoặc NULL (tránh chia cho 0).
    """
    battery = pd.to_numeric(df[battery_col], errors="coerce")
    plugged = pd.to_numeric(df[plugged_col], errors="coerce")
    ratio = battery / plugged.replace(0, np.nan)
    return ratio

def compute_battery_density(df: pd.DataFrame,
                             capacity_col: str = "battery_capacity_whr",
                             weight_col: str = "laptop_weight") -> pd.Series:
    """Mật độ pin / trọng lượng = battery_capacity_whr / laptop_weight."""
    capacity = pd.to_numeric(df[capacity_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    return capacity / weight.replace(0, np.nan)

def compute_office_battery_per_whr(df: pd.DataFrame,
                                    minutes_col: str = "office_battery_result_minutes",
                                    capacity_col: str = "battery_capacity_whr") -> pd.Series:
    """Thời lượng pin thực tế / Whr — đánh giá khả năng tối ưu điện năng."""
    minutes = pd.to_numeric(df[minutes_col], errors="coerce")
    capacity = pd.to_numeric(df[capacity_col], errors="coerce")
    return minutes / capacity.replace(0, np.nan) 

# ── Giai đoạn 3 — Hàm kiểm định thống kê dùng chung ──────────────────
from scipy.stats import mannwhitneyu, spearmanr

def mann_whitney_with_effect_size(group1: pd.Series, group2: pd.Series) -> dict:
    """
    Chạy Mann-Whitney U test + effect size (rank-biserial correlation).
    r gần 0 -> khác biệt nhỏ, r gần ±1 -> khác biệt lớn. Tự loại NaN.
    """
    g1 = pd.to_numeric(group1, errors="coerce").dropna()
    g2 = pd.to_numeric(group2, errors="coerce").dropna()
    if len(g1) == 0 or len(g2) == 0:
        return {"n1": len(g1), "n2": len(g2), "u_stat": None, "p_value": None, "effect_size_r": None}
    u_stat, p_value = mannwhitneyu(g1, g2, alternative="two-sided")
    # rank-biserial effect size
    r = 1 - (2 * u_stat) / (len(g1) * len(g2))
    return {
        "n1": len(g1), "n2": len(g2), "median1": g1.median(), "median2": g2.median(),
        "u_stat": u_stat, "p_value": p_value, "effect_size_r": round(r, 4),
    }


def spearman_with_note(x: pd.Series, y: pd.Series) -> dict:
    """Spearman correlation, tự loại NaN theo cặp, kèm ghi chú correlation != causation."""
    df_tmp = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(df_tmp) < 3:
        return {"n": len(df_tmp), "rho": None, "p_value": None}
    rho, p_value = spearmanr(df_tmp["x"], df_tmp["y"])
    return {"n": len(df_tmp), "rho": round(rho, 4), "p_value": p_value,
            "note": "Correlation không suy ra nhân quả (correlation != causation)."}


def percentile_quadrant(df: pd.DataFrame, col_x: str, col_y: str,
                         upper_pct: float = 0.75, lower_pct: float = 0.25) -> pd.DataFrame:
    """
    Gắn nhãn từng dòng vào 1 trong 4 nhóm percentile dựa trên col_x, col_y:
    'top_x_top_y', 'top_x_bottom_y', 'bottom_x_top_y', 'bottom_x_bottom_y', 'middle'.
    Dùng cho H1' (Golden Ratio) và H9 (click nhiều nhưng benchmark kém).
    """
    x = pd.to_numeric(df[col_x], errors="coerce")
    y = pd.to_numeric(df[col_y], errors="coerce")
    x_hi, x_lo = x.quantile(upper_pct), x.quantile(lower_pct)
    y_hi, y_lo = y.quantile(upper_pct), y.quantile(lower_pct)

    labels = pd.Series("middle", index=df.index)
    labels[(x >= x_hi) & (y >= y_hi)] = "top_x_top_y"
    labels[(x >= x_hi) & (y <= y_lo)] = "top_x_bottom_y"
    labels[(x <= x_lo) & (y >= y_hi)] = "bottom_x_top_y"
    labels[(x <= x_lo) & (y <= y_lo)] = "bottom_x_bottom_y"
    return labels