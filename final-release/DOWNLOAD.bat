@echo off
echo 🔥 Aniner Browser - دانلود مستقیم EXE واقعی
echo.

echo [1/3] دانلود Aniner.exe (838KB)...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/metamapappir-blip/web-app/arena/01a0c5f0-web-app/final-release/Aniner.exe' -OutFile 'Aniner.exe'"
if exist Aniner.exe (
    echo ✅ Aniner.exe دانلود شد!
) else (
    echo ❌ خطا - از لینک دستی دانلود کن:
    echo https://github.com/metamapappir-blip/web-app/raw/arena/01a0c5f0-web-app/final-release/Aniner.exe
)

echo [2/3] دانلود WebView2Loader.dll...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/metamapappir-blip/web-app/arena/01a0c5f0-web-app/final-release/WebView2Loader.dll' -OutFile 'WebView2Loader.dll'"

echo [3/3] دانلود نصاب با آیکون دسکتاپ...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/metamapappir-blip/web-app/arena/01a0c5f0-web-app/final-release/Aniner-Setup.exe' -OutFile 'Aniner-Setup.exe'"

echo.
echo ✅ تمام فایل‌ها دانلود شد!
echo 📁 فایل‌ها: Aniner.exe, Aniner-Setup.exe, WebView2Loader.dll
echo 🖥️ برای آیکون دسکتاپ: Aniner-Setup.exe رو اجرا کن
echo.
pause
