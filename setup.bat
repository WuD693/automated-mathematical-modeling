@echo off
chcp 65001 >nul
title 自动化数学建模平台 — 安装启动

echo.
echo   ╔══════════════════════════════════════╗
echo   ║     🔬 自动化数学建模平台            ║
echo   ║     一键安装 + 启动                  ║
echo   ╚══════════════════════════════════════╝
echo.

:: ==========================================
:: 步骤 1：检查 Python
:: ==========================================
echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel%==0 (
    python --version
    echo         Python 已安装 ✓
    goto :install_deps
)

echo         未检测到 Python，尝试自动安装...
echo.

winget --version >nul 2>&1
if %errorlevel%==0 (
    echo         正在通过 winget 安装 Python 3.12...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    echo         Python 安装完成，请重新运行 setup.bat
    pause
    exit /b 0
)

echo.
echo   ⚠️  自动安装失败，请手动安装 Python：
echo.
echo   1. 打开 Microsoft Store，搜索 "Python 3.12"，点击安装
echo   2. 或者访问 https://www.python.org/downloads/ 下载安装
echo   3. 安装时务必勾选 "Add Python to PATH"
echo   4. 安装完成后，重新运行 setup.bat
echo.
pause
exit /b 1

:: ==========================================
:: 步骤 2：安装依赖
:: ==========================================
:install_deps
echo.
echo [2/3] 安装项目依赖（可能需要几分钟）...
echo.
python -m pip install streamlit pandas numpy scikit-learn matplotlib seaborn openpyxl scipy
if %errorlevel%==0 (
    echo.
    echo         依赖安装完成 ✓
) else (
    echo.
    echo         ⚠️ 部分依赖安装失败，尝试继续...
)
echo.
echo [3/3] 启动平台（服务器就绪后自动打开浏览器）...
echo.
echo   ┌─────────────────────────────────────┐
echo   │  等待服务器启动...                   │
echo   │  关闭此窗口即可停止服务              │
echo   └─────────────────────────────────────┘
echo.

:: 启动 Streamlit（让它自己打开浏览器）
python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

pause
