"""
自动建模引擎 — 问题类型判定、多模型训练、性能对比、指标解释
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import warnings

warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# 回归模型
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# 分类模型
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC

# 聚类模型
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score

# 指标
from sklearn.metrics import (
    r2_score, mean_squared_error, mean_absolute_error,
    accuracy_score, f1_score, precision_score, recall_score,
)

# ============================================================
# 模型池
# ============================================================
REGRESSION_MODELS = {
    "线性回归": LinearRegression(),
    "岭回归": Ridge(alpha=1.0),
    "Lasso回归": Lasso(alpha=1.0, max_iter=5000),
    "随机森林": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    "梯度提升": GradientBoostingRegressor(n_estimators=100, random_state=42),
}

CLASSIFICATION_MODELS = {
    "逻辑回归": LogisticRegression(max_iter=5000, random_state=42),
    "随机森林": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    "梯度提升": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "支持向量机": SVC(kernel="rbf", probability=True, random_state=42),
}

# ============================================================
# 指标中文说明
# ============================================================
METRIC_EXPLANATIONS = {
    "R²": "拟合优度，越接近 1 模型越好（0.8以上为优秀，0.6-0.8为良好）",
    "MSE": "均方误差，预测值与真实值偏差的平方均值，越小越好",
    "MAE": "平均绝对误差，预测偏差的平均大小，越小越好",
    "准确率": "预测正确的比例，越接近 1 越好",
    "F1分数": "精确率与召回率的调和平均，兼顾查准与查全，越接近 1 越好",
    "精确率": "预测为正例中真正为正的比例",
    "召回率": "真正为正例中被找出的比例",
    "轮廓系数": "聚类质量的度量，范围[-1,1]，越接近 1 聚类越紧凑（>0.4 为较好）",
}

# ============================================================
# 问题类型判定
# ============================================================
def detect_problem_type(df: pd.DataFrame, target_col: Optional[str]) -> str:
    """
    判定分析类型: regression / classification / clustering
    """
    if target_col is None or target_col not in df.columns:
        return "clustering"

    y = df[target_col].dropna()

    if pd.api.types.is_numeric_dtype(y):
        unique_ratio = y.nunique() / len(y)
        # 少量整数值 → 可能更适合分类
        if y.nunique() <= 15 and unique_ratio < 0.1:
            return "classification"
        return "regression"
    else:
        return "classification"


# ============================================================
# 数据准备
# ============================================================
def _prepare_xy(df: pd.DataFrame, target_col: str):
    """分离特征 X 和目标 y，并对 X 做预处理"""
    y = df[target_col].copy()

    # 特征列：排除目标列
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols].copy()

    # 编码文本列
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            if X[col].nunique() <= 20:
                X = pd.get_dummies(X, columns=[col], drop_first=True)
            else:
                X[col] = LabelEncoder().fit_transform(X[col].astype(str))

    # 填充残留 NaN（极少情况）
    X = X.fillna(X.median())

    return X, y


# ============================================================
# 回归分析
# ============================================================
def _run_regression(df: pd.DataFrame, target_col: str) -> Dict:
    X, y = _prepare_xy(df, target_col)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = []
    for name, model in REGRESSION_MODELS.items():
        try:
            # 对需要缩放的模型使用 scaled 数据，树模型用原始数据
            if name in ("线性回归", "岭回归", "Lasso回归"):
                X_tr, X_te = X_train_scaled, X_test_scaled
            else:
                X_tr, X_te = X_train, X_test

            model.fit(X_tr, y_train)
            y_pred = model.predict(X_te)

            r2 = r2_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)

            # 交叉验证
            cv_scores = cross_val_score(
                model, X_tr, y_train, cv=3,
                scoring="r2", n_jobs=-1
            )

            results.append({
                "模型": name,
                "R²": round(r2, 4),
                "MSE": round(mse, 2),
                "MAE": round(mae, 2),
                "交叉验证R²": f"{cv_scores.mean():.4f} ± {cv_scores.std():.4f}",
                "得分": round(max(r2, 0), 4),  # 综合排序分
            })
        except Exception as e:
            results.append({"模型": name, "R²": None, "MSE": None, "MAE": None,
                           "交叉验证R²": "失败", "得分": 0, "错误": str(e)[:60]})

    results.sort(key=lambda x: x["得分"], reverse=True)

    # 特征重要性（用随机森林）
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    importances = list(zip(X.columns, rf.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    top_features = importances[:8]

    return {
        "类型": "回归分析",
        "目标列": target_col,
        "测试集大小": len(y_test),
        "模型结果": results,
        "Top特征": top_features,
        "总体最优": results[0]["模型"] if results else "无",
    }


# ============================================================
# 分类分析
# ============================================================
def _run_classification(df: pd.DataFrame, target_col: str) -> Dict:
    X, y = _prepare_xy(df, target_col)

    # 编码目标变量
    le = LabelEncoder()
    y_encoded = le.fit_transform(y.astype(str))
    class_names = le.classes_

    # 检查是否可以做分层抽样
    class_counts = pd.Series(y_encoded).value_counts()
    can_stratify = (class_counts.min() >= 2)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42,
        stratify=y_encoded if can_stratify else None,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = []
    for name, model in CLASSIFICATION_MODELS.items():
        try:
            if name in ("逻辑回归", "支持向量机"):
                X_tr, X_te = X_train_scaled, X_test_scaled
            else:
                X_tr, X_te = X_train, X_test

            model.fit(X_tr, y_train)
            y_pred = model.predict(X_te)

            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
            prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
            rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)

            cv_scores = cross_val_score(
                model, X_tr, y_train, cv=3,
                scoring="accuracy", n_jobs=-1
            )

            results.append({
                "模型": name,
                "准确率": round(acc, 4),
                "F1分数": round(f1, 4),
                "精确率": round(prec, 4),
                "召回率": round(rec, 4),
                "交叉验证准确率": f"{cv_scores.mean():.4f} ± {cv_scores.std():.4f}",
                "得分": round(acc, 4),
            })
        except Exception as e:
            results.append({"模型": name, "准确率": None, "F1分数": None,
                           "精确率": None, "召回率": None,
                           "交叉验证准确率": "失败", "得分": 0, "错误": str(e)[:60]})

    results.sort(key=lambda x: x["得分"], reverse=True)

    # 特征重要性（随机森林）
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    importances = list(zip(X.columns, rf.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    top_features = importances[:8]

    return {
        "类型": "分类分析",
        "目标列": target_col,
        "类别": list(class_names),
        "测试集大小": len(y_test),
        "模型结果": results,
        "Top特征": top_features,
        "总体最优": results[0]["模型"] if results else "无",
    }


# ============================================================
# 聚类分析
# ============================================================
def _run_clustering(df: pd.DataFrame) -> Dict:
    # 仅用数值列
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    X = df[numeric_cols].copy()
    X = X.fillna(X.median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    results = []

    # KMeans（尝试 2-6 个簇）
    best_k = 2
    best_sil = -1
    kmeans_scores = []
    for k in range(2, min(7, len(X) // 3)):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        kmeans_scores.append({"k": k, "轮廓系数": round(sil, 4)})
        if sil > best_sil:
            best_sil = sil
            best_k = k

    km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels = km_final.fit_predict(X_scaled)

    results.append({
        "模型": "K-Means",
        "最佳簇数": best_k,
        "轮廓系数": round(best_sil, 4),
        "簇大小": [int((cluster_labels == i).sum()) for i in range(best_k)],
        "得分": round(best_sil, 4),
    })

    # 层次聚类
    for k_candidate in [best_k]:
        try:
            agg = AgglomerativeClustering(n_clusters=k_candidate)
            labels_agg = agg.fit_predict(X_scaled)
            sil_agg = silhouette_score(X_scaled, labels_agg)
            results.append({
                "模型": "层次聚类",
                "最佳簇数": k_candidate,
                "轮廓系数": round(sil_agg, 4),
                "簇大小": [int((labels_agg == i).sum()) for i in range(k_candidate)],
                "得分": round(sil_agg, 4),
            })
        except Exception:
            pass

    results.sort(key=lambda x: x["得分"], reverse=True)

    # 簇中心特征分析
    cluster_centers = pd.DataFrame(
        scaler.inverse_transform(km_final.cluster_centers_),
        columns=numeric_cols,
    )
    cluster_centers.index = [f"簇{i+1}" for i in range(best_k)]

    return {
        "类型": "聚类分析",
        "样本量": len(X),
        "特征数": len(numeric_cols),
        "模型结果": results,
        "聚类标签": cluster_labels.tolist(),
        "簇中心": cluster_centers,
        "总体最优": "K-Means",
    }


# ============================================================
# 主入口
# ============================================================
def analyze(df: pd.DataFrame, target_col: Optional[str] = None,
            y_original: Optional[pd.Series] = None) -> Dict:
    """
    自动判断问题类型并执行建模。

    参数:
        df: 输入 DataFrame（建议已清洗的特征）
        target_col: 目标列名，None 则自动判断/聚类
        y_original: 原始目标列数据（当 df 中目标列被编码时使用）

    返回:
        {类型, 模型结果, Top特征, 总体最优, ...}
    """
    # 如果 df 中找不到目标列（被清洗器编码了），使用 y_original
    if target_col and target_col not in df.columns:
        if y_original is not None:
            # 将原始目标列恢复到 df 中用于类型判定
            combined = df.copy()
            combined[target_col] = y_original.values[:len(df)]
            problem_type = detect_problem_type(combined, target_col)

            if problem_type == "regression":
                return _run_regression_with_y(df, target_col, y_original)
            elif problem_type == "classification":
                return _run_classification_with_y(df, target_col, y_original)
            else:
                return _run_clustering(df)
        else:
            # 找不到目标列也没有原始数据，退回聚类
            return _run_clustering(df)

    problem_type = detect_problem_type(df, target_col)

    if problem_type == "regression":
        return _run_regression(df, target_col)
    elif problem_type == "classification":
        return _run_classification(df, target_col)
    else:
        return _run_clustering(df)


def _run_regression_with_y(df_features, target_col, y_original):
    """使用清洗后的特征 + 原始目标列做回归"""
    return _run_regression(_merge_y(df_features, target_col, y_original), target_col)


def _run_classification_with_y(df_features, target_col, y_original):
    """使用清洗后的特征 + 原始目标列做分类"""
    return _run_classification(_merge_y(df_features, target_col, y_original), target_col)


def _merge_y(df_features, target_col, y_original):
    """将原始目标列合并到特征 DataFrame 中"""
    combined = df_features.copy()
    combined[target_col] = pd.Series(
        y_original.values[:len(df_features)],
        index=df_features.index,
    )
    return combined
