"""Full-screen monitor test (dead / stuck pixel finder)."""

from __future__ import annotations

from typing import List, Optional, Tuple

COLOURS: List[Tuple[str, str]] = [
    ("#000000", "colour.black"),
    ("#ffffff", "colour.white"),
    ("#ff0000", "colour.red"),
    ("#00ff00", "colour.green"),
    ("#0000ff", "colour.blue"),
    ("#808080", "colour.gray"),
    ("#ff00ff", "colour.magenta"),
    ("#00ffff", "colour.cyan"),
    ("#ffff00", "colour.yellow"),
]


class MonitorTest:
    """Owns the full-screen window; the GUI only calls :meth:`open`."""

    def __init__(self, parent, on_close=None):
        self.parent = parent
        self.on_close = on_close
        self.window = None
        self.index = 0
        self.paused = False
        self._job: Optional[str] = None

    # -- public ----------------------------------------------------------- #
    def open(self) -> None:
        import tkinter as tk

        if self.window is not None:
            try:
                self.window.lift()
                return
            except Exception:
                self.window = None

        try:
            from . import i18n
        except Exception:  # pragma: no cover
            i18n = None  # type: ignore

        win = tk.Toplevel(self.parent)
        self.window = win
        win.configure(background="#000000")
        win.attributes("-fullscreen", True)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        win.title("Monitor test")

        self.canvas = tk.Canvas(win, highlightthickness=0, background="#000000")
        self.canvas.pack(fill="both", expand=True)
        self.label = self.canvas.create_text(
            0, 0, text="", fill="#ffffff", font=("Segoe UI", 20, "bold")
        )
        self.hint = self.canvas.create_text(0, 0, text="", fill="#ffffff", font=("Segoe UI", 14))

        win.bind("<Escape>", lambda _event: self.close())
        win.bind("<space>", lambda _event: self.toggle_pause())
        win.bind("n", lambda _event: self.next_colour())
        win.bind("N", lambda _event: self.next_colour())
        win.bind("<Right>", lambda _event: self.next_colour())
        win.bind("<Button-1>", lambda _event: self.next_colour())
        win.bind("<Configure>", lambda _event: self._layout())
        win.protocol("WM_DELETE_WINDOW", self.close)

        self._draw()
        self._schedule()

    def close(self) -> None:
        if self._job and self.window is not None:
            try:
                self.window.after_cancel(self._job)
            except Exception:
                pass
        self._job = None
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass

    def next_colour(self) -> None:
        self.index = (self.index + 1) % len(COLOURS)
        self._draw()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self._draw()

    # -- internals -------------------------------------------------------- #
    def _schedule(self) -> None:
        if self.window is None:
            return
        try:
            self._job = self.window.after(3000, self._auto_advance)
        except Exception:
            self._job = None

    def _auto_advance(self) -> None:
        if self.window is None:
            return
        if not self.paused:
            self.next_colour()
        self._schedule()

    def _label_text(self) -> str:
        try:
            from . import i18n

            return i18n.t(COLOURS[self.index][1])
        except Exception:  # pragma: no cover
            return COLOURS[self.index][1]

    def _help_text(self) -> str:
        try:
            from . import i18n

            return i18n.t("monitor.help")
        except Exception:  # pragma: no cover
            return "Esc to exit"

    def _draw(self) -> None:
        if self.window is None:
            return
        colour = COLOURS[self.index][0]
        try:
            self.canvas.configure(background=colour)
            self.window.configure(background=colour)
        except Exception:
            return
        # Pick a readable text colour for this background.
        brightness = int(colour[1:3], 16) + int(colour[3:5], 16) + int(colour[5:7], 16)
        text_colour = "#000000" if brightness > 380 else "#ffffff"
        self.canvas.itemconfigure(self.label, text=self._label_text(), fill=text_colour)
        self.canvas.itemconfigure(
            self.hint,
            text=f"{self._help_text()}" + ("\n[paused]" if self.paused else ""),
            fill=text_colour,
        )
        self._layout()

    def _layout(self) -> None:
        if self.window is None:
            return
        try:
            width = self.canvas.winfo_width() or self.window.winfo_screenwidth()
            height = self.canvas.winfo_height() or self.window.winfo_screenheight()
            self.canvas.coords(self.label, width / 2, height / 2 - 30)
            self.canvas.coords(self.hint, width / 2, height / 2 + 40)
        except Exception:
            pass
