@echo off
title AutoMathModel

echo.
echo   AutoMathModel - Launching...
echo   http://localhost:8501
echo   Close this window to stop
echo.

python -m streamlit run app.py --server.port 8501
