@echo off
chcp 65001 > nul
title ZMRobo Media Downloader

cd /d "%~dp0"

echo ========================================================
echo   ZMROBO MEDIA DOWNLOADER - TẢI ẢNH & ICON CỤC BỘ
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren he thong!
    echo.
    pause
    exit /b 1
)

echo Dang bat dau chay tool tai media da luong...
echo.

python download_media.py

echo.
echo ========================================================
echo Nhan phim bat ky de thoat...
echo ========================================================
pause > nul

