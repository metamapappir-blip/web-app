"""PCScope - a small, dependency-light PC hardware diagnostics app.

Modules::

    util      cross-platform helpers and formatting
    i18n      English / Persian strings with Arabic-script shaping for Tkinter
    results   the Result / ResultSet model shared by every probe
    info      hardware inventory (CPU, board, RAM, disks, GPU, display)
    bench     active tests (CPU, memory, disk, network, speakers, stress)
    health    temperatures, fans, battery and disk health
    report    text / HTML / JSON writers
    runner    the catalogue that maps a test id to a probe
    gui       Tkinter desktop UI
    cli       headless runner (--cli)
"""

from __future__ import annotations

from .util import APP_NAME, APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION"]
__version__ = APP_VERSION
