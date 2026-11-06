@echo off
chcp 65001 > nul
title ZMRobo Data Viewer

cd /d "%~dp0"

echo ========================================================
echo   ZMROBO DATA VIEWER - GIAO DIEN XEM DU LIEU
echo   [CHE DO KHONG CACHE - DOC 100%% ANH MOI TU O CUNG]
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

:: Giai phong cong 8080 neu co tien trinh server cu dang chay ngam
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>nul

echo Dang khoi dong may chu web va mo trinh duyet...
echo.

python tools\server.py

pause

