"""
结论自动生成 — 从数据+模型结果中提炼通俗中文结论
避免专业术语，让非技术用户也能读懂。
"""

import pandas as pd
import numpy as np
from typing import Dict, List


def generate_insights(df: pd.DataFrame, model_result: Dict) -> List[dict]:
    """
    根据数据和分析结果，生成分类的中文结论。

    返回:
        [{category: 类别, text: 结论文字, icon: 图标}, ...]
    """
    insights = []
    problem_type = model_result.get("类型", "")

    # ---- 1. 数据概况 ----
    insights.extend(_data_overview(df, model_result))

    # ---- 2. 模型表现 ----
    insights.extend(_model_performance(model_result))

    # ---- 3. 关键因素 ----
    insights.extend(_key_factors(model_result))

    # ---- 4. 针对性洞察 ----
    if problem_type == "回归分析":
        insights.extend(_regression_insights(df, model_result))
    elif problem_type == "分类分析":
        insights.extend(_classification_insights(model_result))
    elif problem_type == "聚类分析":
        insights.extend(_clustering_insights(model_result))

    return insights


def _data_overview(df: pd.DataFrame, result: Dict) -> List[dict]:
    """数据整体概况"""
    items = []
    n_rows = len(df)
    n_cols = len(df.columns)
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    items.append({
        "category": "数据概况",
        "icon": "📋",
        "text": f"本次分析共包含 {n_rows:,} 条记录、{n_cols} 个特征（其中 {len(numeric_cols)} 个数值型特征）",
    })

    problem_type = result.get("类型", "")
    if problem_type == "回归分析":
        target = result.get("目标列", "目标")
        items.append({
            "category": "分析目标",
            "icon": "🎯",
            "text": f"分析目标：预测「{target}」的数值大小",
        })
    elif problem_type == "分类分析":
        target = result.get("目标列", "目标")
        categories = result.get("类别", [])
        cat_str = "、".join([str(c) for c in categories[:5]])
        items.append({
            "category": "分析目标",
            "icon": "🎯",
            "text": f"分析目标：判断「{target}」属于哪个类别（{cat_str}）",
        })
    else:
        items.append({
            "category": "分析目标",
            "icon": "🎯",
            "text": "分析目标：自动探索数据中的自然分组（无监督聚类）",
        })

    # 数据质量提示
    missing = df.isnull().sum().sum()
    if missing > 0:
        items.append({
            "category": "数据质量",
            "icon": "⚠️",
            "text": f"数据中存在 {missing} 个缺失值，建议清洗后再分析",
        })

    return items


def _model_performance(result: Dict) -> List[dict]:
    """模型表现描述"""
    items = []
    problem_type = result.get("类型", "")
    best_model = result.get("总体最优", "")
    models = result.get("模型结果", [])

    if not models:
        return items

    best = models[0]
    model_count = len([m for m in models if m.get("得分", 0) > 0])

    if problem_type == "回归分析":
        r2 = best.get("R²", 0)
        if r2 is None:
            r2 = 0
        if r2 >= 0.85:
            quality = "非常好"
        elif r2 >= 0.7:
            quality = "较好"
        elif r2 >= 0.5:
            quality = "中等"
        else:
            quality = "偏弱"

        items.append({
            "category": "模型表现",
            "icon": "🧠",
            "text": (
                f"最优模型「{best_model}」的拟合优度为 {r2:.1%}，"
                f"意味着该模型可以解释 {r2:.0%} 的目标变化（{quality}）。"
                f"平均预测误差约 {best.get('MAE', '?')}"
            ),
        })

        # 交叉验证稳定性
        cv_str = best.get("交叉验证R²", "")
        if "±" in str(cv_str):
            items.append({
                "category": "模型稳定性",
                "icon": "📊",
                "text": f"交叉验证 R² = {cv_str}，模型在不同数据子集上表现稳定",
            })

    elif problem_type == "分类分析":
        acc = best.get("准确率", 0)
        if acc is None:
            acc = 0
        if acc >= 0.9:
            quality = "非常好"
        elif acc >= 0.75:
            quality = "良好"
        elif acc >= 0.6:
            quality = "中等"
        else:
            quality = "偏低"

        items.append({
            "category": "模型表现",
            "icon": "🧠",
            "text": (
                f"最优模型「{best_model}」的准确率为 {acc:.1%}，"
                f"F1 分数 {best.get('F1分数', '?')}（{quality}）。"
                f"该模型能够较为准确地完成分类任务"
            ),
        })

    else:
        sil = best.get("轮廓系数", 0)
        if sil is None:
            sil = 0
        k = best.get("最佳簇数", "?")
        if sil >= 0.5:
            quality = "结构清晰，聚类质量好"
        elif sil >= 0.3:
            quality = "聚类结构较合理"
        else:
            quality = "聚类界限较模糊"

        items.append({
            "category": "聚类结果",
            "icon": "🧠",
            "text": (
                f"数据可自然划分为 {k} 个群体（轮廓系数 {sil:.3f}），{quality}。"
                f"各簇大小分别为：{best.get('簇大小', '?')}"
            ),
        })

    return items


def _key_factors(result: Dict) -> List[dict]:
    """关键影响因素"""
    items = []
    top_features = result.get("Top特征", [])
    if not top_features:
        return items

    valid = [(f, imp) for f, imp in top_features if not np.isnan(imp) and imp > 0.01]
    if not valid:
        return items

    top3 = valid[:3]
    problem_type = result.get("类型", "")

    if problem_type == "回归分析":
        feat_desc = "、".join([f"「{f}」（贡献度 {imp:.0%}）" for f, imp in top3])
        items.append({
            "category": "关键影响因素",
            "icon": "🔑",
            "text": f"对目标影响最大的 3 个因素是：{feat_desc}",
        })
        if len(valid) > 3:
            others = "、".join([f"「{f}」" for f, _ in valid[3:]])
            items.append({
                "category": "次要因素",
                "icon": "📌",
                "text": f"次要影响因素包括：{others}，这些因素也有一定参考价值",
            })
    elif problem_type == "分类分析":
        feat_desc = "、".join([f"「{f}」（区分度 {imp:.0%}）" for f, imp in top3])
        items.append({
            "category": "关键区分特征",
            "icon": "🔑",
            "text": f"最能区分不同类别的 3 个特征是：{feat_desc}",
        })
    else:
        # 聚类 - 查看簇中心差异
        feat_desc = "、".join([f"「{f}」" for f, _ in top3])
        items.append({
            "category": "群体差异维度",
            "icon": "🔑",
            "text": f"不同群体在以下特征上差异最明显：{feat_desc}",
        })

    return items


def _regression_insights(df: pd.DataFrame, result: Dict) -> List[dict]:
    """回归分析专属洞察"""
    items = []
    top_features = result.get("Top特征", [])
    if not top_features:
        return items

    valid = [(f, imp) for f, imp in top_features if not np.isnan(imp)]
    if not valid:
        return items

    # 最强因素的方向性分析
    top_feat, top_imp = valid[0]
    if top_feat in df.columns and pd.api.types.is_numeric_dtype(df[top_feat]):
        corr = df[top_feat].corr(df.get(result.get("目标列", ""), pd.Series()))
        if not np.isnan(corr):
            direction = "正相关" if corr > 0 else "负相关"
            items.append({
                "category": "关键发现",
                "icon": "💡",
                "text": (
                    f"「{top_feat}」与目标呈「{direction}」（相关系数 {corr:.3f}），"
                    f"这意味着 {top_feat} 越高，目标值越{'高' if corr > 0 else '低'}"
                ),
            })

    # 数据分布提示
    models = result.get("模型结果", [])
    rf_model = [m for m in models if "森林" in m.get("模型", "")]
    linear_model = [m for m in models if "线性" in m.get("模型", "") or "回归" in m.get("模型", "")]

    if rf_model and linear_model:
        rf_score = rf_model[0].get("得分", 0)
        lr_score = linear_model[0].get("得分", 0)
        if rf_score and lr_score:
            if rf_score - lr_score > 0.05:
                items.append({
                    "category": "建模建议",
                    "icon": "💭",
                    "text": (
                        "树模型（随机森林/梯度提升）显著优于线性模型，"
                        "说明数据中存在非线性关系，建议关注特征间的交互效应"
                    ),
                })
            elif abs(rf_score - lr_score) < 0.02:
                items.append({
                    "category": "建模建议",
                    "icon": "💭",
                    "text": "线性模型与非线性模型效果接近，说明数据关系较为简单明了，结果可信度高",
                })

    return items


def _classification_insights(result: Dict) -> List[dict]:
    """分类分析专属洞察"""
    items = []
    models = result.get("模型结果", [])
    acc_values = [m.get("准确率") for m in models if m.get("准确率") is not None]
    if acc_values and max(acc_values) == 1.0:
        items.append({
            "category": "提示",
            "icon": "⚠️",
            "text": (
                "模型准确率达到 100%，可能原因：①数据高度可分（特征差异大）"
                "②特征与标签存在直接映射关系 ③样本量偏小。建议用更多数据验证"
            ),
        })

    return items


def _clustering_insights(result: Dict) -> List[dict]:
    """聚类分析专属洞察"""
    items = []
    models = result.get("模型结果", [])
    best = models[0] if models else {}
    k = best.get("最佳簇数", 2)
    cluster_sizes = best.get("簇大小", [])

    if cluster_sizes:
        min_sz = min(cluster_sizes)
        max_sz = max(cluster_sizes)
        if min_sz > 0 and max_sz / min_sz > 3:
            items.append({
                "category": "提示",
                "icon": "⚠️",
                "text": (
                    f"各簇大小差异较大（{min_sz} ~ {max_sz}），"
                    f"可能存在一个主导群体和若干小群体，建议关注小群体的独特特征"
                ),
            })

    # 簇中心解读
    centers = result.get("簇中心")
    if centers is not None and len(centers) <= 4:
        # 为每个簇生成一句话描述
        for i in range(len(centers)):
            row = centers.iloc[i]
            top_cols = row.abs().nlargest(2).index.tolist()
            vals = [f"{c}={row[c]:.1f}" for c in top_cols]
            items.append({
                "category": f"簇{i+1}特征",
                "icon": "🔍",
                "text": f"群体 {i+1}（{cluster_sizes[i]} 个样本）：{'、'.join(vals)} 较{'高' if row[top_cols[0]] > centers.values.mean() else '低'}",
            })

    return items
