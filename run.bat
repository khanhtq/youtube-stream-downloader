@echo off
chcp 65001 > nul
title YouTube Stream Downloader

echo ========================================================
echo        YOUTUBE STREAM & VIDEO DOWNLOADER
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python trên hệ thống của bạn!
    echo Vui lòng cài đặt Python từ https://www.python.org/
    pause
    exit /b 1
)

echo Đang kiểm tra và khởi động chương trình...
python main.py %*

if %errorlevel% neq 0 (
    echo.
    echo Ứng dụng đã thoát với mã lỗi: %errorlevel%
    pause
)
