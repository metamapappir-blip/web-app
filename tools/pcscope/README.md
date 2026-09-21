<div align="center">

<img src="./assets/pcscope.png" width="96" alt="PCScope">

# PCScope

**A small, portable hardware tester for Windows.** One `.exe`, no installer, no
telemetry, no internet account. Pick the tests you want, press run, and export a
report you can share or keep for comparison later.

[![Version](https://img.shields.io/badge/version-1.0.0-blueviolet)](https://github.com/metamapappir-blip/web-app/releases/tag/pcscope-v1.0.0)
[![Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d6)](https://github.com/metamapappir-blip/web-app/releases/tag/pcscope-v1.0.0)
[![UI](https://img.shields.io/badge/UI-English%20%2F%20%D9%81%D8%A7%D8%B1%D8%B3%DB%8C-0ea5e9)](https://github.com/metamapappir-blip/web-app/releases/tag/pcscope-v1.0.0)

English · [فارسی](./README.fa.md)

</div>

---

## Download

Grab **`PCScope.exe`** from the
[latest release](https://github.com/metamapappir-blip/web-app/releases/tag/pcscope-v1.0.0).
Double-click it - nothing is installed, and the only file it creates outside its
own folder is the report you ask it to save.

**Direct download:** <https://github.com/metamapappir-blip/web-app/releases/download/pcscope-v1.0.0/PCScope.exe>

One-liner if you prefer PowerShell (downloads, verifies the checksum and starts it):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Download-PCScope.ps1 -AsAdministrator
```

`Download-PCScope.ps1` (and the `Download-PCScope.bat` wrapper for double-clicking)
fetch the executable from the release, compare its SHA-256 with the published
`SHA256SUMS.txt`, unblock it and launch it. Add `-DownloadOnly` to fetch without
starting, or `-Destination C:\Tools` to choose another folder.

Windows SmartScreen warns about unsigned executables from new projects: choose
**More info → Run anyway**. `SHA256SUMS.txt` in the release lets you verify the
download:

```bat
certutil -hashfile PCScope.exe SHA256
```

> **Tip:** run it **as administrator** if you want temperature and fan sensors.
> Most laptops only publish those to elevated processes.

---

## What it tests

| Test | What it does |
| --- | --- |
| **System information** | CPU, cores/threads, clocks, cache, motherboard, BIOS, installed memory and module layout, drives, GPU, display resolution and refresh rate, OS build, uptime |
| **CPU benchmark** | Single-core and multi-core integer throughput, plus how well the score scales with the number of threads |
| **Memory (RAM)** | Write/read bandwidth over a large block and a byte-for-byte integrity check |
| **Disk speed** | Sequential write/read on the system drive, random 4K mixed IOPS, and a checksum verification of everything written |
| **Disk health** | Model, media type (SSD/HDD), capacity, free space and the health status Windows reports |
| **GPU and display** | Adapter name, VRAM, driver version, screen resolution, refresh rate and DPI scaling |
| **Network** | Active adapter and Wi-Fi name, TCP latency, ping loss, download and upload speed |
| **Battery** | Charge level, time remaining, design vs. full-charge capacity, wear level and cycle count |
| **Temperature and fans** | Every thermal sensor the machine exposes, plus fan RPM where available |
| **Monitor test** | Full-screen solid colours (black → white → RGB → gray) to spot dead or stuck pixels |
| **Speaker test** | Short tones on the default output device |
| **Stability stress** | Loads all cores for 5/10/30 minutes while sampling clocks and temperature, with a live chart and throttling detection |

Every result is graded **OK / Warning / Problem / Info** and can be exported as
**HTML**, **TXT** or **JSON** (HTML keeps the Persian report right-to-left).

---

## Using it

1. Tick the tests you want (all non-interactive ones are on by default).
2. Pick the disk test size and stress length in the bottom-left corner.
3. Press **Run selected**. Long tests can be stopped at any time with **Stop**.
4. Press **Save report (HTML)** - or **Copy summary** to paste a short digest
   into a chat or ticket.

Press the **فارسی / English** button at the top right to switch language. The
Persian UI is right-aligned and shaped properly for Windows.

### Command line

`PCScopeCLI.exe` runs the same tests with no window, which is handy for
automation, remote support or a quick check from PowerShell:

```bat
PCScopeCLI.exe --all --out-dir "%USERPROFILE%\Desktop\PCScope reports"
PCScopeCLI.exe --quick --only cpu,memory,disk --lang fa --html report.html
PCScopeCLI.exe --list            :: show the test ids
PCScopeCLI.exe --all --json out.json
```

Useful flags: `--all`, `--only`, `--skip`, `--quick`, `--lang en|fa`, `--txt`,
`--html`, `--json`, `--out-dir`, `--disk-mb`, `--memory-mb`, `--stress-minutes`,
`--quiet`. The exit code is `1` when any test reports a problem, so scripts can
branch on it.

From source (no exe needed):

```bat
python main.py                 :: windowed app
python main.py --cli --all     :: headless run
```

---

## Reading the numbers

- **Compare with yourself, not with the internet.** Scores depend on power
  profile, background load, cooling and drivers. Run PCScope when the machine is
  healthy, keep the report, and compare again when something feels slow.
- **Close other programs** before the disk, memory and stress tests; they move a
  lot of data and are sensitive to background noise.
- **Disk read speeds can look inflated** on small test files because Windows
  caches data in RAM. Use the 1 GB or 2 GB setting for a number that means
  something.
- **Speed tests use Cloudflare's public endpoints** (`speed.cloudflare.com`) and
  ping `1.1.1.1` / `8.8.8.8`. Nothing about your machine is uploaded; the upload
  test posts 1 MB of random bytes that is discarded.
- **No sensor reported** for temperature is normal on many desktops and on
  laptops without the vendor's driver installed - it is not a failure.

---

## Building from source

Requires Python 3.10-3.13 (64-bit).

```bat
pip install -r requirements-build.txt
pyinstaller --noconfirm --clean pcscope.spec
```

or just run **`build.bat`**. The result lands in `dist\`:

- `PCScope.exe` - windowed GUI
- `PCScopeCLI.exe` - console build

Dependencies are deliberately tiny: `psutil` for hardware access, and
`arabic-reshaper` + `python-bidi` so Tkinter can draw Persian text.

### Tests

```bat
python tests/test_smoke.py
```

runs the full suite headlessly, including the GUI, which is exercised against a
mock `tkinter` so it works on machines (and CI runners) without a display.
The Windows build is produced by
[`.github/workflows/pcscope-build.yml`](../../.github/workflows/pcscope-build.yml),
which runs the same tests before packaging.

---

## Notes on naming and license

PCScope is an independent tool that lives in this repository; it is not part of
the Nova Proxy brand and uses none of its marks (see `TRADEMARKS.md` at the repo
root). It is distributed under the same license as this repository,
[PolyForm Noncommercial 1.0.0](../LICENSE) - free for personal and internal use,
commercial redistribution requires written permission.
