@echo off
title AutoMathModel - Setup

echo.
echo   =========================================
echo     AutoMathModel - One-Click Setup
echo   =========================================
echo.

echo [1/3] Checking Python...
python --version >nul 2>&1
if %errorlevel%==0 (
    python --version
    echo         OK
    goto :install_deps
)

echo         Python not found. Trying auto-install...
echo.

winget --version >nul 2>&1
if %errorlevel%==0 (
    echo         Installing Python 3.12 via winget...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    echo         Done! Please re-run setup.bat
    pause
    exit /b 0
)

echo   Python not found. Please install Python 3.12:
echo.
echo     1. Visit https://www.python.org/downloads/
echo     2. Download Python 3.12 and install
echo     3. MUST check "Add Python to PATH"
echo     4. Re-run setup.bat
echo.
pause
exit /b 1

:install_deps
echo.
echo [2/3] Installing dependencies (may take a few minutes)...
echo.
python -m pip install streamlit pandas numpy scikit-learn matplotlib seaborn openpyxl scipy
if %errorlevel%==0 (
    echo.
    echo         OK
) else (
    echo.
    echo         WARNING: Some packages failed, trying to continue...
)

echo.
echo [3/3] Starting server...
echo.
echo   http://localhost:8501
echo   Browser will open when ready
echo   Close this window to stop
echo.

python -m streamlit run app.py --server.port 8501

pause
