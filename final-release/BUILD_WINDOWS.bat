@echo off
chcp 65001 >nul
echo 🔥 Aniner Browser v2.0 - ساخت EXE واقعی ویندوز
echo ترکیبی از بهترین‌ها - PyQt + Electron + Arc + Firefox
echo.

echo [1/4] چک کردن Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python نصب نیست! از https://python.org دانلود کن
    pause
    exit /b
)
echo ✅ Python OK

echo [2/4] نصب پیش‌نیازها...
pip install PyQt5 PyQtWebEngine pyinstaller Pillow --quiet
echo ✅ پیش‌نیازها نصب شد

echo [3/4] ساخت EXE ترکیبی خفن...
cd /d "%~dp0"
pyinstaller --onefile --windowed --icon=assets/icon.ico --name Aniner-v2-Real --add-data="assets/icon.png;assets" --hidden-import=PyQt5.sip src/aniner_v2.py
if errorlevel 1 (
    echo ❌ خطا در ساخت EXE
    pause
    exit /b
)
echo ✅ EXE ساخته شد!

echo [4/4] کپی فایل‌ها...
copy /Y dist\Aniner-v2-Real.exe .\dist\Aniner-v2-Real.exe
copy /Y assets\icon.ico .\dist\
copy /Y ..\WebView2Loader.dll .\dist\ 2>nul
echo ✅ تمام!

echo.
echo 🎉 Aniner v2.0 آماده است!
echo 📁 فایل: dist\Aniner-v2-Real.exe
echo 🖥️ برای آیکون دسکتاپ: Create-Desktop-Shortcut.bat رو اجرا کن
echo ⭐ ستاره بده: https://github.com/metamapappir-blip/web-app
echo.
pause
