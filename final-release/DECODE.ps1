# Aniner EXE Decoder - Base64 to EXE
# این فایل متنی رو به EXE واقعی تبدیل میکنه

Write-Host "🔥 Aniner EXE Decoder" -ForegroundColor Cyan
Write-Host "در حال تبدیل Base64 به EXE واقعی..." -ForegroundColor Yellow

# Check if b64 file exists
if (!(Test-Path "Aniner.exe.b64.txt")) {
    Write-Host "❌ فایل Aniner.exe.b64.txt پیدا نشد!" -ForegroundColor Red
    Write-Host "این فایل رو از همین پوشه دانلود کن" -ForegroundColor Yellow
    pause
    exit
}

# Decode
$b64 = Get-Content "Aniner.exe.b64.txt" -Raw
$bytes = [Convert]::FromBase64String($b64)
[IO.File]::WriteAllBytes("Aniner.exe", $bytes)

Write-Host "✅ Aniner.exe ساخته شد! (838KB - واقعی)" -ForegroundColor Green
Write-Host "📁 حجم: $((Get-Item Aniner.exe).Length) bytes" -ForegroundColor Cyan

# Also decode dll if exists
if (Test-Path "WebView2Loader.dll.b64.txt") {
    $b64dll = Get-Content "WebView2Loader.dll.b64.txt" -Raw
    $bytesdll = [Convert]::FromBase64String($b64dll)
    [IO.File]::WriteAllBytes("WebView2Loader.dll", $bytesdll)
    Write-Host "✅ WebView2Loader.dll ساخته شد!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 حالا می‌تونی Aniner.exe رو اجرا کنی!" -ForegroundColor Yellow
Write-Host "برای آیکون دسکتاپ: Aniner-Setup.exe رو اجرا کن" -ForegroundColor Yellow
pause
