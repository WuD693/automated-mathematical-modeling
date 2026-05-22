@echo off
chcp 65001 >nul
title 自动化数学建模平台

echo.
echo   🔬 自动化数学建模平台
echo   ─────────────────────
echo.
echo   正在启动...
echo   http://localhost:8501
echo   关闭此窗口即可停止
echo.

start "" http://localhost:8501
streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
