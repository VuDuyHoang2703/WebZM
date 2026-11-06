@echo off
chcp 65001 > nul
title ZMRobo Crawler Tool

cd /d "%~dp0"

echo ========================================================
echo   ZMROBO DATA CRAWLER
echo   Website: https://www.zmrobo.net
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren he thong!
    echo Vui long cai dat Python va tick chon "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo Dang bat dau chay tool cao du lieu...
echo.

python crawler_zmrobo.py

echo.
echo ========================================================
echo Hoan tat! Nhan phim bat ky de thoat...
echo ========================================================
pause > nul

