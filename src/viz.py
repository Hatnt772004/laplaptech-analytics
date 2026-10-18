"""
src/viz.py — Hàm vẽ chart dùng chung cho các notebook EDA (Giai đoạn 3).
"""
import matplotlib.pyplot as plt
import seaborn as sns

def save_fig(fig, filename: str, fig_dir: str = "../reports/figures"):
    """Lưu chart ra reports/figures/, dùng chung filename cho mọi notebook."""
    import os
    os.makedirs(fig_dir, exist_ok=True)
    path = os.path.join(fig_dir, filename)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    print(f"Đã lưu: {path}")
    return path


def plot_group_boxplot(df, group_col: str, value_col: str, title: str, filename: str):
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(data=df, x=group_col, y=value_col, ax=ax)
    ax.set_title(title)
    save_fig(fig, filename)
    plt.show()
    plt.close(fig)


def plot_quadrant_scatter(df, x_col: str, y_col: str, label_col: str, title: str, filename: str, x_lines=None, y_lines=None):
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(data=df, x=x_col, y=y_col, hue=label_col, ax=ax, alpha=0.7)
    for v in (x_lines if x_lines is not None else [df[x_col].median()]):
        ax.axvline(v, color="gray", linestyle="--", linewidth=0.8)
    for v in (y_lines if y_lines is not None else [df[y_col].median()]):
        ax.axhline(v, color="gray", linestyle="--", linewidth=0.8)
    ax.legend(title=None, fontsize=8)
    ax.set_title(title)
    save_fig(fig, filename)
    plt.show()
    plt.close(fig)