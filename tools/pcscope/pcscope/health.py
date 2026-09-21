"""Health-ish probes: temperatures, fans, battery and disk health."""

from __future__ import annotations

import os
import tempfile
import time
import xml.etree.ElementTree as ElementTree
from typing import Any, Dict, List, Optional

import psutil

from . import info as sysinfo
from . import util
from .results import FAIL, INFO, PASS, WARN, Result


# --------------------------------------------------------------------------- #
# sensors
# --------------------------------------------------------------------------- #
def _psutil_temperatures() -> Dict[str, float]:
    out: Dict[str, float] = {}
    try:
        readings = psutil.sensors_temperatures() or {}
    except Exception:
        return out
    for chip, entries in readings.items():
        for entry in entries:
            label = entry.label or chip
            name = f"{chip} {label}".strip()
            try:
                out[name] = round(float(entry.current), 1)
            except (TypeError, ValueError):
                continue
    return out


def _wmi_thermal_zone() -> Dict[str, float]:
    if not util.IS_WINDOWS:
        return {}
    rows = util.wmi(
        "MSAcpi_ThermalZoneTemperature",
        ["InstanceName", "CurrentTemperature"],
        namespace="root/WMI",
        timeout=15,
    )
    out: Dict[str, float] = {}
    for index, row in enumerate(rows):
        raw = row.get("CurrentTemperature")
        try:
            celsius = float(raw) / 10.0 - 273.15
        except (TypeError, ValueError):
            continue
        if -20 <= celsius <= 130:
            out[row.get("InstanceName") or f"ThermalZone{index}"] = round(celsius, 1)
    return out


def _hardware_monitor(namespace: str) -> Dict[str, float]:
    """Read a LibreHardwareMonitor / OpenHardwareMonitor WMI namespace."""
    if not util.IS_WINDOWS:
        return {}
    script = (
        "$ErrorActionPreference='SilentlyContinue'; "
        f"Get-CimInstance -Namespace '{namespace}' -ClassName Sensor | "
        "Where-Object { $_.SensorType -eq 'Temperature' } | "
        "Select-Object Name, Identifier, Parent, Value | ConvertTo-Json -Depth 3 -Compress"
    )
    out: Dict[str, float] = {}
    for row in util.parse_json_objects(util.powershell(script, timeout=20)):
        try:
            value = float(row.get("Value"))
        except (TypeError, ValueError):
            continue
        if not -20 <= value <= 130:
            continue
        name = util.clean_str(row.get("Name")) or util.clean_str(row.get("Identifier")) or "sensor"
        out[name] = round(value, 1)
    return out


def temperatures() -> Dict[str, float]:
    """Best-effort temperature map. Empty when nothing reports a sensor."""
    for source in (
        _hardware_monitor("root\\LibreHardwareMonitor"),
        _hardware_monitor("root\\OpenHardwareMonitor"),
        _psutil_temperatures,
        _wmi_thermal_zone,
    ):
        data = source() if callable(source) else source
        if data:
            return data
    return {}


def fan_speeds() -> Dict[str, float]:
    out: Dict[str, float] = {}
    if not util.IS_WINDOWS:
        try:
            fans = psutil.sensors_fans() or {}
        except Exception:
            return out
        for chip, entries in fans.items():
            for entry in entries:
                out[f"{chip} {entry.label or ''}".strip()] = float(entry.current)
        return out
    script = (
        "$ErrorActionPreference='SilentlyContinue'; "
        "Get-CimInstance -Namespace 'root\\LibreHardwareMonitor' -ClassName Sensor | "
        "Where-Object { $_.SensorType -eq 'Fan' } | Select-Object Name,Value | ConvertTo-Json -Depth 3 -Compress"
    )
    for row in util.parse_json_objects(util.powershell(script, timeout=20)):
        try:
            value = float(row.get("Value"))
        except (TypeError, ValueError):
            continue
        out[util.clean_str(row.get("Name")) or "fan"] = round(value, 0)
    return out


def thermal_result(progress=None, stop=None) -> Result:
    res = Result(id="thermal", title_key="test.thermal")
    started = time.time()
    temps = temperatures()
    fans = fan_speeds()
    try:
        load = psutil.cpu_percent(interval=0.5)
    except Exception:
        load = None

    if temps:
        hottest = max(temps.values())
        res.add("key.state", f"{load:.0f}%" if load is not None else "-", note="CPU load")
        for name in sorted(temps, key=lambda key: -temps[key])[:8]:
            res.add("key.temperature", f"{temps[name]:.1f} °C", note=name)
    else:
        res.add("key.temperature", "verdict.no_sensor", status=INFO)
        res.add("note.admin_required", "-", status=INFO)
    for name in sorted(fans)[:6]:
        res.add("key.state", f"{fans[name]:.0f} RPM", note=name)

    status = INFO
    verdict = "verdict.idle"
    if temps:
        hottest = max(temps.values())
        status = PASS
        verdict = "verdict.normal"
        if hottest >= 90:
            status, verdict = FAIL, "verdict.high"
        elif hottest >= 80:
            status, verdict = WARN, "verdict.high"
    res.score = round(max(temps.values()), 1) if temps else None
    res.unit = "°C"
    res.duration = time.time() - started
    res.finish(status, verdict, summary_is_key=True)
    return res


# --------------------------------------------------------------------------- #
# battery
# --------------------------------------------------------------------------- #
def _battery_report() -> Dict[str, Any]:
    """Parse ``powercfg /batteryreport`` into design/full capacity and cycles."""
    out: Dict[str, Any] = {}
    if not util.IS_WINDOWS:
        return out
    path = os.path.join(tempfile.gettempdir(), f"pcscope_battery_{os.getpid()}.xml")
    code, _stdout, _stderr = util.run(
        ["powercfg", "/batteryreport", "/output", path, "/duration", "1", "/xml"],
        timeout=45,
    )
    if code != 0 or not os.path.isfile(path):
        return out
    try:
        tree = ElementTree.parse(path)
        root = tree.getroot()
        batteries = [node for node in root.iter() if util.strip_ns(node.tag) == "Battery"]
        for battery in batteries:
            data: Dict[str, Any] = {}
            for child in battery.iter():
                key = util.strip_ns(child.tag)
                if key and child.text and key not in data:
                    data[key] = child.text.strip()
            if data.get("DesignCapacity"):
                out = {
                    "design_mwh": _as_float(data.get("DesignCapacity")),
                    "full_mwh": _as_float(data.get("FullChargeCapacity")),
                    "cycles": _as_float(data.get("CycleCount")),
                    "chemistry": data.get("Chemistry", ""),
                    "manufacturer": data.get("Manufacturer", ""),
                }
                break
    except Exception:
        pass
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return out


def _as_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def battery_result(progress=None, stop=None) -> Result:
    res = Result(id="battery", title_key="test.battery")
    started = time.time()
    battery = None
    try:
        battery = psutil.sensors_battery()
    except Exception:
        battery = None

    if battery is None:
        res.add("key.state", "verdict.desktop")
        res.duration = time.time() - started
        res.finish(INFO, "verdict.desktop", summary_is_key=True)
        return res

    percent = getattr(battery, "percent", None)
    plugged = getattr(battery, "power_plugged", None)
    secsleft = getattr(battery, "secsleft", None)
    if secsleft in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN, -1, -2):
        secsleft = None

    res.add("key.state", f"{percent:.0f}%" if percent is not None else "-")
    res.add("key.power", "verdict.plugged" if plugged else "verdict.discharging")
    if secsleft:
        res.add("key.time_left", util.human_duration(secsleft))

    report = _battery_report()
    wear: Optional[float] = None
    if report.get("design_mwh") and report.get("full_mwh"):
        design = report["design_mwh"]
        full = report["full_mwh"]
        wear = 100.0 * (1.0 - full / design)
        res.add("key.design_capacity", f"{design / 1000:.1f} Wh")
        res.add("key.full_capacity", f"{full / 1000:.1f} Wh")
        res.add("key.wear", f"{wear:.1f}%")
    if report.get("cycles") is not None:
        res.add("key.cycles", f"{int(report['cycles'])}")

    status = PASS
    verdict = "verdict.normal"
    if wear is not None and wear >= 40:
        status, verdict = FAIL, "verdict.high"
    elif wear is not None and wear >= 25:
        status, verdict = WARN, "verdict.fair"
    if percent is not None and percent < 15 and not plugged:
        status = WARN if status == PASS else status
    res.score = round(wear, 1) if wear is not None else None
    res.unit = "% wear"
    res.duration = time.time() - started
    res.finish(status, verdict, summary_is_key=True)
    return res


# --------------------------------------------------------------------------- #
# disks
# --------------------------------------------------------------------------- #
def disk_health_result(progress=None, stop=None) -> Result:
    res = Result(id="disk_health", title_key="test.disk_health")
    started = time.time()
    drives = sysinfo.storage_info()
    if not drives:
        res.add("key.disk", "-")
        res.duration = time.time() - started
        res.finish(INFO, "verdict.no_sensor", summary_is_key=True)
        return res

    status = PASS
    for drive in drives[:6]:
        name = " ".join(p for p in (drive.get("model") or drive.get("device"), drive.get("media")) if p)
        total = drive.get("total") or drive.get("capacity") or 0
        free = drive.get("free")
        if drive.get("mount"):
            name = f"{drive['mount']}  {name}".strip()
        free_text = ""
        if drive.get("free") is not None and total:
            free_text = f"{util.human_bytes(drive['free'])} free of {util.human_bytes(total)}"
        elif total:
            free_text = util.human_bytes(total)
        res.add("key.disk", name or "-", note=free_text)
        free_pct = None
        if total and free is not None:
            free_pct = 100.0 * free / total
            res.add("key.disk_free", f"{free_pct:.0f}%",
                    status=PASS if free_pct >= 15 else (WARN if free_pct >= 5 else FAIL))
            if free_pct < 10:
                status = WARN
            if free_pct < 3:
                status = FAIL
        health = (drive.get("health") or "").strip()
        if health:
            row_status = PASS if health.lower() in ("healthy", "ok") else FAIL
            res.add("key.state", health, note="health", status=row_status)
            if row_status == FAIL:
                status = FAIL

    res.duration = time.time() - started
    res.finish(status, "verdict.ok", summary_is_key=True)
    return res
