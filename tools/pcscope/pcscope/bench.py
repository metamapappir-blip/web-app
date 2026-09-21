"""Active tests: CPU, memory, disk, network, speakers and stability stress.

Every public function takes the same optional hooks:

``progress(fraction, message_key)``
    called with 0.0 .. 1.0 so a UI can move a bar;
``stop()``
    polled between chunks - returning ``True`` aborts and marks the result
    ``skipped``.
"""

from __future__ import annotations

import math
import os
import random
import re
import socket
import ssl
import statistics
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Sequence

import psutil

from . import info as sysinfo
from . import util
from .results import FAIL, INFO, PASS, SKIPPED, WARN, Result, grade_thresholds

ProgressCb = Optional[Callable[[float, str], None]]
StopCb = Optional[Callable[[], bool]]

_MB = 1024 * 1024

# A mid-range desktop from roughly 2020 scores about this many ops/s per core in
# CPython 3.12. It only turns a raw score into a friendly word - never compare
# across machines with different Python versions.
_CPU_BASELINE = 4_500_000.0


def _tick(progress: ProgressCb, fraction: float, key: str = "") -> None:
    if progress:
        try:
            progress(max(0.0, min(1.0, fraction)), key)
        except Exception:
            pass


def _stopped(stop: StopCb) -> bool:
    if not stop:
        return False
    try:
        return bool(stop())
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# CPU
# --------------------------------------------------------------------------- #
def _burn(duration: float) -> int:
    """Integer-heavy workload; returns the number of operations completed."""
    ops = 0
    end = time.perf_counter() + duration
    block = 20_000
    while time.perf_counter() < end:
        total = 0
        n = 1_000_003
        for i in range(1, block):
            n = (n * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFF
            total += math.isqrt(n + i)
        ops += block
        if total == -1:  # never true: keeps the loop from being optimised away
            print(total)
    return ops


def cpu_benchmark(duration: float = 2.5, progress: ProgressCb = None, stop: StopCb = None) -> Result:
    res = Result(id="cpu", title_key="test.cpu")
    wall_start = time.time()
    workers = psutil.cpu_count(logical=True) or 1

    _tick(progress, 0.02, "status.running")
    single = 0.0
    try:
        start = time.perf_counter()
        single_ops = _burn(max(0.5, duration))
        single = single_ops / max(time.perf_counter() - start, 1e-6)
    except Exception as exc:
        res.error = str(exc)

    if _stopped(stop):
        res.duration = time.time() - wall_start
        res.finish(SKIPPED, "verdict.cancelled", summary_is_key=True)
        return res

    multi: Optional[float] = None
    scaling: Optional[float] = None
    try:
        start = time.perf_counter()
        total_ops = 0
        completed = 0
        with ProcessPoolExecutor(max_workers=workers) as pool:
            pending = [pool.submit(_burn, max(0.5, duration / 2.0)) for _ in range(workers)]
            while pending:
                for future in list(pending):
                    if future.done():
                        pending.remove(future)
                        completed += 1
                        try:
                            total_ops += int(future.result())
                        except Exception:
                            pass
                        _tick(progress, 0.45 + 0.5 * completed / max(workers, 1), "status.running")
                if pending and not _stopped(stop):
                    time.sleep(0.05)
                elif pending:
                    for future in pending:
                        future.cancel()
                    break
        if completed == workers and total_ops > 0:
            multi = total_ops / max(time.perf_counter() - start, 1e-6)
    except Exception as exc:  # noqa: BLE001 - locked-down machines block spawning
        res.error = f"multi-core: {exc}"
        multi = None

    if _stopped(stop):
        res.duration = time.time() - wall_start
        res.finish(SKIPPED, "verdict.cancelled", summary_is_key=True)
        return res

    _tick(progress, 1.0, "status.running")

    res.add("key.score", f"{single:,.0f} ops/s", note="note.single_core")
    res.score = round(single / _CPU_BASELINE * 100.0, 1)
    res.unit = "points"
    res.add("key.threads", str(workers))
    if multi and single > 0:
        scaling = multi / single
        res.add("key.score", f"{multi:,.0f} ops/s", note="note.multi_core")
        res.add("key.scaling", f"{scaling:.1f}x / {workers} ({100 * scaling / max(workers, 1):.0f}%)")

    status = PASS
    verdict = grade_thresholds(single, _CPU_BASELINE * 1.15, _CPU_BASELINE * 0.7, _CPU_BASELINE * 0.35)
    if verdict == "verdict.slow":
        status = WARN
    if scaling is not None and workers >= 4 and scaling < workers * 0.35:
        status = WARN
        res.add("note.low_scaling", f"{scaling:.1f}x of {workers}", status=WARN)
    if multi is None:
        status = WARN if status == PASS else status
        res.add("note.multicore_unavailable", res.error or "-", status=WARN)
    res.duration = time.time() - wall_start
    res.finish(status, verdict, summary_is_key=True)
    return res


# --------------------------------------------------------------------------- #
# memory
# --------------------------------------------------------------------------- #
def memory_benchmark(
    size_bytes: Optional[int] = None,
    progress: ProgressCb = None,
    stop: StopCb = None,
) -> Result:
    res = Result(id="memory", title_key="test.memory")
    wall_start = time.time()
    try:
        available = psutil.virtual_memory().available
    except Exception:
        available = 512 * _MB
    if not size_bytes:
        size_bytes = int(util.clamp(available * 0.25, 128 * _MB, 2 * 1024 * _MB))

    chunk = 32 * _MB
    chunks = max(1, size_bytes // chunk)
    size_bytes = chunks * chunk
    block = (b"PCScope" * (chunk // 7 + 1))[:chunk]

    try:
        buf = bytearray(size_bytes)

        # Touch every page once so the numbers reflect steady-state bandwidth
        # rather than first-touch page faults.
        for index in range(chunks):
            if _stopped(stop):
                raise KeyboardInterrupt
            offset = index * chunk
            buf[offset:offset + chunk] = block

        write_start = time.perf_counter()
        for index in range(chunks):
            if _stopped(stop):
                raise KeyboardInterrupt
            offset = index * chunk
            buf[offset:offset + chunk] = block
            _tick(progress, 0.45 * (index + 1) / chunks, "status.running")
        write_seconds = max(time.perf_counter() - write_start, 1e-6)

        read_start = time.perf_counter()
        for index in range(chunks):
            if _stopped(stop):
                raise KeyboardInterrupt
            offset = index * chunk
            buf.count(b"S", offset, offset + chunk)
            _tick(progress, 0.45 + 0.4 * (index + 1) / chunks, "status.running")
        read_seconds = max(time.perf_counter() - read_start, 1e-6)

        verify_start = time.perf_counter()
        valid = True
        for index in range(chunks):
            if _stopped(stop):
                raise KeyboardInterrupt
            offset = index * chunk
            if buf[offset:offset + chunk] != block:
                valid = False
                break
        verify_seconds = max(time.perf_counter() - verify_start, 1e-6)
        del buf
    except KeyboardInterrupt:
        res.duration = time.time() - wall_start
        res.finish(SKIPPED, "verdict.cancelled", summary_is_key=True)
        return res
    except MemoryError:
        res.duration = time.time() - wall_start
        res.finish(INFO, "verdict.no_sensor", summary_is_key=True)
        return res
    except Exception as exc:
        res.duration = time.time() - wall_start
        res.error = str(exc)
        res.finish(FAIL, str(exc))
        return res

    write_mbps = (size_bytes / _MB) / write_seconds
    read_mbps = (size_bytes / _MB) / read_seconds
    compare_mbps = (2 * size_bytes / _MB) / verify_seconds

    res.add("key.bandwidth", f"{write_mbps:,.0f} MB/s", note="note.write")
    res.add("key.bandwidth", f"{read_mbps:,.0f} MB/s", note="note.read")
    res.add("key.file_size", util.human_bytes(size_bytes))
    res.add("key.integrity", "verdict.passed" if valid else "verdict.failed",
            status=PASS if valid else FAIL)
    res.add("key.score", f"{compare_mbps:,.0f} MB/s", note="note.compare")
    res.score = round((write_mbps + read_mbps) / 2.0, 1)
    res.unit = "MB/s"

    status = FAIL if not valid else PASS
    if grade_thresholds(read_mbps, 5000, 2500, 1000) == "verdict.slow":
        status = WARN if status == PASS else status
    res.duration = time.time() - wall_start
    res.finish(status, "verdict.passed" if valid else "verdict.failed", summary_is_key=True)
    return res


# --------------------------------------------------------------------------- #
# disk
# --------------------------------------------------------------------------- #
def disk_benchmark(
    size_bytes: Optional[int] = None,
    path: Optional[str] = None,
    progress: ProgressCb = None,
    stop: StopCb = None,
) -> Result:
    res = Result(id="disk", title_key="test.disk")
    wall_start = time.time()
    if size_bytes is None:
        size_bytes = 1024 * _MB
    drive = sysinfo.system_drive()
    target_dir = path or tempfile.gettempdir()
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception:
        target_dir = tempfile.gettempdir()
    file_path = os.path.join(target_dir, f"pcscope_disk_test_{os.getpid()}.tmp")

    chunk = 8 * _MB
    chunks = max(1, int(size_bytes) // chunk)
    payload = os.urandom(1 * _MB) * (chunk // _MB)
    crcs: List[int] = [zlib.crc32(payload)]
    write_mbps = read_mbps = 0.0
    iops: Optional[float] = None

    write_flags = os.O_CREAT | os.O_TRUNC | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    read_flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    rw_flags = os.O_RDWR | getattr(os, "O_BINARY", 0)
    valid = True

    try:
        fd = os.open(file_path, write_flags, 0o600)
        start = time.perf_counter()
        try:
            for index in range(chunks):
                if _stopped(stop):
                    raise KeyboardInterrupt
                os.write(fd, payload)
                _tick(progress, 0.4 * (index + 1) / chunks, "status.running")
            os.fsync(fd)
        finally:
            os.close(fd)
        write_mbps = (chunks * chunk / _MB) / max(time.perf_counter() - start, 1e-6)

        fd = os.open(file_path, read_flags)
        start = time.perf_counter()
        try:
            for index in range(chunks):
                if _stopped(stop):
                    raise KeyboardInterrupt
                data = b""
                while len(data) < chunk:
                    more = os.read(fd, chunk - len(data))
                    if not more:
                        break
                    data += more
                if len(data) == chunk and zlib.crc32(data) != crcs[0]:
                    valid = False
                _tick(progress, 0.4 + 0.35 * (index + 1) / chunks, "status.running")
        finally:
            os.close(fd)
        read_mbps = (chunks * chunk / _MB) / max(time.perf_counter() - start, 1e-6)

        random_ops = min(1500, max(200, chunks * 8))
        block4k = os.urandom(4096)
        positions = [random.randrange(0, chunks) * chunk for _ in range(random_ops)]
        fd = os.open(file_path, rw_flags)
        start = time.perf_counter()
        try:
            for offset in positions:
                if _stopped(stop):
                    raise KeyboardInterrupt
                os.pwrite(fd, block4k, offset)
            os.fsync(fd)
            for offset in positions:
                if _stopped(stop):
                    raise KeyboardInterrupt
                os.pread(fd, 4096, offset)
        finally:
            os.close(fd)
        iops = (2 * len(positions)) / max(time.perf_counter() - start, 1e-6)
    except KeyboardInterrupt:
        _safe_remove(file_path)
        res.duration = time.time() - wall_start
        res.finish(SKIPPED, "verdict.cancelled", summary_is_key=True)
        return res
    except Exception as exc:
        error = str(exc)
        _safe_remove(file_path)
        res.duration = time.time() - wall_start
        res.error = error
        res.finish(FAIL, error)
        return res

    _safe_remove(file_path)
    _tick(progress, 1.0, "status.running")

    media = (drive.get("media") or "").lower()
    res.add("key.disk", " ".join(p for p in (drive.get("model") or drive.get("device"),
                                             drive.get("media")) if p) or "-")
    res.add("key.file_size", util.human_bytes(chunks * chunk))
    res.add("key.bandwidth", f"{write_mbps:.1f} MB/s", note="note.seq_write")
    res.add("key.bandwidth", f"{read_mbps:.1f} MB/s", note="note.seq_read")
    if iops:
        res.add("key.iops", f"{iops:.0f} IOPS", note="note.mixed_4k")
    res.add("key.integrity", "verdict.passed" if valid else "verdict.failed",
            status=PASS if valid else FAIL)
    res.score = round(read_mbps, 1)
    res.unit = "MB/s"

    status = FAIL if not valid else PASS
    if "hdd" in media or "spinning" in media:
        verdict = grade_thresholds(read_mbps, 140, 80, 40)
    else:
        verdict = grade_thresholds(read_mbps, 1200, 450, 180)
    if verdict == "verdict.slow":
        status = WARN if status == PASS else status
    res.duration = time.time() - wall_start
    res.finish(status, "verdict.passed" if valid else "verdict.failed", summary_is_key=True)
    return res


def _safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# network
# --------------------------------------------------------------------------- #
_LATENCY_TARGETS: Sequence[tuple] = (
    ("1.1.1.1", 443),
    ("8.8.8.8", 443),
    ("cloudflare.com", 443),
)
_DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=10000000"
_UPLOAD_URL = "https://speed.cloudflare.com/__up"


def _tcp_latency(host: str, port: int, timeout: float = 3.0) -> Optional[float]:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return (time.perf_counter() - start) * 1000.0
    except Exception:
        return None


def _ping(host: str = "1.1.1.1", count: int = 10) -> tuple:
    """Return (loss percent, average rtt ms) or (None, None)."""
    if util.IS_WINDOWS:
        code, out, _err = util.run(["ping", "-n", str(count), "-w", "2000", host], timeout=count * 3 + 8)
    else:
        code, out, _err = util.run(["ping", "-c", str(count), "-W", "2", host], timeout=count * 3 + 8)
    if code != 0 and not out:
        return None, None
    loss: Optional[float] = None
    match = re.search(r"\((\d+)% loss\)", out)
    if match:
        loss = float(match.group(1))
    else:
        match = re.search(r"(\d+(?:\.\d+)?)% packet loss", out)
        if match:
            loss = float(match.group(1))
        else:
            sent = re.search(r"Sent\s*=\s*(\d+)", out)
            lost = re.search(r"Lost\s*=\s*(\d+)", out)
            if sent and lost and float(sent.group(1)):
                loss = 100.0 * float(lost.group(1)) / float(sent.group(1))
    average: Optional[float] = None
    match = re.search(r"Average\s*=\s*(\d+)ms", out)
    if match:
        average = float(match.group(1))
    else:
        match = re.search(r"=\s*[\d.]+/([\d.]+)/[\d.]+", out)
        if match:
            average = float(match.group(1))
    return loss, average


def _transfer(url: str, data: Optional[bytes] = None, progress: ProgressCb = None,
              stop: StopCb = None, span: tuple = (0.0, 1.0)) -> Optional[float]:
    """Download (``data=None``) or upload, returning the speed in Mbps."""
    expected = len(data) if data else 10_000_000
    request = urllib.request.Request(url, data=data, headers={"User-Agent": "PCScope/1.0"})
    start = time.perf_counter()
    moved = 0
    try:
        context = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=45, context=context) as response:
            while True:
                if _stopped(stop):
                    break
                chunk = response.read(65536)
                if not chunk:
                    break
                moved += len(chunk)
                _tick(progress, span[0] + (span[1] - span[0]) * min(1.0, moved / expected), "status.running")
    except Exception:  # noqa: BLE001 - being offline is a normal outcome
        if moved <= 0:
            return None
    elapsed = max(time.perf_counter() - start, 1e-6)
    if moved <= 0:
        return None
    return moved * 8 / elapsed / 1_000_000.0


def network_test(progress: ProgressCb = None, stop: StopCb = None) -> Result:
    res = Result(id="network", title_key="test.network")
    wall_start = time.time()
    adapters = sysinfo.network_adapters()
    active = [a for a in adapters if a["up"] and (a["ipv4"] or a["ipv6"])]
    for adapter in (active or adapters)[:3]:
        value = " ".join(
            p for p in (
                adapter["name"],
                adapter["kind"],
                f"{adapter['speed_mbps']} Mbps" if adapter.get("speed_mbps") else "",
            ) if p
        )
        res.add("key.network", value)
        if adapter.get("ipv4"):
            res.add("key.ip", adapter["ipv4"])
        if adapter.get("ssid"):
            res.add("key.wifi", adapter["ssid"])
    if not active:
        res.duration = time.time() - wall_start
        res.finish(WARN, "verdict.offline", summary_is_key=True)
        return res

    _tick(progress, 0.08, "status.running")
    samples: List[float] = []
    for host, port in _LATENCY_TARGETS:
        if _stopped(stop):
            break
        value = _tcp_latency(host, port)
        if value is not None:
            samples.append(value)
    loss, ping_average = _ping()

    if samples:
        res.add("key.latency", f"{statistics.mean(samples):.1f} ms", note="note.tcp")
        res.add("key.latency", f"{min(samples):.1f} ms", note="note.best")
    if ping_average is not None:
        res.add("key.latency", f"{ping_average:.1f} ms", note="note.ping_avg")
    if loss is not None:
        icmp_only = bool(samples) and loss >= 50
        res.add("key.loss", f"{loss:.0f}%",
                status=INFO if icmp_only else (PASS if loss < 2 else (WARN if loss < 10 else FAIL)))
        if icmp_only:
            res.add("note.ping_blocked", f"{loss:.0f}%", status=INFO)

    online = bool(samples) or ping_average is not None
    if online:
        _tick(progress, 0.35, "status.running")
        download = _transfer(_DOWNLOAD_URL, progress=progress, stop=stop, span=(0.35, 0.75))
        if download is not None:
            res.add("key.download", f"{download:.1f} Mbps")
        _tick(progress, 0.8, "status.running")
        upload = _transfer(_UPLOAD_URL, data=os.urandom(_MB), progress=progress, stop=stop, span=(0.8, 1.0))
        if upload is not None:
            res.add("key.upload", f"{upload:.1f} Mbps")

    if _stopped(stop):
        res.duration = time.time() - wall_start
        res.finish(SKIPPED, "verdict.cancelled", summary_is_key=True)
        return res

    status = PASS
    verdict = "verdict.ok"
    if not online:
        status, verdict = WARN, "verdict.offline"
    else:
        mean_latency = statistics.mean(samples) if samples else (ping_average or 0)
        if loss is not None and loss >= 10 and not samples:
            status, verdict = FAIL, "verdict.slow"
        elif (loss is not None and loss >= 10 and samples) or mean_latency > 150:
            status, verdict = WARN, "verdict.fair"
        elif loss is not None and loss >= 2:
            status, verdict = WARN, "verdict.fair"
    res.duration = time.time() - wall_start
    res.finish(status, verdict, summary_is_key=True)
    return res


# --------------------------------------------------------------------------- #
# speakers
# --------------------------------------------------------------------------- #
def audio_test(progress: ProgressCb = None, stop: StopCb = None) -> Result:
    res = Result(id="audio", title_key="test.audio")
    wall_start = time.time()
    if not util.IS_WINDOWS:
        res.add("key.state", "-")
        res.duration = time.time() - wall_start
        res.finish(INFO, "status.unsupported", summary_is_key=True)
        return res
    try:
        import winsound

        for index, freq in enumerate((440, 880, 1320)):
            if _stopped(stop):
                break
            winsound.Beep(freq, 250)
            _tick(progress, (index + 1) / 3.0, "status.running")
            time.sleep(0.12)
        res.add("key.state", "verdict.ok")
        res.duration = time.time() - wall_start
        res.finish(PASS, "verdict.ok", summary_is_key=True)
    except Exception as exc:
        res.error = str(exc)
        res.add("key.state", str(exc))
        res.duration = time.time() - wall_start
        res.finish(WARN, str(exc))
    return res


# --------------------------------------------------------------------------- #
# stability stress
# --------------------------------------------------------------------------- #
def stress_test(
    duration: float = 300.0,
    progress: ProgressCb = None,
    stop: StopCb = None,
    on_sample: Optional[Callable[[Dict[str, Any]], None]] = None,
    sample_interval: float = 2.0,
) -> Result:
    """Load every core for ``duration`` seconds while sampling temperatures."""
    from . import health

    res = Result(id="stress", title_key="test.stress")
    wall_start = time.time()
    workers = psutil.cpu_count(logical=True) or 1

    try:
        freq = psutil.cpu_freq()
        max_clock = freq.max if freq and freq.max else None
    except Exception:
        max_clock = None
    if not max_clock:
        max_clock = sysinfo.cpu_details().get("max_mhz")

    temps: List[float] = []
    clocks: List[float] = []
    samples: List[Dict[str, Any]] = []
    deadline = wall_start + duration
    last_sample = 0.0
    used_processes = True

    def sample() -> None:
        reading = health.temperatures()
        temp = max(reading.values()) if reading else None
        if temp is not None:
            temps.append(temp)
        clock = None
        try:
            current = psutil.cpu_freq()
            if current:
                clock = current.current
                clocks.append(clock)
        except Exception:
            pass
        payload = {
            "time": time.time() - wall_start,
            "temp": temp,
            "clock": clock,
        }
        samples.append(payload)
        if on_sample:
            try:
                on_sample(payload)
            except Exception:
                pass

    try:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            pending = [pool.submit(_burn, 2.0) for _ in range(workers)]
            while time.time() < deadline and not _stopped(stop):
                for future in list(pending):
                    if future.done():
                        pending.remove(future)
                        try:
                            future.result()
                        except Exception:
                            pass
                        if not _stopped(stop) and time.time() < deadline:
                            pending.append(pool.submit(_burn, 2.0))
                now = time.time()
                if now - last_sample >= sample_interval:
                    last_sample = now
                    sample()
                _tick(progress, min(0.99, (now - wall_start) / max(duration, 1e-6)), "status.running")
                time.sleep(0.1)
            for future in pending:
                future.cancel()
    except Exception as exc:  # noqa: BLE001 - fall back to thread load
        res.error = f"process load unavailable: {exc}"
        used_processes = False
        stop_flag = threading.Event()

        def worker() -> None:
            while not stop_flag.is_set():
                _burn(0.5)

        threads = []
        try:
            for _ in range(workers):
                thread = threading.Thread(target=worker, daemon=True)
                thread.start()
                threads.append(thread)
            while time.time() < deadline and not _stopped(stop):
                now = time.time()
                if now - last_sample >= sample_interval:
                    last_sample = now
                    sample()
                _tick(progress, min(0.99, (now - wall_start) / max(duration, 1e-6)), "status.running")
                time.sleep(0.2)
        finally:
            stop_flag.set()
            for thread in threads:
                thread.join(timeout=2)

    cancelled = _stopped(stop)
    elapsed = time.time() - wall_start
    res.add("key.duration", util.human_duration(elapsed))
    res.add("key.threads", f"{workers}" + ("" if used_processes else " (threads)"))
    res.add("key.samples", str(len(samples)))
    if temps:
        res.add("key.temperature", f"{statistics.mean(temps):.1f} °C", note="note.avg")
        res.add("key.max", f"{max(temps):.1f} °C", note="note.temp")
        res.add("key.min", f"{min(temps):.1f} °C", note="note.temp")
    else:
        res.add("key.temperature", "verdict.no_sensor", status=INFO)
    if clocks and max_clock:
        mean_clock = statistics.mean(clocks)
        res.add("key.clocks", f"{mean_clock:.0f} / {max_clock:.0f} MHz ({100 * mean_clock / max_clock:.0f}%)")

    status = PASS
    verdict = "verdict.stable"
    if temps:
        if max(temps) >= 95:
            status, verdict = FAIL, "verdict.high"
        elif max(temps) >= 88:
            status, verdict = WARN, "verdict.high"
    if clocks and max_clock and statistics.mean(clocks) < max_clock * 0.75:
        status = WARN if status == PASS else status
        verdict = "verdict.throttled"
        res.add("note.throttle", f"{statistics.mean(clocks):.0f} / {max_clock:.0f} MHz", status=WARN)
    if cancelled:
        status, verdict = SKIPPED, "verdict.cancelled"
    res.score = round(statistics.mean(temps), 1) if temps else None
    res.unit = "°C"
    res.duration = elapsed
    res.finish(status, verdict, summary_is_key=True)
    return res
