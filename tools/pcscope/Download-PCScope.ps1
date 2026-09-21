<#
.SYNOPSIS
    Downloads PCScope from this repository's GitHub release, verifies its
    checksum and starts it.

.DESCRIPTION
    Right-click this file and choose "Run with PowerShell", or run it from a
    terminal:

        powershell -NoProfile -ExecutionPolicy Bypass -File .\Download-PCScope.ps1

    The script downloads PCScope.exe together with SHA256SUMS.txt from the
    release, compares the SHA-256 hash, unblocks the file (so Windows stops
    treating it as downloaded from the internet) and launches the app.

    Persian: این اسکریپت فایل PCScope.exe را از نسخه منتشرشده روی گیت‌هاب
    می‌گیرد، چک‌سام آن را بررسی می‌کند و برنامه را اجرا می‌کند.
#>

[CmdletBinding()]
param(
    # Release tag to download, for example pcscope-v1.0.0
    [string] $Tag = "pcscope-v1.0.0",
    # Repository that hosts the release
    [string] $Repo = "metamapappir-blip/web-app",
    # Where to save the executable
    [string] $Destination = (Join-Path $env:USERPROFILE "Desktop"),
    # Ask for elevation so temperature and fan sensors are available
    [switch] $AsAdministrator,
    # Download only, do not start the app
    [switch] $DownloadOnly
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$base = "https://github.com/$Repo/releases/download/$Tag"
$exeUrl = "$base/PCScope.exe"
$sumUrl = "$base/SHA256SUMS.txt"
$exePath = Join-Path $Destination "PCScope.exe"
$sumPath = Join-Path $Destination "SHA256SUMS.txt"

if (-not (Test-Path -LiteralPath $Destination)) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

function Get-ReleaseFile {
    param([string] $Url, [string] $OutFile)
    Write-Host "Downloading $Url" -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
    }
    catch {
        # PowerShell 7 does not need -UseBasicParsing
        Invoke-WebRequest -Uri $Url -OutFile $OutFile
    }
}

try {
    Get-ReleaseFile -Url $exeUrl -OutFile $exePath

    Write-Host "Checking the download against the published checksum..." -ForegroundColor Cyan
    Get-ReleaseFile -Url $sumUrl -OutFile $sumPath
    $expected = (Get-Content -LiteralPath $sumPath |
        Where-Object { $_ -match "PCScope\.exe" } |
        Select-Object -First 1) -split "\s+" | Select-Object -First 1
    Remove-Item -LiteralPath $sumPath -Force -ErrorAction SilentlyContinue

    $actual = (Get-FileHash -LiteralPath $exePath -Algorithm SHA256).Hash
    if ($expected -and ($actual -ine $expected)) {
        Remove-Item -LiteralPath $exePath -Force -ErrorAction SilentlyContinue
        throw "Checksum mismatch: expected $expected but got $actual. The download was removed."
    }
    Write-Host "Checksum OK ($actual)" -ForegroundColor Green

    Unblock-File -LiteralPath $exePath -ErrorAction SilentlyContinue
    Write-Host "Saved to $exePath" -ForegroundColor Green

    if (-not $DownloadOnly) {
        Write-Host "Starting PCScope..." -ForegroundColor Cyan
        if ($AsAdministrator) {
            Start-Process -FilePath $exePath -Verb RunAs
        }
        else {
            Start-Process -FilePath $exePath
        }
    }
}
catch {
    Write-Host ""
    Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "You can also get the file by hand from:" -ForegroundColor Yellow
    Write-Host "  https://github.com/$Repo/releases/tag/$Tag" -ForegroundColor Yellow
    exit 1
}

if (-not $DownloadOnly) {
    Write-Host ""
    Write-Host "Tip: run it with -AsAdministrator if you want temperature and fan readings." -ForegroundColor DarkGray
}
