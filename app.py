"""
自动化数学建模平台 — 主程序
零代码、一站式：数据上传 → 清洗 → 建模 → 可视化 → 结论
"""

import streamlit as st
import pandas as pd
from config import PAGE_TITLE, PAGE_LAYOUT, COLORS, STEPS, MAX_FILE_SIZE_MB
from modules.data_loader import load_data
from modules.data_cleaner import clean_data
from modules.auto_model import analyze, METRIC_EXPLANATIONS
from modules.visualizer import create_figures
from modules.insight import generate_insights

# ============================================================
# 页面设置
# ============================================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="",
    layout=PAGE_LAYOUT,
    initial_sidebar_state="expanded",
)

# ============================================================
# 自定义 CSS
# ============================================================
def load_css():
    """加载自定义样式"""
    css_path = "assets/style.css"
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # 打包后路径可能不同，静默跳过

load_css()

# ============================================================
# 初始化会话状态
# ============================================================
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "data" not in st.session_state:
    st.session_state.data = None
if "data_meta" not in st.session_state:
    st.session_state.data_meta = None
if "cleaned_data" not in st.session_state:
    st.session_state.cleaned_data = None
if "cleaning_report" not in st.session_state:
    st.session_state.cleaning_report = None
if "target_col" not in st.session_state:
    st.session_state.target_col = None
if "y_original" not in st.session_state:
    st.session_state.y_original = None
if "model_result" not in st.session_state:
    st.session_state.model_result = None
if "figures" not in st.session_state:
    st.session_state.figures = None
if "insights" not in st.session_state:
    st.session_state.insights = None


# ============================================================
# 侧边栏 — 步骤导航
# ============================================================
with st.sidebar:
    st.markdown("## 🔬 自动数学建模")
    st.markdown("---")

    for step in STEPS:
        step_id = step["id"]
        if step_id < st.session_state.current_step:
            badge = "✅"
        elif step_id == st.session_state.current_step:
            badge = "🔵"
        else:
            badge = "⚪"

        if step_id == st.session_state.current_step:
            st.markdown(
                f"""<div style="padding:8px 12px; margin:4px 0;
                background:{COLORS['primary_pale']}; border-radius:6px;
                border-left:3px solid {COLORS['primary']}; font-weight:bold;
                color:{COLORS['title']};">{badge} {step['icon']} {step['name']}</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""<div style="padding:8px 12px; margin:4px 0;
                color:{COLORS['muted']};">{badge} {step['icon']} {step['name']}</div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.caption("所有数据均在本地处理，不会上传网络")

# ============================================================
# 主内容区
# ============================================================
st.markdown(
    f"""<h1 style="color:{COLORS['title']}; margin-bottom:4px;">
    🔬 自动化数学建模平台</h1>""",
    unsafe_allow_html=True,
)
st.markdown(
    f"""<p style="color:{COLORS['muted']}; font-size:15px; margin-bottom:24px;">
    上传您的数据，自动完成清洗、建模、可视化，洞察关键结论 — 全程无需编写代码</p>""",
    unsafe_allow_html=True,
)

# ============================================================
# 步骤 1：上传数据
# ============================================================
css_class = "step-card-completed" if st.session_state.data is not None else "step-card-active"
st.markdown(
    f"""<div class="{css_class}">
    <h3>📂 步骤 1：上传数据</h3>
    <p style="color:{COLORS['muted']};">支持 CSV 和 Excel 文件，最大 {MAX_FILE_SIZE_MB}MB</p>
    </div>""",
    unsafe_allow_html=True,
)

if st.session_state.data is None:
    uploaded_file = st.file_uploader(
        "选择数据文件",
        type=["csv", "xlsx", "xls"],
        help="拖拽文件到此处或点击选择",
    )

    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"文件超过 {MAX_FILE_SIZE_MB}MB 限制，请压缩后重试")
        else:
            with st.spinner("正在读取数据..."):
                try:
                    df, meta = load_data(uploaded_file)
                    st.session_state.data = df
                    st.session_state.data_meta = meta
                    st.session_state.current_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"读取文件失败：{e}")
else:
    # 已加载数据时显示摘要 + 重新上传按钮
    meta = st.session_state.data_meta
    st.success(f"✅ 已加载：{meta['filename']}（{meta['rows']:,} 行 × {meta['cols']} 列）")
    if st.button("🔄 重新上传", key="reset_data"):
        st.session_state.data = None
        st.session_state.data_meta = None
        st.session_state.cleaned_data = None
        st.session_state.cleaning_report = None
        st.session_state.target_col = None
        st.session_state.y_original = None
        st.session_state.model_result = None
        st.session_state.current_step = 1
        st.rerun()

# ============================================================
# 步骤 2：数据预览与清洗
# ============================================================
if st.session_state.data is not None:
    css_class = "step-card-completed" if st.session_state.current_step > 2 else "step-card-active"
    st.markdown(
        f"""<div class="{css_class}">
        <h3>🔧 步骤 2：数据预览与清洗</h3>
        <p style="color:{COLORS['muted']};">自动处理缺失值、异常值、文本编码</p>
        </div>""",
        unsafe_allow_html=True,
    )

    meta = st.session_state.data_meta
    df = st.session_state.data

    # 基本信息卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("数据行数", f"{meta['rows']:,}")
    col2.metric("数据列数", meta["cols"])
    col3.metric("文件大小", f"{meta['file_size_mb']} MB")
    col4.metric("缺失值数量", meta["missing_count"])

    # 列类型分布
    type_counts = pd.Series(meta["col_types"]).value_counts()
    type_str = " | ".join([f"{v}列 {k}个" for k, v in type_counts.items()])
    st.caption(f"列类型分布：{type_str}")

    # 数据预览表格
    st.markdown("**数据预览**（前 10 行）")
    st.dataframe(df.head(10), use_container_width=True)

    # 每列简要统计（仅数值列）
    numeric_cols = [c for c, t in meta["col_types"].items() if t == "数值"]
    if numeric_cols:
        with st.expander("查看数值列统计摘要"):
            st.dataframe(df[numeric_cols].describe(), use_container_width=True)

    # 清洗按钮
    if st.session_state.cleaned_data is None:
        st.markdown("---")
        if st.button("🔄 开始自动清洗", type="primary", use_container_width=True):
            with st.spinner("正在清洗数据..."):
                cleaned, report, stats = clean_data(df)
                st.session_state.cleaned_data = cleaned
                st.session_state.cleaning_report = report
                st.session_state.cleaning_stats = stats
                st.session_state.current_step = 3
                st.rerun()
    else:
        # 清洗已完成，展示报告
        st.markdown("---")
        st.markdown("#### ✅ 清洗完成")
        for line in st.session_state.cleaning_report:
            st.markdown(
                f"""<div class="cleaning-report">• {line}</div>""",
                unsafe_allow_html=True,
            )

        # 清洗前后对比
        stats = st.session_state.cleaning_stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("原始行数", f"{stats['original_rows']:,}",
                  delta=f"{stats['final_rows'] - stats['original_rows']}" if stats['final_rows'] != stats['original_rows'] else None)
        c2.metric("清洗后行数", f"{stats['final_rows']:,}")
        c3.metric("填充缺失值", f"{stats['missing_filled']}个")
        c4.metric("处理异常值", f"{stats['outliers_clipped']}个")

        # 清洗后预览
        with st.expander("查看清洗后数据（前 10 行）"):
            st.dataframe(st.session_state.cleaned_data.head(10), use_container_width=True)

        if st.button("🔄 重新清洗", key="reclean"):
            st.session_state.cleaned_data = None
            st.session_state.cleaning_report = None
            st.session_state.current_step = 2
            st.rerun()

else:
    st.markdown(
        f"""<div style="opacity:0.5; background:{COLORS['card_bg']};
        border:1px solid {COLORS['divider']}; border-radius:8px; padding:24px; margin-bottom:16px;">
        <h3 style="color:{COLORS['muted']};">🔧 步骤 2：数据预览与清洗</h3>
        <p style="color:{COLORS['muted']};">请先上传数据</p>
        </div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# 步骤 3：选择分析目标
# ============================================================
if st.session_state.current_step >= 3:
    css_class = "step-card-completed" if st.session_state.current_step > 3 else "step-card-active"
    st.markdown(
        f"""<div class="{css_class}">
        <h3>🎯 步骤 3：选择分析目标</h3>
        <p style="color:{COLORS['muted']};">选择目标列，或让系统自动判断分析类型</p>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.session_state.cleaned_data is not None and st.session_state.current_step == 3:
        original_cols = st.session_state.data.columns.tolist()
        cleaned_cols = st.session_state.cleaned_data.columns.tolist()

        col1, col2 = st.columns([1, 1])
        with col1:
            target_col = st.selectbox(
                "选择要分析的目标列（预测/分类对象）",
                options=["（自动判断/聚类分析）"] + original_cols,
                help="选择你想预测或分类的列，留空则由系统自动判断",
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            auto_mode = target_col.startswith("（")
            if auto_mode:
                st.info("将自动进行聚类分析或降维探索")
            else:
                st.info(f"将以「{target_col}」为目标进行分析")

        if st.button("🚀 开始建模分析", type="primary", use_container_width=True):
            with st.spinner("正在训练模型，请稍候..."):
                # 准备 y_original（目标列的原始值）
                y_orig = None
                actual_target = None if auto_mode else target_col
                if not auto_mode:
                    y_orig = st.session_state.data[target_col]

                result = analyze(
                    st.session_state.cleaned_data,
                    target_col=actual_target,
                    y_original=y_orig,
                )
                st.session_state.model_result = result
                st.session_state.target_col = actual_target
                st.session_state.y_original = y_orig
                st.session_state.current_step = 4
                st.rerun()
else:
    st.markdown(
        f"""<div style="opacity:0.5; background:{COLORS['card_bg']};
        border:1px solid {COLORS['divider']}; border-radius:8px; padding:24px; margin-bottom:16px;">
        <h3 style="color:{COLORS['muted']};">🎯 步骤 3：选择分析目标</h3>
        <p style="color:{COLORS['muted']};">请先完成数据清洗</p>
        </div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# 步骤 4：建模结果
# ============================================================
if st.session_state.current_step >= 4:
    css_class = "step-card-completed" if st.session_state.current_step > 4 else "step-card-active"
    st.markdown(
        f"""<div class="{css_class}">
        <h3>🧠 步骤 4：建模结果</h3>
        <p style="color:{COLORS['muted']};">自动训练多个模型，对比选出最优方案</p>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.session_state.model_result is not None and st.session_state.current_step == 4:
        result = st.session_state.model_result

        # 分析类型 + 最优模型
        st.markdown(f"### {result['类型']} — 最优模型：**{result['总体最优']}**")

        # 模型对比表
        st.markdown("#### 模型性能对比")
        df_models = pd.DataFrame(result["模型结果"])
        # 只显示有效列
        display_cols = [c for c in df_models.columns if c not in ("得分", "错误") and df_models[c].notna().any()]
        st.dataframe(
            df_models[display_cols],
            use_container_width=True,
            hide_index=True,
        )

        # 指标解释
        st.markdown("#### 指标说明")
        metric_keys = {
            "回归分析": ["R²", "MSE", "MAE"],
            "分类分析": ["准确率", "F1分数", "精确率", "召回率"],
            "聚类分析": ["轮廓系数"],
        }
        for key in metric_keys.get(result["类型"], []):
            if key in METRIC_EXPLANATIONS:
                st.caption(f"**{key}**：{METRIC_EXPLANATIONS[key]}")

        # 特征重要性
        if result.get("Top特征"):
            st.markdown("#### 关键影响因素（Top 特征）")
            top = result["Top特征"]
            # 简单的进度条展示
            for feat, imp in top[:5]:
                pct = int(imp * 100)
                st.markdown(
                    f"""<div style="margin:4px 0;">
                    <span style="color:{COLORS['body']}; font-size:14px;">{feat}</span>
                    <div style="background:{COLORS['divider']}; border-radius:4px; height:20px; margin-top:2px;">
                    <div style="background:{COLORS['primary']}; width:{pct}%; height:20px;
                    border-radius:4px; text-align:right; padding-right:8px; line-height:20px;
                    color:white; font-size:12px;">{pct}%</div>
                    </div></div>""",
                    unsafe_allow_html=True,
                )

        # 聚类额外信息
        if result["类型"] == "聚类分析" and result.get("簇中心") is not None:
            with st.expander("查看各簇特征中心"):
                st.dataframe(result["簇中心"], use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📊 生成可视化图表", type="primary", use_container_width=True):
                with st.spinner("正在生成 Nature 风格图表和结论..."):
                    figs = create_figures(st.session_state.cleaned_data, result)
                    ins = generate_insights(st.session_state.cleaned_data, result)
                    st.session_state.figures = figs
                    st.session_state.insights = ins
                    st.session_state.current_step = 5
                    st.rerun()
        with c2:
            if st.button("🔄 重新建模", key="remodel"):
                st.session_state.model_result = None
                st.session_state.target_col = None
                st.session_state.figures = None
                st.session_state.current_step = 3
                st.rerun()
else:
    st.markdown(
        f"""<div style="opacity:0.5; background:{COLORS['card_bg']};
        border:1px solid {COLORS['divider']}; border-radius:8px; padding:24px; margin-bottom:16px;">
        <h3 style="color:{COLORS['muted']};">🧠 步骤 4：建模结果</h3>
        <p style="color:{COLORS['muted']};">请先选择分析目标</p>
        </div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# 步骤 5：可视化图表
# ============================================================
if st.session_state.current_step >= 5:
    css_class = "step-card-completed" if st.session_state.current_step > 5 else "step-card-active"
    st.markdown(
        f"""<div class="{css_class}">
        <h3>📊 步骤 5：可视化图表</h3>
        <p style="color:{COLORS['muted']};">Nature 期刊风格 — 无冗余边框、科学配色、出版级质量</p>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.session_state.figures is not None and st.session_state.current_step == 5:
        figs = st.session_state.figures
        st.markdown(f"共生成 **{len(figs)}** 张图表")

        # 以 2 列网格展示图表
        names = list(figs.keys())
        for i in range(0, len(names), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(names):
                    name = names[idx]
                    data = figs[name]
                    with col:
                        st.markdown(f"**{name}**")
                        st.image(data, use_container_width=True)

                        # 下载按钮
                        st.download_button(
                            label=f"下载 {name} (PNG)",
                            data=data,
                            file_name=f"{name}.png",
                            mime="image/png",
                            key=f"dl_{idx}",
                        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💡 查看关键结论", type="primary", use_container_width=True):
                st.session_state.current_step = 6
                st.rerun()
        with c2:
            if st.button("🔄 重新生成图表", key="regen_figs"):
                st.session_state.figures = None
                st.session_state.insights = None
                st.session_state.current_step = 4
                st.rerun()
else:
    st.markdown(
        f"""<div style="opacity:0.5; background:{COLORS['card_bg']};
        border:1px solid {COLORS['divider']}; border-radius:8px; padding:24px; margin-bottom:16px;">
        <h3 style="color:{COLORS['muted']};">📊 步骤 5：可视化图表</h3>
        <p style="color:{COLORS['muted']};">请先完成建模</p>
        </div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# 步骤 6：关键结论
# ============================================================
if st.session_state.current_step >= 6:
    css_class = "step-card-completed" if st.session_state.current_step > 6 else "step-card-active"
    st.markdown(
        f"""<div class="{css_class}">
        <h3>💡 步骤 6：关键结论</h3>
        <p style="color:{COLORS['muted']};">基于建模结果自动提炼，通俗中文呈现</p>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.session_state.insights is not None and st.session_state.current_step == 6:
        insights = st.session_state.insights

        # 按类别分组展示
        from collections import defaultdict
        grouped = defaultdict(list)
        for ins in insights:
            grouped[ins["category"]].append(ins)

        for category, items in grouped.items():
            for item in items:
                icon = item.get("icon", "")
                bg_color = {
                    "数据概况": "#F0F7FF",
                    "分析目标": "#FFF8E1",
                    "数据质量": "#FFF3E0",
                    "模型表现": "#E8F5E9",
                    "模型稳定性": "#E8F5E9",
                    "关键影响因素": "#F3E5F5",
                    "次要因素": "#ECEFF1",
                    "关键发现": "#FFF9C4",
                    "聚类结果": "#E8F5E9",
                    "建模建议": "#E3F2FD",
                    "提示": "#FFEBEE",
                    "群体差异维度": "#F3E5F5",
                }.get(category, "#F0F7FF")

                st.markdown(
                    f"""<div style="background:{bg_color}; border-left:4px solid {COLORS['primary']};
                    border-radius:6px; padding:12px 16px; margin:6px 0;">
                    <span style="font-size:13px; color:{COLORS['muted']};">{icon} {category}</span><br>
                    <span style="color:{COLORS['body']};">{item['text']}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

        if st.button("🔄 重新分析", key="redo_all"):
            st.session_state.model_result = None
            st.session_state.figures = None
            st.session_state.insights = None
            st.session_state.target_col = None
            st.session_state.current_step = 3
            st.rerun()
else:
    st.markdown(
        f"""<div style="opacity:0.5; background:{COLORS['card_bg']};
        border:1px solid {COLORS['divider']}; border-radius:8px; padding:24px; margin-bottom:16px;">
        <h3 style="color:{COLORS['muted']};">💡 步骤 6：关键结论</h3>
        <p style="color:{COLORS['muted']};">请先完成可视化</p>
        </div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# 调试：显示当前状态（开发阶段使用，上线后移除）
# ============================================================
with st.sidebar:
    st.markdown("---")
    st.caption(f"当前步骤: {st.session_state.current_step}/6")
    st.caption(f"数据已加载: {'是' if st.session_state.data is not None else '否'}")
    if st.session_state.data_meta:
        st.caption(f"文件: {st.session_state.data_meta['filename']}")
        st.caption(f"规模: {st.session_state.data_meta['rows']}行 x {st.session_state.data_meta['cols']}列")
    if st.session_state.model_result:
        st.caption(f"分析类型: {st.session_state.model_result['类型']}")
        st.caption(f"最优模型: {st.session_state.model_result['总体最优']}")
