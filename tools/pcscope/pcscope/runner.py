"""The test catalogue: what can run, and how to run it."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from . import bench, health, info, util
from .results import Result

ProgressCb = Optional[Callable[[float, str], None]]
StopCb = Optional[Callable[[], bool]]


CATALOGUE: List[Dict[str, Any]] = [
    {
        "id": "system",
        "title_key": "test.system",
        "desc_key": "test.system.desc",
        "kind": "info",
        "default": True,
        "estimated": 3,
    },
    {
        "id": "cpu",
        "title_key": "test.cpu",
        "desc_key": "test.cpu.desc",
        "kind": "bench",
        "default": True,
        "estimated": 12,
    },
    {
        "id": "memory",
        "title_key": "test.memory",
        "desc_key": "test.memory.desc",
        "kind": "bench",
        "default": True,
        "estimated": 20,
        "long": True,
    },
    {
        "id": "disk",
        "title_key": "test.disk",
        "desc_key": "test.disk.desc",
        "kind": "bench",
        "default": True,
        "estimated": 60,
        "long": True,
    },
    {
        "id": "disk_health",
        "title_key": "test.disk_health",
        "desc_key": "test.disk_health.desc",
        "kind": "info",
        "default": True,
        "estimated": 5,
    },
    {
        "id": "gpu",
        "title_key": "test.gpu",
        "desc_key": "test.gpu.desc",
        "kind": "info",
        "default": True,
        "estimated": 4,
    },
    {
        "id": "network",
        "title_key": "test.network",
        "desc_key": "test.network.desc",
        "kind": "bench",
        "default": True,
        "estimated": 35,
    },
    {
        "id": "battery",
        "title_key": "test.battery",
        "desc_key": "test.battery.desc",
        "kind": "info",
        "default": True,
        "estimated": 10,
    },
    {
        "id": "thermal",
        "title_key": "test.thermal",
        "desc_key": "test.thermal.desc",
        "kind": "info",
        "default": True,
        "estimated": 8,
    },
    {
        "id": "audio",
        "title_key": "test.audio",
        "desc_key": "test.audio.desc",
        "kind": "interactive",
        "default": False,
        "estimated": 3,
        "windows_only": True,
    },
    {
        "id": "stress",
        "title_key": "test.stress",
        "desc_key": "test.stress.desc",
        "kind": "long",
        "default": False,
        "estimated": 300,
        "long": True,
    },
    {
        "id": "monitor",
        "title_key": "test.monitor",
        "desc_key": "test.monitor.desc",
        "kind": "interactive",
        "default": False,
        "estimated": 0,
    },
]

BY_ID: Dict[str, Dict[str, Any]] = {item["id"]: item for item in CATALOGUE}
DEFAULT_IDS = [item["id"] for item in CATALOGUE if item.get("default")]


def available(item: Dict[str, Any]) -> bool:
    if item.get("windows_only") and not util.IS_WINDOWS:
        return False
    return True


def ids() -> List[str]:
    return [item["id"] for item in CATALOGUE if available(item)]


def estimated_seconds(selected: List[str]) -> int:
    return sum(int(BY_ID.get(test_id, {}).get("estimated", 0)) for test_id in selected)


def run(
    test_id: str,
    progress: ProgressCb = None,
    stop: StopCb = None,
    on_sample: Optional[Callable[[Dict[str, Any]], None]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Result:
    """Run one test by id and return its :class:`Result`."""
    options = options or {}

    if test_id == "system":
        return info.collect_system_result()
    if test_id == "cpu":
        return bench.cpu_benchmark(duration=float(options.get("cpu_duration", 2.5)),
                                   progress=progress, stop=stop)
    if test_id == "memory":
        return bench.memory_benchmark(size_bytes=options.get("memory_size"),
                                      progress=progress, stop=stop)
    if test_id == "disk":
        return bench.disk_benchmark(size_bytes=options.get("disk_size"),
                                    path=options.get("disk_path"),
                                    progress=progress, stop=stop)
    if test_id == "disk_health":
        return health.disk_health_result(progress=progress, stop=stop)
    if test_id == "gpu":
        return info.collect_gpu_result()
    if test_id == "network":
        return bench.network_test(progress=progress, stop=stop)
    if test_id == "battery":
        return health.battery_result(progress=progress, stop=stop)
    if test_id == "thermal":
        return health.thermal_result(progress=progress, stop=stop)
    if test_id == "audio":
        return bench.audio_test(progress=progress, stop=stop)
    if test_id == "stress":
        return bench.stress_test(duration=float(options.get("stress_duration", 300.0)),
                                 progress=progress, stop=stop, on_sample=on_sample)
    if test_id == "monitor":
        from .results import INFO

        result = Result(id="monitor", title_key="test.monitor")
        result.add("key.state", "monitor.open_hint")
        result.finish(INFO, "status.running", summary_is_key=True)
        return result

    from .results import SKIPPED

    result = Result(id=test_id, title_key=test_id)
    result.finish(SKIPPED, "status.skipped", summary_is_key=True)
    return result
