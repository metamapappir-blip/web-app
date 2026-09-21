# Aniner Browser - Create Desktop Shortcut PowerShell Script
# این اسکریپت آیکون Aniner را روی دسکتاپ می‌سازد

$WshShell = New-Object -comObject WScript.Shell
$Desktop = $WshShell.SpecialFolders.Item("Desktop")
$ShortcutPath = "$Desktop\Aniner Browser.lnk"

# Find Aniner.exe
$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetPath = "$CurrentDir\Aniner.exe"
if (!(Test-Path $TargetPath)) {
    $TargetPath = "$env:ProgramFiles\Aniner\Aniner.exe"
}
if (!(Test-Path $TargetPath)) {
    $TargetPath = "$PSScriptRoot\Aniner.exe"
}

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = Split-Path $TargetPath
$Shortcut.Description = "Aniner - مرورگر فوق خفن نسل جدید"
$Shortcut.IconLocation = "$CurrentDir\icon.ico"
if (!(Test-Path $Shortcut.IconLocation)) {
    $Shortcut.IconLocation = $TargetPath
}
$Shortcut.Save()

Write-Host "✅ آیکون Aniner روی دسکتاپ ساخته شد!" -ForegroundColor Green
Write-Host "📁 مسیر: $ShortcutPath" -ForegroundColor Cyan
Write-Host "🚀 برای اجرا روی آیکون دابل کلیک کن!" -ForegroundColor Yellow
Pause
