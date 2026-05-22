"""
Nature 风格可视化 — matplotlib 出版级图表
参考 Nature 期刊规范：无多余边框、科学配色、Arial 字体、高清输出
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd
import os
from io import BytesIO
from typing import Dict, List, Optional
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from config import COLORS

# ============================================================
# 中文字体注册（Windows）
# ============================================================
def _register_chinese_fonts():
    """将系统常用中文字体注册到 matplotlib"""
    font_candidates = [
        "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑 Bold
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
        "C:/Windows/Fonts/simkai.ttf",     # 楷体
    ]
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                fm.fontManager.addfont(fp)
            except Exception:
                pass

_register_chinese_fonts()

# ============================================================
# Nature 期刊全局样式
# ============================================================
NATURE_COLORS = COLORS["nature_palette"]

plt.rcParams.update({
    # 字体 — 中文优先
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.unicode_minus": False,

    # 边框 — Nature 风格：无顶/右边框
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,

    # 网格
    "axes.grid": False,

    # 线条与标记
    "lines.linewidth": 1.5,
    "lines.markersize": 5,
    "lines.markeredgewidth": 0.5,

    # 图例
    "legend.frameon": False,
    "legend.loc": "best",

    # 输出
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "savefig.format": "png",

    # 色板
    "axes.prop_cycle": plt.cycler(color=NATURE_COLORS),
})

FIG_SIZE = (6, 4)
FIG_SIZE_WIDE = (8, 4)


# ============================================================
# 工具函数
# ============================================================
def _fig_to_bytes(fig: plt.Figure, fmt: str = "png", dpi: int = 300) -> bytes:
    """将 Figure 转为字节流"""
    buf = BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return buf.read()


def _apply_nature_style(ax: plt.Axes):
    """对单个 Axes 应用 Nature 风格微调"""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=4, width=0.8)


# ============================================================
# 数据探索图
# ============================================================

def plot_distribution(df: pd.DataFrame, column: str) -> plt.Figure:
    """直方图 + KDE 密度曲线"""
    data = df[column].dropna()
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    ax.hist(data, bins="auto", density=True, alpha=0.6, color=NATURE_COLORS[0],
            edgecolor="white", linewidth=0.5)
    # KDE
    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(data)
        x_range = np.linspace(data.min(), data.max(), 200)
        ax.plot(x_range, kde(x_range), color=NATURE_COLORS[1], linewidth=2)
    except Exception:
        pass

    ax.set_xlabel(column)
    ax.set_ylabel("密度")
    ax.set_title(f"{column} 分布")
    _apply_nature_style(ax)
    return fig


def plot_boxplot(df: pd.DataFrame, columns: List[str]) -> plt.Figure:
    """多列箱线图"""
    data = df[columns].dropna()
    if data.empty:
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        ax.text(0.5, 0.5, "无数值列", ha="center", va="center")
        return fig

    fig, ax = plt.subplots(figsize=(max(5, len(columns) * 1.2), 4))
    bp = ax.boxplot(
        [data[c].dropna() for c in columns],
        patch_artist=True,
        widths=0.5,
        medianprops={"color": "black", "linewidth": 1},
        flierprops={"marker": "o", "markersize": 3, "markerfacecolor": NATURE_COLORS[1]},
    )
    for patch, color in zip(bp["boxes"], NATURE_COLORS[:len(columns)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)

    ax.set_xticklabels(columns, rotation=30, ha="right")
    ax.set_ylabel("数值")
    _apply_nature_style(ax)
    return fig


def plot_correlation_heatmap(df: pd.DataFrame) -> plt.Figure:
    """相关性热力图"""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        ax.text(0.5, 0.5, "需要至少2个数值列", ha="center", va="center")
        return fig

    corr = numeric_df.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

    fig, ax = plt.subplots(figsize=(max(5, len(corr) * 0.9), max(4, len(corr) * 0.7)))
    cmap = sns.diverging_palette(250, 15, s=75, l=40, n=12, center="light")
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f", cmap=cmap,
        vmin=-1, vmax=1, square=True, linewidths=0.5,
        cbar_kws={"shrink": 0.8, "label": "相关系数"},
        ax=ax,
    )
    ax.set_title("特征相关性热力图")
    return fig


# ============================================================
# 模型结果图
# ============================================================

def plot_regression_fit(y_true: np.ndarray, y_pred: np.ndarray) -> plt.Figure:
    """回归：真实值 vs 预测值散点图"""
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    r2 = 1 - np.sum((y_true - y_pred) ** 2) / np.sum((y_true - y_true.mean()) ** 2)
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]

    ax.scatter(y_true, y_pred, alpha=0.5, s=20, color=NATURE_COLORS[0], edgecolors="none")
    ax.plot(lims, lims, "--", color=NATURE_COLORS[1], linewidth=1.2, label="完美预测线")
    ax.set_xlabel("真实值")
    ax.set_ylabel("预测值")
    ax.set_title(f"回归拟合效果 (R² = {r2:.3f})")
    ax.legend()
    _apply_nature_style(ax)
    return fig


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray) -> plt.Figure:
    """回归：残差图"""
    residuals = y_true - y_pred
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    ax.scatter(y_pred, residuals, alpha=0.5, s=20, color=NATURE_COLORS[2], edgecolors="none")
    ax.axhline(0, linestyle="--", color=NATURE_COLORS[1], linewidth=1.2)
    ax.set_xlabel("预测值")
    ax.set_ylabel("残差（真实值 - 预测值）")
    ax.set_title("残差分布图")
    _apply_nature_style(ax)
    return fig


def plot_feature_importance(features: List[tuple], top_n: int = 10) -> plt.Figure:
    """特征重要性水平条形图"""
    features = features[:top_n]
    names = [f[0] for f in features][::-1]
    values = [f[1] for f in features][::-1]

    fig, ax = plt.subplots(figsize=(6, max(3, len(names) * 0.4)))
    colors = sns.color_palette("Blues_d", len(names))
    ax.barh(names, values, color=colors, edgecolor="white", height=0.6)
    ax.set_xlabel("重要性")
    ax.set_title("特征重要性排名")

    for i, v in enumerate(values):
        ax.text(v + max(values) * 0.01, i, f"{v:.3f}", va="center", fontsize=8)

    _apply_nature_style(ax)
    return fig


def plot_cluster_scatter(X: np.ndarray, labels: np.ndarray) -> plt.Figure:
    """聚类散点图（PCA 降维到 2D）"""
    # PCA 降维
    if X.shape[1] > 2:
        pca = PCA(n_components=2, random_state=42)
        X_2d = pca.fit_transform(StandardScaler().fit_transform(X))
    else:
        X_2d = X[:, :2]

    n_clusters = len(set(labels))
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    palette = sns.color_palette("Set2", n_clusters)
    for i in range(n_clusters):
        mask = labels == i
        ax.scatter(X_2d[mask, 0], X_2d[mask, 1], s=15, alpha=0.7,
                   color=palette[i], label=f"簇 {i+1}", edgecolors="none")

    ax.set_xlabel("主成分 1" if X.shape[1] > 2 else "特征 1")
    ax.set_ylabel("主成分 2" if X.shape[1] > 2 else "特征 2")
    ax.set_title(f"聚类结果 ({n_clusters} 个簇)")
    ax.legend(markerscale=2)
    _apply_nature_style(ax)
    return fig


def plot_model_comparison(results: List[dict], metric_key: str, title: str = "模型性能对比") -> plt.Figure:
    """模型性能对比柱状图"""
    valid = [r for r in results if r.get(metric_key) is not None]
    if not valid:
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        ax.text(0.5, 0.5, "无可用数据", ha="center", va="center")
        return fig

    names = [r["模型"] for r in valid]
    values = [r[metric_key] for r in valid]

    fig, ax = plt.subplots(figsize=(max(5, len(names) * 0.9), 4))
    colors = sns.color_palette("Blues_d", len(names))
    bars = ax.bar(names, values, color=colors, edgecolor="white", width=0.55)

    # 数值标签
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                f"{val:.4f}", ha="center", fontsize=8)

    ax.set_ylabel(metric_key)
    ax.set_title(title)
    ax.set_ylim(0, max(values) * 1.15)

    # 如果是 R² 或准确率，加参考线
    if metric_key in ("R²", "准确率", "F1分数"):
        ax.axhline(0.8, linestyle=":", color="gray", alpha=0.5, linewidth=0.8)

    _apply_nature_style(ax)
    return fig


# ============================================================
# 主入口：根据模型结果生成全套图表
# ============================================================

def create_figures(df: pd.DataFrame, model_result: Dict) -> Dict[str, bytes]:
    """
    根据数据 + 模型结果，生成全套 Nature 风格图表。

    返回:
        {图表名称: PNG图片字节}
    """
    figures = {}
    problem_type = model_result.get("类型", "")
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    # ----- 数据探索图（通用）-----
    if numeric_cols:
        try:
            # 第一个数值列的分布
            col0 = numeric_cols[0]
            fig = plot_distribution(df, col0)
            figures[f"分布图 - {col0}"] = _fig_to_bytes(fig)
        except Exception:
            pass

        if len(numeric_cols) >= 2:
            try:
                # 箱线图
                fig = plot_boxplot(df, numeric_cols[:6])
                figures["箱线图"] = _fig_to_bytes(fig)
            except Exception:
                pass

            try:
                # 热力图
                fig = plot_correlation_heatmap(df)
                figures["相关性热力图"] = _fig_to_bytes(fig)
            except Exception:
                pass

    # ----- 模型专属图 -----
    if problem_type == "回归分析":
        try:
            # 用最优模型重新拟合生成预测值
            from sklearn.linear_model import LinearRegression
            from sklearn.model_selection import train_test_split
            from modules.auto_model import _prepare_xy

            target_col = model_result.get("目标列")
            if target_col and target_col in df.columns:
                X, y = _prepare_xy(df, target_col)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                lr = LinearRegression()
                lr.fit(X_train, y_train)
                y_pred = lr.predict(X_test)

                fig = plot_regression_fit(y_test.values, y_pred)
                figures["回归拟合图"] = _fig_to_bytes(fig)

                fig = plot_residuals(y_test.values, y_pred)
                figures["残差图"] = _fig_to_bytes(fig)
        except Exception:
            pass

    if problem_type == "分类分析":
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split
            from modules.auto_model import _prepare_xy

            target_col = model_result.get("目标列")
            if target_col and target_col in df.columns:
                X, y = _prepare_xy(df, target_col)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                lr = LogisticRegression(max_iter=5000)
                lr.fit(X_train, y_train)
                # 分类不画拟合图，画混淆矩阵风格
                y_pred = lr.predict(X_test)
                # 保存分类报告为文本
                from sklearn.metrics import classification_report
                cr = classification_report(y_test, y_pred, output_dict=True)
                # 转化为热力图风格的 DataFrame
                cr_df = pd.DataFrame(cr).T
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.axis("off")
                table = ax.table(
                    cellText=cr_df.round(3).values[:min(5, len(cr_df))],
                    colLabels=cr_df.columns,
                    rowLabels=cr_df.index[:min(5, len(cr_df))],
                    cellLoc="center",
                    loc="center",
                )
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                ax.set_title("分类报告", fontsize=13)
                figures["分类报告"] = _fig_to_bytes(fig)
        except Exception:
            pass

    if problem_type == "聚类分析":
        try:
            labels = np.array(model_result.get("聚类标签", []))
            X = df[numeric_cols].fillna(df[numeric_cols].median()).values
            if len(labels) > 0 and len(X) == len(labels):
                fig = plot_cluster_scatter(X, labels)
                figures["聚类散点图"] = _fig_to_bytes(fig)
        except Exception:
            pass

    # ----- 特征重要性 + 模型对比（通用）-----
    if model_result.get("Top特征"):
        try:
            fig = plot_feature_importance(model_result["Top特征"])
            figures["特征重要性"] = _fig_to_bytes(fig)
        except Exception:
            pass

    if model_result.get("模型结果"):
        try:
            mr = model_result["模型结果"]
            if problem_type == "回归分析":
                metric = "R²"
            elif problem_type == "分类分析":
                metric = "准确率"
            else:
                metric = "轮廓系数"
            fig = plot_model_comparison(mr, metric, "模型性能对比")
            figures["模型性能对比"] = _fig_to_bytes(fig)
        except Exception:
            pass

    return figures


# ============================================================
# 单图导出
# ============================================================
def export_figure(fig_bytes: bytes, filename: str, fmt: str = "png") -> bytes:
    """已弃用 — create_figures 直接返回 bytes。保留用于后续可能的格式转换。"""
    return fig_bytes
