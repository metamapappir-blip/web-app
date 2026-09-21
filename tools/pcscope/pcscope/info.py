"""Hardware inventory: CPU, board, memory, storage, GPU, display, network.

Everything is best effort: a machine that blocks WMI, a Linux box or a VM
simply gets fewer rows instead of an error.
"""

from __future__ import annotations

import os
import platform
import re
import socket
from typing import Any, Dict, List, Optional

import psutil

from . import util
from .results import INFO, PASS, Result, Row, WARN

# SMBIOS memory type codes (DDR generation).
_MEMORY_TYPES = {
    20: "DDR",
    21: "DDR2",
    22: "DDR2 FB-DIMM",
    24: "DDR3",
    26: "DDR4",
    27: "LPDDR4",
    34: "DDR5",
    35: "LPDDR5",
}


# --------------------------------------------------------------------------- #
# CPU
# --------------------------------------------------------------------------- #
def cpu_name() -> str:
    name = ""
    if util.IS_WINDOWS:
        rows = util.wmi(
            "Win32_Processor",
            ["Name", "MaxClockSpeed", "NumberOfCores", "NumberOfLogicalProcessors",
             "L2CacheSize", "L3CacheSize", "SocketDesignation"],
        )
        if rows:
            name = util.clean_str(rows[0].get("Name"))
    elif util.IS_LINUX:
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if "model name" in line:
                        name = line.split(":", 1)[1].strip()
                        break
        except OSError:
            name = ""
    elif util.IS_MAC:
        _code, out, _err = util.run(["sysctl", "-n", "machdep.cpu.brand_string"])
        name = out
    if not name:
        name = util.clean_str(platform.processor()) or util.clean_str(platform.machine())
    return re.sub(r"\s+", " ", name).strip()


def cpu_details() -> Dict[str, Any]:
    details: Dict[str, Any] = {
        "name": cpu_name(),
        "physical": psutil.cpu_count(logical=False),
        "logical": psutil.cpu_count(logical=True),
        "max_mhz": None,
        "l2_kb": None,
        "l3_kb": None,
        "virtualization": None,
    }
    if util.IS_WINDOWS:
        rows = util.wmi("Win32_Processor", ["MaxClockSpeed", "L2CacheSize", "L3CacheSize",
                                            "VirtualizationFirmwareEnabled"])
        if rows:
            row = rows[0]
            details["max_mhz"] = _as_float(row.get("MaxClockSpeed"))
            details["l2_kb"] = _as_float(row.get("L2CacheSize"))
            details["l3_kb"] = _as_float(row.get("L3CacheSize"))
            details["virtualization"] = row.get("VirtualizationFirmwareEnabled")
    try:
        freq = psutil.cpu_freq()
        if freq:
            details["current_mhz"] = round(freq.current, 1)
            details["max_mhz"] = details["max_mhz"] or round(freq.max, 1) if freq.max else details["max_mhz"]
    except Exception:
        details["current_mhz"] = None
    return details


def _as_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# board / bios / machine
# --------------------------------------------------------------------------- #
def machine_info() -> Dict[str, str]:
    info = {"vendor": "", "model": "", "board": "", "bios": "", "serial": ""}
    if not util.IS_WINDOWS:
        info["model"] = platform.node()
        return info
    rows = util.wmi("Win32_ComputerSystemProduct", ["Vendor", "Name", "Version"])
    if rows:
        info["vendor"] = util.clean_str(rows[0].get("Vendor"))
        info["model"] = util.clean_str(rows[0].get("Name")) or util.clean_str(rows[0].get("Version"))
    boards = util.wmi("Win32_BaseBoard", ["Manufacturer", "Product"])
    if boards:
        vendor = util.clean_str(boards[0].get("Manufacturer"))
        product = util.clean_str(boards[0].get("Product"))
        info["board"] = " ".join(part for part in (vendor, product) if part)
    bioses = util.wmi("Win32_BIOS", ["Manufacturer", "SMBIOSBIOSVersion", "ReleaseDate"])
    if bioses:
        version = util.clean_str(bioses[0].get("SMBIOSBIOSVersion"))
        vendor = util.clean_str(bioses[0].get("Manufacturer"))
        date = util.clean_str(bioses[0].get("ReleaseDate"))
        if date and len(date) >= 8 and date[:8].isdigit():
            date = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
        info["bios"] = " ".join(part for part in (vendor, version, f"({date})" if date else "") if part)
    systems = util.wmi("Win32_ComputerSystem", ["Manufacturer", "Model", "SystemFamily"])
    if systems:
        info["vendor"] = info["vendor"] or util.clean_str(systems[0].get("Manufacturer"))
        info["model"] = info["model"] or util.clean_str(systems[0].get("Model"))
    return info


# --------------------------------------------------------------------------- #
# memory
# --------------------------------------------------------------------------- #
def memory_modules() -> List[Dict[str, Any]]:
    modules: List[Dict[str, Any]] = []
    if not util.IS_WINDOWS:
        return modules
    props = ["BankLabel", "Capacity", "Speed", "ConfiguredClockSpeed",
             "Manufacturer", "PartNumber", "SMBIOSMemoryType"]
    for row in util.wmi("Win32_PhysicalMemory", props):
        capacity = _as_float(row.get("Capacity"))
        modules.append(
            {
                "slot": util.clean_str(row.get("BankLabel")),
                "capacity": capacity,
                "speed": _as_float(row.get("ConfiguredClockSpeed")) or _as_float(row.get("Speed")),
                "vendor": util.clean_str(row.get("Manufacturer")),
                "part": util.clean_str(row.get("PartNumber")),
                "type": _MEMORY_TYPES.get(int(_as_float(row.get("SMBIOSMemoryType")) or 0), ""),
            }
        )
    return modules


def memory_info() -> Dict[str, Any]:
    try:
        vm = psutil.virtual_memory()
        total = vm.total
        used_pct = vm.percent
    except Exception:
        total, used_pct = 0, None
    modules = memory_modules()
    installed = sum(m["capacity"] or 0 for m in modules) or None
    info: Dict[str, Any] = {
        "total": total,
        "used_percent": used_pct,
        "modules": modules,
        "installed": installed,
        "slots_used": len(modules),
        "type": modules[0]["type"] if modules and modules[0]["type"] else "",
        "speed": modules[0]["speed"] if modules and modules[0]["speed"] else None,
    }
    try:
        swap = psutil.swap_memory()
        info["swap_total"] = swap.total
    except Exception:
        info["swap_total"] = 0
    return info


# --------------------------------------------------------------------------- #
# storage
# --------------------------------------------------------------------------- #
def storage_info() -> List[Dict[str, Any]]:
    """Physical drives (model/media/health) merged with mounted volumes."""
    drives: List[Dict[str, Any]] = []
    physical: List[Dict[str, Any]] = []
    if util.IS_WINDOWS:
        script = (
            "$ErrorActionPreference='SilentlyContinue'; "
            "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,BusType,HealthStatus,"
            "OperationalStatus,Size,SerialNumber | ConvertTo-Json -Depth 3 -Compress"
        )
        for row in util.parse_json_objects(util.powershell(script, timeout=25)):
            physical.append(
                {
                    "model": util.clean_str(row.get("FriendlyName")),
                    "media": util.clean_str(row.get("MediaType")),
                    "bus": util.clean_str(row.get("BusType")),
                    "health": util.clean_str(row.get("HealthStatus")),
                    "status": util.clean_str(row.get("OperationalStatus")),
                    "size": _as_float(row.get("Size")),
                    "serial": util.clean_str(row.get("SerialNumber")),
                }
            )
        if not physical:  # older PowerShell / no elevation
            for row in util.wmi("Win32_DiskDrive", ["Model", "InterfaceType", "Size", "MediaType"]):
                physical.append(
                    {
                        "model": util.clean_str(row.get("Model")),
                        "media": util.clean_str(row.get("MediaType")),
                        "bus": util.clean_str(row.get("InterfaceType")),
                        "health": "",
                        "status": "",
                        "size": _as_float(row.get("Size")),
                        "serial": "",
                    }
                )
    else:
        for row in _linux_disks():
            physical.append(row)

    volumes: List[Dict[str, Any]] = []
    seen = set()
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except Exception:
            continue
        key = part.device
        if key in seen:
            continue
        seen.add(key)
        volumes.append(
            {
                "device": part.device,
                "mount": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
                "system": _is_system_drive(part.mountpoint),
            }
        )

    for vol in volumes:
        drive = dict(vol)
        match = _match_physical(vol, physical)
        drive.update(
            {
                "model": match.get("model") or vol["device"],
                "media": match.get("media") or "",
                "bus": match.get("bus") or "",
                "health": match.get("health") or "",
                "status": match.get("status") or "",
                "capacity": match.get("size") or vol["total"],
            }
        )
        drives.append(drive)
    if not drives and physical:
        for item in physical:
            drives.append(
                {
                    "device": "", "mount": "", "fstype": "", "total": item.get("size") or 0,
                    "used": 0, "free": 0, "percent": None, "system": False,
                    "model": item.get("model", ""), "media": item.get("media", ""),
                    "bus": item.get("bus", ""), "health": item.get("health", ""),
                    "status": item.get("status", ""), "capacity": item.get("size"),
                }
            )
    return drives


def _is_system_drive(mount: str) -> bool:
    if util.IS_WINDOWS:
        drive = os.path.splitdrive(os.path.abspath(mount))[0].upper()
        sys_drive = os.path.splitdrive(os.environ.get("SystemDrive", "C:"))[0].upper()
        return bool(drive) and drive == sys_drive
    return mount == os.sep


def _match_physical(volume: Dict[str, Any], physical: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not physical:
        return {}
    if len(physical) == 1:
        return physical[0]
    # Windows: match "\\.\PHYSICALDRIVE0" order with the disk index when possible.
    device = volume.get("device", "")
    match = re.search(r"PHYSICALDRIVE(\d+)", device, re.IGNORECASE)
    if match and util.IS_WINDOWS:
        index = int(match.group(1))
        letters = util.parse_json_objects(
            util.powershell(
                "$ErrorActionPreference='SilentlyContinue'; "
                "Get-Disk | Select-Object Number,SerialNumber,FriendlyName | ConvertTo-Json -Depth 3 -Compress"
            )
        )
        serial = ""
        for row in letters:
            if str(row.get("Number")) == str(index):
                serial = util.clean_str(row.get("SerialNumber"))
                break
        for item in physical:
            if serial and item.get("serial") and item["serial"] == serial:
                return item
    return physical[0]


def _linux_disks() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    code, text, _err = util.run(["lsblk", "-dno", "MODEL,SIZE,TYPE"], timeout=10)
    if code != 0:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.rsplit(None, 2)  # MODEL SIZE TYPE
        if not parts:
            continue
        model = parts[0].strip() if len(parts) == 3 else ""
        if model in ("0", ""):
            model = ""
        out.append(
            {
                "model": model.strip(),
                "media": "",
                "bus": "",
                "health": "",
                "status": "",
                "size": None,
                "serial": "",
            }
        )
    return out


def system_drive() -> Dict[str, Any]:
    drives = storage_info()
    for drive in drives:
        if drive.get("system"):
            return drive
    for drive in drives:
        if drive.get("mount") == os.sep or (util.IS_WINDOWS and drive.get("mount", "").endswith(":\\")):
            return drive
    return drives[0] if drives else {}


# --------------------------------------------------------------------------- #
# gpu / display
# --------------------------------------------------------------------------- #
def gpu_info() -> List[Dict[str, Any]]:
    gpus: List[Dict[str, Any]] = []
    if util.IS_WINDOWS:
        props = ["Name", "DriverVersion", "AdapterRAM", "VideoProcessor", "DriverDate",
                 "CurrentHorizontalResolution", "CurrentVerticalResolution", "CurrentRefreshRate"]
        for row in util.wmi("Win32_VideoController", props):
            vram = _as_float(row.get("AdapterRAM"))
            if vram is not None and vram > 0:
                # Some drivers report 32-bit truncated values below 1 GB.
                if vram < 256 * 1024 * 1024:
                    vram = None
            gpus.append(
                {
                    "name": util.clean_str(row.get("Name")),
                    "driver": util.clean_str(row.get("DriverVersion")),
                    "vram": vram,
                    "processor": util.clean_str(row.get("VideoProcessor")),
                    "driver_date": util.clean_str(row.get("DriverDate")),
                }
            )
    elif util.IS_MAC:
        _code, out, _err = util.run(["system_profiler", "SPDisplaysDataType"], timeout=20)
        name = ""
        vram = None
        for line in out.splitlines():
            stripped = line.strip()
            if stripped.endswith(":") and "Chipset" not in stripped and name == "":
                if stripped.lower().startswith(("nvidia", "amd", "radeon", "intel", "apple")):
                    name = stripped[:-1]
            if stripped.startswith("VRAM"):
                vram = _as_float(stripped.split(":")[-1].strip().split()[0])
                if vram:
                    vram *= 1024 * 1024
        if name:
            gpus.append({"name": name, "driver": "", "vram": vram, "processor": "", "driver_date": ""})
    else:  # Linux - best effort through lspci
        _code, out, _err = util.run(["lspci"], timeout=10)
        for line in out.splitlines():
            if re.search(r"VGA compatible controller|3D controller", line):
                gpus.append(
                    {
                        "name": line.split(":", 2)[-1].strip(),
                        "driver": "",
                        "vram": None,
                        "processor": "",
                        "driver_date": "",
                    }
                )
    return gpus


def display_info() -> Dict[str, Any]:
    """Primary monitor size, refresh rate, DPI and monitor count."""
    out: Dict[str, Any] = {
        "width": None,
        "height": None,
        "refresh": None,
        "dpi": None,
        "count": None,
        "scaling": None,
    }
    if not util.IS_WINDOWS:
        return out
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        out["count"] = int(user32.GetSystemMetrics(80))  # SM_CMONITORS
        out["width"] = int(user32.GetSystemMetrics(0))
        out["height"] = int(user32.GetSystemMetrics(1))

        class DEVMODEW(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", wintypes.WCHAR * 32),
                ("dmSpecVersion", wintypes.WORD),
                ("dmDriverVersion", wintypes.WORD),
                ("dmSize", wintypes.WORD),
                ("dmDriverExtra", wintypes.WORD),
                ("dmFields", wintypes.DWORD),
                ("dmOrientation", ctypes.c_short),
                ("dmPaperSize", ctypes.c_short),
                ("dmPaperLength", ctypes.c_short),
                ("dmPaperWidth", ctypes.c_short),
                ("dmScale", ctypes.c_short),
                ("dmCopies", ctypes.c_short),
                ("dmDefaultSource", ctypes.c_short),
                ("dmPrintQuality", ctypes.c_short),
                ("dmPositionX", ctypes.c_long),
                ("dmPositionY", ctypes.c_long),
                ("dmDisplayOrientation", wintypes.DWORD),
                ("dmDisplayFixedOutput", wintypes.DWORD),
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", wintypes.WCHAR * 32),
                ("dmLogPixels", wintypes.WORD),
                ("dmBitsPerPel", wintypes.DWORD),
                ("dmPelsWidth", wintypes.DWORD),
                ("dmPelsHeight", wintypes.DWORD),
                ("dmDisplayFlags", wintypes.DWORD),
                ("dmDisplayFrequency", wintypes.DWORD),
                # The remaining fields are unused here, but the structure must
                # match sizeof(DEVMODEW) exactly: EnumDisplaySettings writes the
                # whole thing, and a short buffer would corrupt memory.
                ("dmICMMethod", wintypes.DWORD),
                ("dmICMIntent", wintypes.DWORD),
                ("dmMediaType", wintypes.DWORD),
                ("dmDitherType", wintypes.DWORD),
                ("dmReserved1", wintypes.DWORD),
                ("dmReserved2", wintypes.DWORD),
                ("dmPanningWidth", wintypes.DWORD),
                ("dmPanningHeight", wintypes.DWORD),
            ]

        # Oversized backing buffer: EnumDisplaySettings writes sizeof(DEVMODEW)
        # bytes, and a short buffer would corrupt memory.
        buffer = ctypes.create_string_buffer(1024)
        dm = ctypes.cast(buffer, ctypes.POINTER(DEVMODEW)).contents
        dm.dmSize = ctypes.sizeof(DEVMODEW)
        try:
            if user32.EnumDisplaySettingsW(None, 0xFFFFFFFF, ctypes.byref(dm)):  # ENUM_CURRENT_SETTINGS
                out["width"] = int(dm.dmPelsWidth) or out["width"]
                out["height"] = int(dm.dmPelsHeight) or out["height"]
                out["refresh"] = int(dm.dmDisplayFrequency) or None
        except Exception:
            pass
        try:
            hdc = user32.GetDC(0)
            if hdc:
                try:
                    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                    if dpi:
                        out["dpi"] = int(dpi)
                        out["scaling"] = round(100.0 * dpi / 96.0)
                finally:
                    user32.ReleaseDC(0, hdc)
        except Exception:
            pass
    except Exception:
        pass
    return out


# --------------------------------------------------------------------------- #
# network adapters
# --------------------------------------------------------------------------- #
def network_adapters() -> List[Dict[str, Any]]:
    adapters: List[Dict[str, Any]] = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    for name, stat in stats.items():
        if name.lower().startswith(("lo", "loopback")):
            continue
        ipv4 = ""
        ipv6 = ""
        mac = ""
        for addr in addrs.get(name, []):
            if addr.family == socket.AF_INET:
                ipv4 = addr.address
            elif getattr(socket, "AF_INET6", object()) == addr.family:
                ipv6 = addr.address.split("%")[0]
            elif addr.family == psutil.AF_LINK:
                mac = addr.address
        kind = "Wi-Fi" if _is_wireless(name) else ("Ethernet" if _is_ethernet(name) else "")
        adapters.append(
            {
                "name": name,
                "up": bool(stat.isup),
                "speed_mbps": stat.speed if stat.speed and stat.speed > 0 else None,
                "mtu": stat.mtu,
                "duplex": stat.duplex,
                "ipv4": ipv4,
                "ipv6": ipv6,
                "mac": mac,
                "kind": kind,
                "ssid": wifi_ssid() if kind == "Wi-Fi" else "",
            }
        )
    if not adapters:
        for name in addrs:
            adapters.append(
                {"name": name, "up": False, "speed_mbps": None, "mtu": None, "duplex": 0,
                 "ipv4": "", "ipv6": "", "mac": "", "kind": "", "ssid": ""}
            )
    # Prefer connected adapters with an IPv4 address.
    adapters.sort(key=lambda item: (not item["up"], not item["ipv4"]))
    return adapters


def _is_wireless(name: str) -> bool:
    lowered = name.lower()
    if any(token in lowered for token in ("wi-fi", "wifi", "wlan", "wireless", "802.11", "airport")):
        return True
    if not util.IS_WINDOWS:
        return False
    rows = util.wmi("Win32_NetworkAdapter", ["NetConnectionID", "Name", "AdapterTypeID", "InterfaceType"], timeout=15)
    for row in rows:
        if util.clean_str(row.get("NetConnectionID")) == name:
            return str(row.get("InterfaceType", "")) == "802.11" or str(row.get("AdapterTypeID", "")) == "9"
    return False


def _is_ethernet(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("ethernet", "eth", "en0", "en1", "local area connection"))


def wifi_ssid() -> str:
    if not util.IS_WINDOWS:
        if util.IS_MAC:
            _code, out, _err = util.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                timeout=10,
            )
            for line in out.splitlines():
                if " SSID:" in line:
                    return line.split(":", 1)[1].strip()
        return ""
    script = (
        "$ErrorActionPreference='SilentlyContinue'; "
        "(netsh wlan show interfaces) -match '\\sSSID' | ForEach-Object { ($_ -split ':',2)[1].Trim() }"
    )
    out = util.powershell(script, timeout=15)
    for line in out.splitlines():
        line = line.strip()
        if line and "BSSID" not in line.upper():
            return line
    return ""


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #
def collect_system_result() -> Result:
    res = Result(id="system", title_key="test.system")
    cpu = cpu_details()
    machine = machine_info()
    mem = memory_info()
    drives = storage_info()
    gpus = gpu_info()
    display = display_info()
    boot = None
    try:
        boot = psutil.boot_time()
    except Exception:
        pass

    cores = cpu.get("physical") or 0
    threads = cpu.get("logical") or 0
    res.add("key.machine", " ".join(p for p in (machine.get("vendor"), machine.get("model")) if p) or platform.node())
    res.add("key.motherboard", machine.get("board") or "-")
    res.add("key.bios", machine.get("bios") or "-")
    res.add("key.cpu", cpu.get("name") or "-")
    res.add("key.cpu_cores", f"{cores}C / {threads}T" if cores and threads else str(threads or "-"))
    if cpu.get("max_mhz"):
        res.add("key.cpu_base", f"{cpu['max_mhz'] / 1000:.2f} GHz")
    if cpu.get("l2_kb") or cpu.get("l3_kb"):
        cache_parts = []
        if cpu.get("l2_kb"):
            cache_parts.append(f"L2 {cpu['l2_kb'] / 1024:.1f} MB")
        if cpu.get("l3_kb"):
            cache_parts.append(f"L3 {cpu['l3_kb'] / 1024:.1f} MB")
        res.add("key.cache", " / ".join(cache_parts))
    res.add("key.ram_total", util.human_bytes(mem.get("total")))
    if mem.get("slots_used"):
        detail_parts = []
        for module in mem["modules"]:
            detail_parts.append(
                " ".join(
                    p for p in (
                        util.human_bytes(module.get("capacity")),
                        module.get("type") or "",
                        f"{int(module['speed'])} MT/s" if module.get("speed") else "",
                    ) if p
                )
            )
        res.add("key.ram_modules", f"{mem['slots_used']}x " + " / ".join(detail_parts))
    for index, gpu in enumerate(gpus[:3]):
        label = "key.gpu" if index == 0 else "key.gpu"
        value = gpu.get("name") or "-"
        if gpu.get("vram"):
            value += f" ({util.human_bytes(gpu['vram'])})"
        res.add(label, value)
    for drive in drives[:4]:
        text = " ".join(
            p for p in (
                drive.get("model") or drive.get("device"),
                drive.get("media") or "",
                util.human_bytes(drive.get("capacity") or drive.get("total")),
            ) if p
        )
        res.add("key.disk", text or "-")
    if display.get("width") and display.get("height"):
        display_text = f"{display['width']}x{display['height']}"
        if display.get("refresh"):
            display_text += f" @ {display['refresh']} Hz"
        if display.get("scaling"):
            display_text += f" ({display['scaling']}%)"
        if display.get("count"):
            display_text += f" x{display['count']}"
        res.add("key.display", display_text)
    res.add("key.os", util.windows_build() if util.IS_WINDOWS else platform.platform())
    res.add("key.uptime", util.human_uptime(boot))

    status = PASS
    if mem.get("total") and mem["total"] < 4 * 1024 ** 3:
        status = WARN
        res.add("note.low_ram", util.human_bytes(mem.get("total")), status=WARN)
    if cores and cores <= 2:
        status = WARN
        res.add("note.few_cores", "", status=WARN)
    for drive in drives:
        free_pct = None
        if drive.get("total"):
            free_pct = 100.0 * (drive.get("free") or 0) / drive["total"]
        if free_pct is not None and free_pct < 10:
            status = WARN
            res.add("note.low_disk", f"{(drive.get('mount') or drive.get('model') or '')} {free_pct:.0f}%", status=WARN)
    res.finish(status, "verdict.ok", summary_is_key=True)
    return res


def collect_gpu_result() -> Result:
    res = Result(id="gpu", title_key="test.gpu")
    gpus = gpu_info()
    display = display_info()
    if not gpus:
        res.add("key.gpu", "-")
        res.finish(INFO, "verdict.no_sensor", summary_is_key=True)
        return res
    for gpu in gpus:
        value = gpu.get("name") or "-"
        if gpu.get("vram"):
            value += f" ({util.human_bytes(gpu['vram'])})"
        res.add("key.gpu", value)
        if gpu.get("driver"):
            res.add("key.driver", gpu["driver"])
        if gpu.get("processor"):
            res.add("key.cpu", gpu["processor"])
        if gpu.get("driver_date"):
            res.add("key.bios", gpu["driver_date"][:8])
    if display.get("width"):
        text = f"{display['width']}x{display['height']}"
        if display.get("refresh"):
            text += f" @ {display['refresh']} Hz"
        res.add("key.display", text)
        res.add("key.refresh", f"{display['refresh']} Hz" if display.get("refresh") else "-")
    if display.get("scaling"):
        res.add("key.score", f"DPI scaling {display['scaling']}%")
    if display.get("count"):
        res.add("key.state", f"{display['count']} monitor(s)")

    status = PASS
    if display.get("refresh") and display["refresh"] < 60:
        status = WARN
    res.finish(status, "verdict.ok", summary_is_key=True)
    return res


def computer_name() -> str:
    machine = machine_info()
    parts = [machine.get("vendor"), machine.get("model")]
    text = " ".join(p for p in parts if p)
    return text or platform.node()
