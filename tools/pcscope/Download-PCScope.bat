@echo off
rem Downloads PCScope from the releases of this repository, verifies its
rem checksum and starts it. Just double-click this file.
rem
rem Persian: با دو بار کلیک روی این فایل، PCScope دانلود، بررسی و اجرا می‌شود.

setlocal
set "SCRIPT=%~dp0Download-PCScope.ps1"

if not exist "%SCRIPT%" (
    echo Download-PCScope.ps1 not found next to this file.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" %*
if errorlevel 1 (
    echo.
    echo If Windows blocked the download, get the file by hand from:
    echo   https://github.com/metamapappir-blip/web-app/releases/tag/pcscope-v1.0.0
)

pause
endlocal
