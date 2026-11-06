@echo off
chcp 65001 > nul
title ZMRobo Data Viewer

cd /d "%~dp0"

echo ========================================================
echo   ZMROBO DATA VIEWER - GIAO DIEN XEM DU LIEU
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren he thong!
    echo Vui long cai dat Python de khoi chay may chu xem du lieu.
    echo.
    pause
    exit /b 1
)

echo Dang khoi dong may chu web va mo trinh duyet...
echo.

python server.py

pause

