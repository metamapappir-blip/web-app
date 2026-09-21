"""Small cross-platform helpers used by PCScope.

Everything here is dependency-free (stdlib only) and degrades gracefully when a
platform does not support a query, so the same code runs on Windows (the target
of the packaged .exe), Linux and macOS (used for development and CI checks).
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Sequence

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

APP_NAME = "PCScope"
APP_VERSION = "1.0.0"

# Hide the console window of child processes when running as a frozen GUI app.
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0
_STARTUPINFO: Optional[Any] = None
if IS_WINDOWS:  # pragma: no cover - Windows only
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _STARTUPINFO.wShowWindow = 0


# --------------------------------------------------------------------------- #
# process helpers
# --------------------------------------------------------------------------- #
def run(args: Sequence[str], timeout: float = 25.0, shell: bool = False):
    """Run a command and return (returncode, stdout, stderr). Never raises."""
    try:
        proc = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            shell=shell,
            startupinfo=_STARTUPINFO,
            creationflags=CREATE_NO_WINDOW if IS_WINDOWS else 0,
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:  # noqa: BLE001 - best effort helper
        return -1, "", str(exc)


def powershell(script: str, timeout: float = 30.0) -> str:
    """Run a PowerShell snippet and return its stdout ("" on any failure)."""
    if not IS_WINDOWS:
        return ""
    code, out, _err = run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        timeout=timeout,
    )
    return out if code == 0 else ""


def parse_json_objects(text: str) -> List[Dict[str, Any]]:
    """Parse PowerShell ``ConvertTo-Json`` output into a list of dicts."""
    text = (text or "").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except Exception:
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def wmi(
    class_name: str,
    props: Optional[Sequence[str]] = None,
    namespace: Optional[str] = None,
    timeout: float = 25.0,
) -> List[Dict[str, Any]]:
    """Query a WMI/CIM class and return a list of dicts ([] anywhere else)."""
    if not IS_WINDOWS:
        return []
    select = ""
    if props:
        select = " | Select-Object -Property " + ",".join(props)
    ns = f"-Namespace '{namespace}' " if namespace else ""
    script = (
        "$ErrorActionPreference='SilentlyContinue'; "
        f"Get-CimInstance -ClassName {class_name} {ns}{select} | ConvertTo-Json -Depth 4 -Compress"
    )
    return parse_json_objects(powershell(script, timeout=timeout))


# --------------------------------------------------------------------------- #
# formatting
# --------------------------------------------------------------------------- #
def human_bytes(num: Optional[float], digits: int = 1) -> str:
    if num is None:
        return "-"
    try:
        num = float(num)
    except (TypeError, ValueError):
        return "-"
    if num < 0:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    idx = 0
    while num >= 1024 and idx < len(units) - 1:
        num /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(num)} B"
    return f"{num:.{digits}f} {units[idx]}"


def human_bits(num: Optional[float]) -> str:
    if num is None:
        return "-"
    try:
        num = float(num)
    except (TypeError, ValueError):
        return "-"
    units = ["bps", "Kbps", "Mbps", "Gbps"]
    idx = 0
    while num >= 1000 and idx < len(units) - 1:
        num /= 1000.0
        idx += 1
    return f"{num:.2f} {units[idx]}"


def human_speed_mbps(num: Optional[float]) -> str:
    if num is None:
        return "-"
    return f"{num:.1f} MB/s"


def human_duration(seconds: Optional[float]) -> str:
    if seconds is None or seconds < 0:
        return "-"
    if seconds < 1:
        return "<1s"
    seconds = int(round(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def human_uptime(boot_epoch: Optional[float]) -> str:
    if not boot_epoch:
        return "-"
    return human_duration(time.time() - boot_epoch)


def pct(value: Optional[float], total: Optional[float]) -> Optional[float]:
    try:
        if value is None or total in (None, 0):
            return None
        return 100.0 * float(value) / float(total)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def safe_round(value: Optional[float], digits: int = 1) -> Optional[float]:
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def now_stamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def stamp_for_filename() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> str:
    """Directory that holds the running program (source or frozen)."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_report_dir() -> str:
    """Where reports are written when the user does not pick a folder."""
    candidates: List[str] = []
    home = os.path.expanduser("~")
    for sub in ("Desktop", "Documents"):
        path = os.path.join(home, sub)
        if os.path.isdir(path):
            candidates.append(path)
    candidates.append(home)
    candidates.append(os.getcwd())
    for path in candidates:
        if os.path.isdir(path) and os.access(path, os.W_OK):
            return path
    return os.getcwd()


def open_path(path: str) -> bool:
    """Open a file or folder with the platform's default handler."""
    try:
        if IS_WINDOWS:
            os.startfile(path)  # type: ignore[attr-defined] # noqa: S606
        elif IS_MAC:
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def windows_build() -> str:
    """Pretty Windows version string (e.g. 'Windows 11 Pro (10.0.26100)')."""
    if not IS_WINDOWS:
        return platform.platform()
    edition = ""
    display = ""
    build = platform.version()
    try:  # read the marketing version (23H2, 24H2, ...) from the registry
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        )
        for name, target in (("ProductName", "edition"), ("DisplayVersion", "display"),
                             ("CurrentBuildNumber", "build")):
            try:
                value = winreg.QueryValueEx(key, name)[0]
            except OSError:
                continue
            if target == "edition":
                edition = str(value)
            elif target == "display":
                display = str(value)
            else:
                build = str(value)
        winreg.CloseKey(key)
    except Exception:
        edition = platform.platform()
    text = edition or "Windows"
    if display:
        text += f" {display}"
    return f"{text} (build {build})"


_UUID_RE = re.compile(r"^[0-9a-fA-F\-]{6,}$")


def clean_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return text
