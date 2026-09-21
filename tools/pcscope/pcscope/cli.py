"""Command line mode: ``PCScope.exe --cli --all`` (headless, CI friendly)."""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any, Dict, List, Optional

from . import i18n, report, runner, util
from .results import FAIL, ResultSet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pcscope",
        description="PCScope - hardware check and benchmark runner (headless mode)",
    )
    parser.add_argument("--all", action="store_true", help="run every non-interactive test")
    parser.add_argument("--only", default="", help="comma separated test ids to run")
    parser.add_argument("--skip", default="", help="comma separated test ids to skip")
    parser.add_argument("--quick", action="store_true", help="shorter runs (CI friendly)")
    parser.add_argument("--list", action="store_true", help="list available tests and exit")
    parser.add_argument("--lang", default="en", choices=list(i18n.LANGS), help="report language")
    parser.add_argument("--txt", default="", help="write a plain text report here")
    parser.add_argument("--html", default="", help="write an HTML report here")
    parser.add_argument("--json", default="", help="write a JSON report here")
    parser.add_argument("--out-dir", default="", help="write txt+html+json into this folder")
    parser.add_argument("--disk-mb", type=int, default=0, help="disk test file size in MB")
    parser.add_argument("--memory-mb", type=int, default=0, help="memory test block size in MB")
    parser.add_argument("--stress-minutes", type=float, default=0, help="stress test length")
    parser.add_argument("--quiet", action="store_true", help="only print the final summary")
    return parser


def pick_tests(args: argparse.Namespace) -> List[str]:
    available = runner.ids()
    if args.only:
        wanted = [item.strip() for item in args.only.split(",") if item.strip()]
        selected = [item for item in wanted if item in available]
    elif args.all:
        selected = list(available)
    else:
        selected = [item for item in runner.DEFAULT_IDS if item in available]
    skipped = [item.strip() for item in args.skip.split(",") if item.strip()]
    # Interactive tests need a screen and a user, so they are never headless.
    selected = [
        item for item in selected
        if item not in skipped and runner.BY_ID.get(item, {}).get("kind") != "interactive"
    ]
    if args.quick:
        selected = [item for item in selected if item != "stress"]
    return selected


def options_for(args: argparse.Namespace) -> Dict[str, Any]:
    options: Dict[str, Any] = {
        "cpu_duration": 1.0 if args.quick else 2.5,
        "memory_size": (args.memory_mb or 0) * 1024 * 1024 or None,
        "disk_size": (args.disk_mb or (256 if args.quick else 1024)) * 1024 * 1024,
        "stress_duration": (args.stress_minutes or 1.0) * 60.0,
    }
    return options


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    i18n.set_language(args.lang)

    if args.list:
        for item in runner.CATALOGUE:
            if not runner.available(item):
                continue
            print(f"{item['id']:14s} {i18n.tr(item['desc_key'])}")
        return 0

    selected = pick_tests(args)
    if not selected:
        print("nothing to run", file=sys.stderr)
        return 2

    data = ResultSet()
    data.language = args.lang
    data.begin()
    options = options_for(args)
    last_print = 0.0

    for index, test_id in enumerate(selected, start=1):
        item = runner.BY_ID.get(test_id, {})
        title = i18n.tr(item.get("title_key", test_id))
        if not args.quiet:
            print(f"[{index}/{len(selected)}] {title} ...", flush=True)

        def progress(fraction: float, key: str = "") -> None:
            nonlocal last_print
            now = time.time()
            if args.quiet or now - last_print < 0.4:
                return
            last_print = now
            bar = "#" * int(28 * max(0.0, min(1.0, fraction)))
            print(f"\r    {bar:<28} {int(fraction * 100):3d}%", end="", flush=True)

        started = time.time()
        try:
            result = runner.run(test_id, progress=progress, options=options)
        except Exception as exc:  # noqa: BLE001 - keep going, report the failure
            from .results import Result

            result = Result(id=test_id, title_key=item.get("title_key", test_id))
            result.error = str(exc)
            result.finish(FAIL, str(exc))
        result.duration = time.time() - started
        data.add(result)
        if not args.quiet:
            verdict = i18n.tr(result.summary) if result.summary_is_key else result.summary
            print(f"\r    {i18n.status_word_raw(result.status)}: {verdict} "
                  f"({util.human_duration(result.duration)})        ", flush=True)
        if test_id == "system":
            data.computer = next(
                (str(row.value) for row in result.rows if row.label == "key.machine"), ""
            )

    data.end()
    written: Dict[str, str] = {}
    if args.out_dir:
        written = report.save_all(data, args.out_dir, args.lang)
    if args.txt:
        written["txt"] = report.write_text(data, args.txt, args.lang)
    if args.html:
        written["html"] = report.write_html(data, args.html, args.lang)
    if args.json:
        written["json"] = report.write_json(data, args.json, args.lang)

    print()
    print(report.summary_text(data, args.lang))
    for kind, path in written.items():
        print(f"{kind}: {path}")

    counts = data.counts()
    return 1 if counts.get(FAIL) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
