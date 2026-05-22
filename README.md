# 🔬 自动化数学建模平台

**零代码、一站式**自动数学建模工具。上传数据，自动完成清洗→建模→Nature 风格可视化→结论输出，全程无需编写代码。

## 功能流程

```
上传数据 → 自动清洗 → 数学建模 → Nature图表 → 关键结论
```

| 步骤 | 说明 |
|------|------|
| 📂 上传数据 | 支持 CSV / Excel 文件，自动检测编码 |
| 🔧 数据清洗 | 缺失值填充、异常值截断、文本编码、去重 |
| 🎯 选择目标 | 手动指定或自动判断分析类型 |
| 🧠 自动建模 | 对比多个模型，选出最优方案 |
| 📊 可视化 | Nature 期刊风格图表，300 DPI 高清导出 |
| 💡 关键结论 | 中文通俗结论，非技术用户也能读懂 |

## 支持的建模类型

| 类型 | 模型 | 评估指标 |
|------|------|----------|
| **回归分析** | 线性回归、岭回归、Lasso、随机森林、梯度提升 | R² / MSE / MAE |
| **分类分析** | 逻辑回归、随机森林、梯度提升、SVM | 准确率 / F1 / 精确率 / 召回率 |
| **聚类分析** | K-Means、层次聚类 | 轮廓系数 |

## 快速开始

### 方式一：一键启动（推荐）

1. 下载/克隆本项目
2. 双击 `setup.bat`（首次自动安装 Python + 依赖 + 启动）
3. 浏览器打开 http://localhost:8501

### 方式二：命令行

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 方式三：已有环境

双击 `启动平台.bat` 直接启动。

## 测试数据

`test_data/` 目录包含 3 份示例数据：

| 文件 | 类型 | 行数 | 说明 |
|------|------|------|------|
| `regression_sample.csv` | 回归 | 200 | 房价预测（含缺失值+异常值） |
| `classification_sample.csv` | 分类 | 150 | 鸢尾花分类（含拼写错误） |
| `clustering_sample.csv` | 聚类 | 300 | 客户分群（无标签） |

## 项目结构

```
├── app.py              # 主程序入口
├── config.py            # 全局配置
├── modules/
│   ├── data_loader.py   # 数据上传与读取
│   ├── data_cleaner.py  # 自动数据清洗
│   ├── auto_model.py    # 自动建模引擎
│   ├── visualizer.py    # Nature 风格可视化
│   └── insight.py       # 结论自动生成
├── assets/style.css     # 自定义样式
├── docs/                # 规范文档
├── test_data/           # 测试数据集
├── setup.bat            # 一键安装启动
└── 启动平台.bat          # 快速启动
```

## 技术栈

- **UI**: Streamlit
- **数据**: pandas / numpy
- **建模**: scikit-learn
- **可视化**: matplotlib + seaborn（Nature 期刊风格）
- **运行**: Windows 10/11，Python 3.10+

## 许可

MIT License
