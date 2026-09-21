#!/usr/bin/env python3
"""PCScope entry point.

Run without arguments to open the desktop window, or with ``--cli`` to run the
tests headlessly and write a report. This is also the target PyInstaller builds
into a single Windows executable.
"""

from __future__ import annotations

import multiprocessing
import sys
from typing import List, Optional


def _take_value(argv: List[str], flag: str) -> Optional[str]:
    if flag in argv:
        index = argv.index(flag)
        if index + 1 < len(argv):
            value = argv[index + 1]
            del argv[index:index + 2]
            return value
        del argv[index]
    return None


def main(argv: Optional[List[str]] = None) -> int:
    # Required for frozen (PyInstaller) builds that spawn worker processes.
    multiprocessing.freeze_support()

    args: List[str] = list(sys.argv[1:] if argv is None else argv)
    lang = _take_value(args, "--lang") or "en"
    cli_mode = "--cli" in args
    if cli_mode:
        args.remove("--cli")

    if "--version" in args:
        from pcscope.util import APP_VERSION

        print(f"PCScope {APP_VERSION}")
        return 0

    if cli_mode:
        from pcscope.cli import main as cli_main

        if "--lang" not in args:
            args += ["--lang", lang]
        return cli_main(args)

    from pcscope.gui import launch

    launch(lang)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
