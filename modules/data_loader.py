"""
数据加载器 — 文件读取、格式检测、元信息提取
"""

import pandas as pd
from typing import Tuple, Dict


def detect_encoding(file) -> str:
    """尝试检测文件编码，默认返回 utf-8"""
    for enc in ["utf-8", "gbk", "gb2312", "utf-8-sig", "latin1"]:
        try:
            file.seek(0)
            pd.read_csv(file, encoding=enc, nrows=5)
            file.seek(0)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    file.seek(0)
    return "utf-8"


def load_data(uploaded_file) -> Tuple[pd.DataFrame, Dict]:
    """
    根据文件扩展名自动选择读取方式，返回 DataFrame 和元信息。

    参数:
        uploaded_file: Streamlit UploadedFile 对象

    返回:
        (DataFrame, meta_info)
        meta_info = {"rows": int, "cols": int, "col_types": {col名: 类型}, "file_size_mb": float}
    """
    filename = uploaded_file.name.lower()
    file_size_mb = uploaded_file.size / (1024 * 1024)

    if filename.endswith(".csv"):
        encoding = detect_encoding(uploaded_file)
        df = pd.read_csv(uploaded_file, encoding=encoding)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    else:
        raise ValueError(f"不支持的文件格式: {filename}")

    col_types = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_types[col] = "数值"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_types[col] = "日期"
        else:
            col_types[col] = "文本"

    meta = {
        "filename": uploaded_file.name,
        "rows": len(df),
        "cols": len(df.columns),
        "columns": list(df.columns),
        "col_types": col_types,
        "file_size_mb": round(file_size_mb, 2),
        "missing_count": int(df.isnull().sum().sum()),
    }

    return df, meta
