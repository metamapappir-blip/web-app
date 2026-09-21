@echo off
echo 🔥 Aniner Browser - ساخت آیکون دسکتاپ
echo.

set SCRIPT="%~dp0Create-Desktop-Shortcut.ps1"
powershell -ExecutionPolicy Bypass -File %SCRIPT%

pause
