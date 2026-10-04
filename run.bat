@echo off
chcp 65001 > nul
title YouTube Stream Downloader

echo ========================================================
echo        YOUTUBE STREAM & VIDEO DOWNLOADER
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Checking environment and starting application...
python main.py %*

if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code: %errorlevel%
    pause
)
