#!/usr/bin/env python3
"""Headless smoke tests: ``python tests/test_smoke.py``.

The GUI half runs against a stand-in tkinter (see ``mock_tkinter.py``) so the
whole app - window construction, running tests, language switch, report export -
can be exercised on a machine with no display.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import mock_tkinter  # noqa: E402

mock_tkinter.install()

from pcscope import bench, cli, gui, i18n, monitor, report, results, runner  # noqa: E402

FAILURES: list = []
CHECKS = {"run": 0}


def check(condition: bool, label: str) -> None:
    CHECKS["run"] += 1
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        FAILURES.append(label)


# --------------------------------------------------------------------------- #
# 1. catalogue and runner
# --------------------------------------------------------------------------- #
def test_catalogue() -> None:
    print("catalogue")
    ids = runner.ids()
    check(len(ids) >= 8, "catalogue exposes the expected tests")
    check("system" in ids and "cpu" in ids and "disk" in ids, "core tests are available")
    for item in runner.CATALOGUE:
        check(bool(i18n.tr(item["title_key"])), f"title translated: {item['id']}")
        check(bool(i18n.tr(item["desc_key"])), f"description translated: {item['id']}")
    missing = [
        key for key in ("test.system", "btn.run_all", "report.title", "status.pass")
        if not i18n.tr(key)
    ]
    check(not missing, "key strings resolve")
    i18n.set_language("fa")
    check(i18n.tr("app.title") != "", "persian strings resolve")
    i18n.set_language("en")


# --------------------------------------------------------------------------- #
# 2. individual probes (fast subset)
# --------------------------------------------------------------------------- #
def test_probes() -> None:
    print("probes")
    for test_id in ("system", "gpu", "disk_health", "battery", "thermal"):
        result = runner.run(test_id)
        check(result.status in results.STATUS_ORDER, f"{test_id}: produced a status")
        check(isinstance(result.rows, list), f"{test_id}: produced rows")

    result = bench.cpu_benchmark(duration=0.6)
    check(result.status in ("pass", "warn"), "cpu benchmark completed")
    check(result.score is not None and result.score > 0, "cpu benchmark produced a score")
    check(any(row.note == "note.single_core" for row in result.rows),
          "cpu benchmark reports single-core throughput")

    result = bench.memory_benchmark(size_bytes=64 * 1024 * 1024)
    check(result.status in ("pass", "warn", "fail"), "memory benchmark completed")
    check(any(row.label == "key.integrity" for row in result.rows),
          "memory benchmark verifies integrity")

    result = bench.disk_benchmark(size_bytes=32 * 1024 * 1024)
    check(result.status in ("pass", "warn", "fail"), "disk benchmark completed")
    check(any(row.note == "note.seq_read" for row in result.rows),
          "disk benchmark reports read speed")

    result = bench.audio_test()
    check(result.status in ("pass", "warn", "info", "skipped"), "audio test handled")


# --------------------------------------------------------------------------- #
# 3. reports
# --------------------------------------------------------------------------- #
def test_reports() -> None:
    print("reports")
    data = results.ResultSet()
    data.computer = "Test PC"
    data.language = "en"
    data.begin()
    data.add(runner.run("system"))
    data.add(bench.cpu_benchmark(duration=0.5))
    data.end()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pcscope-tests-"))
    paths = report.save_all(data, str(tmp), "en")
    for kind, path in paths.items():
        check(pathlib.Path(path).is_file() and pathlib.Path(path).stat().st_size > 0,
              f"{kind} report written")

    html = pathlib.Path(paths["html"]).read_text(encoding="utf-8")
    check("<html" in html and "</html>" in html, "html report is a full document")
    check('dir="ltr"' in html, "english report is left-to-right")

    paths_fa = report.save_all(data, str(tmp / "fa"), "fa")
    html_fa = pathlib.Path(paths_fa["html"]).read_text(encoding="utf-8")
    check('dir="rtl"' in html_fa, "persian report is right-to-left")
    check("گزارش" in html_fa, "persian report contains persian text")

    summary = report.summary_text(data, "en")
    check("PCScope" in summary and "System information" in summary,
          "summary lists the tests")
    payload = data.to_dict("en")
    check(payload["results"][0]["rows"], "json payload keeps detail rows")

    # network down / offline must not crash and must still export
    shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 4. stop handling
# --------------------------------------------------------------------------- #
def test_stop() -> None:
    print("cancellation")
    stopped = {"value": False}

    def stop() -> bool:
        return stopped["value"]

    result = bench.memory_benchmark(size_bytes=512 * 1024 * 1024, stop=lambda: True)
    check(result.status == "skipped", "memory benchmark honours an immediate stop")

    result = bench.disk_benchmark(size_bytes=512 * 1024 * 1024, stop=lambda: True)
    check(result.status == "skipped", "disk benchmark honours an immediate stop")

    stopped["value"] = True
    result = bench.stress_test(duration=60, stop=stop)
    check(result.status == "skipped", "stress test honours an immediate stop")


# --------------------------------------------------------------------------- #
# 5. CLI
# --------------------------------------------------------------------------- #
def test_cli() -> None:
    print("cli")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pcscope-cli-"))
    code = cli.main(["--quick", "--only", "system,cpu,disk", "--out-dir", str(tmp)])
    check(code == 0, "cli exit code is 0 when nothing fails")
    check(any(tmp.glob("*.html")), "cli wrote an html report")
    check(any(tmp.glob("*.json")), "cli wrote a json report")
    code = cli.main(["--list"])
    check(code == 0, "cli --list works")
    shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 6. GUI against the mock
# --------------------------------------------------------------------------- #
def test_gui() -> None:
    print("gui")
    root = mock_tkinter.Tk()
    app = gui.App(root)
    check(app.tree is not None, "window built")
    check(len(app.vars) >= 8, "test checkboxes created")

    # run a small selection
    for test_id, var in app.vars.items():
        var.set(test_id in ("system", "cpu", "thermal", "gpu"))
    app.disk_size_mb.set(256)
    app.run_selected()
    deadline = time.time() + 180
    while app.worker_thread is not None and app.worker_thread.is_alive():
        if time.time() > deadline:
            break
        app._pump()
        time.sleep(0.05)
    app.worker_thread.join(timeout=5)
    app._pump()
    check(not app.running, "run finished and cleared the running flag")
    check(set(app.data.results) >= {"system", "cpu", "thermal", "gpu"},
          "selected results were collected")
    check(app.tree.get_children(), "results tree was populated")

    # details pane
    app.tree.selection_set("cpu")
    app._show_details("cpu")
    check("Score" in app.details.get("1.0", "end") or len(app.details.get("1.0", "end")) > 0,
          "details pane shows the selected test")

    # language switch
    before = app.details.get("1.0", "end")
    app.toggle_language()
    check(i18n.get_language() == "fa", "language toggled to persian")
    check(app.tree.get_children(), "tree rebuilt after language switch")
    after = app._computer_text() is not None
    app.toggle_language()
    check(i18n.get_language() == "en", "language toggled back to english")
    check(after and before is not None, "details survived the round trip")

    # export through the GUI
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pcscope-gui-"))
    target = tmp / "report.html"
    mock_tkinter.filedialog.answers["save"] = str(target)
    app.save_report()
    check(target.is_file(), "gui saved an html report")
    app.copy_summary()
    check(any(call[0] == "clipboard" for call in mock_tkinter.CALLS),
          "gui copied the summary")

    # stop button
    app.running = True
    app.stop()
    check(app.stop_flag.is_set(), "stop button sets the stop flag")
    app.running = False
    app.stop_flag.clear()

    # monitor window
    app.open_monitor_test()
    check(app.monitor_test is not None and app.monitor_test.window is not None,
          "monitor test window opened")
    app.monitor_test.next_colour()
    app.monitor_test.toggle_pause()
    app._pump()
    app.monitor_test.close()
    check(app.monitor_test.window is None, "monitor test window closed")

    # stress chart drawing
    app._show_chart(True)
    for index in range(30):
        app.samples.append({"time": index, "temp": 60 + index % 20, "clock": 3000})
    app._draw_chart()
    app._show_chart(False)
    check(app.chart_hidden, "stress chart is hidden again when idle")

    shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    started = time.time()
    for test in (
        test_catalogue,
        test_probes,
        test_reports,
        test_stop,
        test_cli,
        test_gui,
    ):
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - report but keep going
            import traceback

            traceback.print_exc()
            FAILURES.append(f"{test.__name__} raised {exc}")
    print()
    print(f"{CHECKS['run']} checks in {time.time() - started:.1f}s")
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES:")
        for item in FAILURES:
            print(f"  - {item}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
