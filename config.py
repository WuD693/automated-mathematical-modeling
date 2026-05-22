"""
全局配置 — 自动化数学建模软件
配色、字体、页面常量均从此文件引用，统一管理。
"""

# ============================================================
# 页面配置
# ============================================================
PAGE_TITLE = "自动化数学建模平台"
PAGE_ICON = "https://img.icons8.com/color/48/artificial-intelligence.png"
PAGE_LAYOUT = "wide"

# ============================================================
# 配色方案（淡蓝色系）
# ============================================================
COLORS = {
    # 页面
    "bg": "#F0F7FF",
    "sidebar_bg": "#E3F2FD",
    "card_bg": "#FFFFFF",

    # 主色
    "primary": "#4A90D9",
    "primary_light": "#5B9BD5",
    "primary_dark": "#3A7BC8",
    "primary_pale": "#E3F2FD",

    # 文字
    "title": "#1565C0",
    "body": "#1A1A2E",
    "muted": "#78909C",

    # 功能色
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "divider": "#E0E0E0",

    # Nature 图表色板
    "nature_palette": [
        "#3498DB", "#E74C3C", "#2ECC71", "#9B59B6",
        "#F39C12", "#1ABC9C", "#E91E63", "#795548",
        "#607D8B", "#CDDC39",
    ],
}

# ============================================================
# 字体配置
# ============================================================
FONTS = {
    "family_sans": "Segoe UI, Microsoft YaHei, sans-serif",
    "family_mono": "Consolas, Microsoft YaHei, monospace",
    "chart_family": "Arial, Microsoft YaHei, sans-serif",
}

# ============================================================
# 文件上传限制
# ============================================================
MAX_FILE_SIZE_MB = 100
SUPPORTED_FORMATS = ["csv", "xlsx", "xls"]

# ============================================================
# MATLAB MCP 配置
# ============================================================
MATLAB_MCP_SERVER = "D:\\浏览器下载\\matlab-mcp-core-server-win64.exe"
MATLAB_MCP_TIMEOUT = 120  # MATLAB 启动/绘图超时（秒）

# 降级模式：当 MATLAB MCP 不可用时使用 matplotlib
FALLBACK_TO_MATPLOTLIB = True

# ============================================================
# 分析步骤定义
# ============================================================
STEPS = [
    {"id": 1, "name": "上传数据", "icon": "📂"},
    {"id": 2, "name": "数据预览与清洗", "icon": "🔧"},
    {"id": 3, "name": "选择分析目标", "icon": "🎯"},
    {"id": 4, "name": "建模结果", "icon": "🧠"},
    {"id": 5, "name": "可视化图表", "icon": "📊"},
    {"id": 6, "name": "关键结论", "icon": "💡"},
]
