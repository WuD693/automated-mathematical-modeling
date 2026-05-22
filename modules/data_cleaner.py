"""
数据清洗器 — 缺失值填充、异常值检测、文本编码、去重
每步操作均生成可读的中文报告。
"""

import pandas as pd
import numpy as np
from typing import Tuple, List


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], dict]:
    """
    对 DataFrame 执行完整的自动清洗流程。

    返回:
        (清洗后 DataFrame, 清洗报告列表, 清洗统计 dict)
    """
    report: List[str] = []
    stats = {"original_rows": len(df), "original_cols": len(df.columns)}
    df = df.copy()

    # ---- 1. 重复行 ----
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        report.append(f"删除 {dup_count} 行完全重复数据")
    else:
        report.append("未发现重复行")

    # ---- 2. 缺失值 ----
    missing_before = {col: int(df[col].isnull().sum()) for col in df.columns}
    total_missing = sum(missing_before.values())

    if total_missing > 0:
        details = []
        for col, cnt in missing_before.items():
            if cnt > 0:
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].median()
                    df[col] = df[col].fillna(fill_val)
                    details.append(f"{col}（{cnt}个缺失 → 中位数 {fill_val:.2f} 填充）")
                else:
                    mode_vals = df[col].mode()
                    fill_val = mode_vals[0] if len(mode_vals) > 0 else "未知"
                    df[col] = df[col].fillna(fill_val)
                    details.append(f"{col}（{cnt}个缺失 → 众数「{fill_val}」填充）")
        report.append("缺失值处理: " + "；".join(details))
    else:
        report.append("未发现缺失值")

    stats["missing_filled"] = total_missing

    # ---- 3. 异常值检测（仅数值列）----
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    outlier_info = {}
    total_outliers = 0

    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        outlier_count = len(outliers)

        if outlier_count > 0:
            # 用边界值封顶（Winsorize），而非删除
            df[col] = df[col].clip(lower=lower, upper=upper)
            outlier_info[col] = {
                "count": outlier_count,
                "lower": round(lower, 2),
                "upper": round(upper, 2),
            }
            total_outliers += outlier_count

    if outlier_info:
        items = [f"{c}（{v['count']}个 → 截断至 [{v['lower']}, {v['upper']}]）"
                 for c, v in outlier_info.items()]
        report.append("异常值处理: " + "；".join(items))
    else:
        report.append("未发现异常值")

    stats["outliers_clipped"] = total_outliers

    # ---- 4. 文本列编码 ----
    text_cols = [
        c for c in df.columns
        if not pd.api.types.is_numeric_dtype(df[c])
        and not pd.api.types.is_datetime64_any_dtype(df[c])
    ]
    encoded_cols = []

    for col in text_cols:
        unique_vals = df[col].nunique()
        if unique_vals <= 1:
            # 只有 1 个值，删除该列
            df = df.drop(columns=[col])
            report.append(f"移除常量列「{col}」（所有值相同）")
        elif unique_vals <= 10:
            # 低基数 → One-Hot 编码
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
            df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
            encoded_cols.append(f"{col}（{unique_vals}个类别 → {len(dummies.columns)}个二值列）")
        else:
            # 高基数 → Label 编码
            df[col] = pd.factorize(df[col])[0]
            encoded_cols.append(f"{col}（{unique_vals}个类别 → 数值标签编码）")

    if encoded_cols:
        report.append("文本编码: " + "；".join(encoded_cols))

    stats["final_rows"] = len(df)
    stats["final_cols"] = len(df.columns)

    return df, report, stats
