@echo off
chcp 65001 >nul
title 自动化数学建模平台

echo.
echo   🔬 自动化数学建模平台
echo   ─────────────────────
echo   正在启动，服务器就绪后自动打开浏览器...
echo   关闭此窗口即可停止
echo.

python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
