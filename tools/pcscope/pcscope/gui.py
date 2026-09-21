"""PCScope desktop UI (Tkinter, no extra widget dependencies).

The UI only renders: every measurement runs in a worker thread and reports back
through a queue, so the window never freezes during a long disk or stress run.
"""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, List, Optional

from . import i18n, monitor, report, runner, util
from .results import FAIL, INFO, PASS, PENDING, RUNNING, SKIPPED, WARN, Result, ResultSet

BG = "#0f1420"
PANEL = "#161d2b"
PANEL2 = "#1d2637"
FG = "#e6edf7"
MUTED = "#93a3ba"
ACCENT = "#38bdf8"

STATUS_COLORS = {
    PASS: "#22c55e",
    WARN: "#f59e0b",
    FAIL: "#ef4444",
    INFO: "#38bdf8",
    SKIPPED: "#94a3b8",
    PENDING: "#64748b",
    RUNNING: "#a78bfa",
}

DISK_SIZES = [("256 MB", 256), ("512 MB", 512), ("1 GB", 1024), ("2 GB", 2048)]
STRESS_MINUTES = [("5 min", 5), ("10 min", 10), ("30 min", 30)]


def shape(text: str) -> str:
    """Shortcut for i18n shaping (Tkinter cannot draw Persian on its own)."""
    return i18n.shape(text)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.data = ResultSet()
        self.queue: "queue.Queue[tuple]" = queue.Queue()
        self.vars: Dict[str, tk.BooleanVar] = {}
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        self.running = False
        self.monitor_test: Optional[monitor.MonitorTest] = None
        self.samples: List[Dict[str, Any]] = []
        self.disk_size_mb = tk.IntVar(value=1024)
        self.stress_minutes = tk.IntVar(value=10)
        self.status_var = tk.StringVar(value="")
        self.summary_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.current_test = ""
        self._build_style()
        self._build_ui()
        self._apply_language()
        self._pump()
        self._load_system_info_async()

    # ------------------------------------------------------------------ #
    # construction
    # ------------------------------------------------------------------ #
    def _build_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=BG, foreground=FG, fieldbackground=PANEL,
                        bordercolor=PANEL2, troughcolor=PANEL2)
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL, relief="flat")
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("Card.TLabel", background=PANEL, foreground=FG)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("TCheckbutton", background=PANEL, foreground=FG,
                        indicatorcolor=PANEL2)
        style.map("TCheckbutton", background=[("active", PANEL)],
                  foreground=[("active", FG)])
        style.configure("Header.TLabel", background=BG, foreground=FG,
                        font=("Segoe UI", 17, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED,
                        font=("Segoe UI", 10))
        style.configure("Section.TLabelframe", background=PANEL, foreground=FG)
        style.configure("Section.TLabelframe.Label", background=PANEL, foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", background=ACCENT, foreground="#06263a",
                        borderwidth=0, focusthickness=0, padding=(14, 7),
                        font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#7dd3fc"), ("disabled", "#334155")],
                  foreground=[("disabled", "#94a3b8")])
        style.configure("TButton", background=PANEL2, foreground=FG, borderwidth=0,
                        focusthickness=0, padding=(12, 6), font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#2b3648")],
                  foreground=[("active", FG)])
        style.configure("TProgressbar", background=ACCENT, troughcolor=PANEL2,
                        borderwidth=0, thickness=8)
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=FG, borderwidth=0, rowheight=26)
        style.configure("Treeview.Heading", background=PANEL2, foreground=MUTED,
                        borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#233246")],
                  foreground=[("selected", FG)])
        style.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2,
                        foreground=FG, arrowcolor=FG)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL2)])

    def _build_ui(self) -> None:
        root = self.root
        root.configure(background=BG)
        root.title("PCScope")
        root.geometry("1080x720")
        root.minsize(900, 620)

        # ---- header ---------------------------------------------------- #
        header = ttk.Frame(root, padding=(18, 14, 18, 8))
        header.pack(fill="x")
        self.title_label = ttk.Label(header, style="Header.TLabel")
        self.title_label.pack(anchor="w")
        self.subtitle_label = ttk.Label(header, style="Sub.TLabel")
        self.subtitle_label.pack(anchor="w")

        header_buttons = ttk.Frame(header)
        header_buttons.pack(anchor="ne", side="right", padx=4)
        self.lang_button = ttk.Button(header_buttons, command=self.toggle_language)
        self.lang_button.pack(side="right", padx=(8, 0))
        self.about_button = ttk.Button(header_buttons, command=self.show_about)
        self.about_button.pack(side="right")

        self.summary_label = ttk.Label(root, style="Muted.TLabel", padding=(18, 0))
        self.summary_label.pack(fill="x")

        # ---- body ------------------------------------------------------ #
        body = ttk.Frame(root, padding=(18, 10, 18, 6))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # left: test picker
        left = ttk.Frame(body, width=330)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        left.grid_propagate(False)
        self.tests_frame = ttk.LabelFrame(left, style="Section.TLabelframe", padding=10)
        self.tests_frame.pack(fill="both", expand=True)

        selector = ttk.Frame(left)
        selector.pack(fill="x", pady=(8, 0))
        self.select_all_button = ttk.Button(selector, command=lambda: self._set_all(True))
        self.select_all_button.pack(side="left")
        self.select_none_button = ttk.Button(selector, command=lambda: self._set_all(False))
        self.select_none_button.pack(side="left", padx=(6, 0))

        options = ttk.LabelFrame(left, style="Section.TLabelframe", padding=10)
        options.pack(fill="x", pady=(10, 0))
        self.disk_size_label = ttk.Label(options, style="Card.TLabel")
        self.disk_size_label.grid(row=0, column=0, sticky="w")
        self.disk_size_combo = ttk.Combobox(
            options, state="readonly", width=12,
            values=[label for label, _ in DISK_SIZES],
        )
        self.disk_size_combo.current(2)
        self.disk_size_combo.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.disk_size_combo.bind("<<ComboboxSelected>>", self._on_disk_size)
        self.stress_label = ttk.Label(options, style="Card.TLabel")
        self.stress_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.stress_combo = ttk.Combobox(
            options, state="readonly", width=12,
            values=[label for label, _ in STRESS_MINUTES],
        )
        self.stress_combo.current(1)
        self.stress_combo.grid(row=1, column=1, sticky="e", padx=(8, 0), pady=(8, 0))
        self.stress_combo.bind("<<ComboboxSelected>>", self._on_stress_minutes)
        options.columnconfigure(0, weight=1)

        # right: results
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        right.columnconfigure(0, weight=1)

        self.results_frame = ttk.LabelFrame(right, style="Section.TLabelframe", padding=8)
        self.results_frame.grid(row=0, column=0, sticky="nsew")
        self.tree = ttk.Treeview(
            self.results_frame,
            columns=("result", "status"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="", anchor="w")
        self.tree.heading("result", text="", anchor="w")
        self.tree.heading("status", text="", anchor="w")
        self.tree.column("#0", width=200, stretch=True)
        self.tree.column("result", width=250, stretch=True)
        self.tree.column("status", width=110, stretch=False, anchor="center")
        scroll = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.tag_configure("pass", foreground=STATUS_COLORS[PASS])
        self.tree.tag_configure("warn", foreground=STATUS_COLORS[WARN])
        self.tree.tag_configure("fail", foreground=STATUS_COLORS[FAIL])
        self.tree.tag_configure("info", foreground=STATUS_COLORS[INFO])
        self.tree.tag_configure("skipped", foreground=STATUS_COLORS[SKIPPED])
        self.tree.tag_configure("pending", foreground=STATUS_COLORS[PENDING])
        self.tree.tag_configure("running", foreground=STATUS_COLORS[RUNNING])
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_details())

        self.details_frame = ttk.LabelFrame(right, style="Section.TLabelframe", padding=8)
        self.details_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.details_frame.rowconfigure(0, weight=1)
        self.details_frame.columnconfigure(0, weight=1)
        self.details = tk.Text(
            self.details_frame,
            height=8,
            wrap="word",
            background=PANEL,
            foreground=FG,
            insertbackground=FG,
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            state="disabled",
        )
        details_scroll = ttk.Scrollbar(self.details_frame, orient="vertical",
                                       command=self.details.yview)
        self.details.configure(yscrollcommand=details_scroll.set)
        self.details.grid(row=0, column=0, sticky="nsew")
        details_scroll.grid(row=0, column=1, sticky="ns")
        self.details.tag_configure("rtl", justify="right")
        self.details.tag_configure("muted", foreground=MUTED)
        self.details.tag_configure("head", foreground=ACCENT)

        self.chart = tk.Canvas(self.details_frame, height=120, background=PANEL,
                               highlightthickness=0)
        self.chart_hidden = True

        # ---- footer ---------------------------------------------------- #
        footer = ttk.Frame(root, padding=(18, 4, 18, 14))
        footer.pack(fill="x")
        self.progress = ttk.Progressbar(footer, mode="determinate",
                                        variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x")
        status_row = ttk.Frame(footer)
        status_row.pack(fill="x", pady=(8, 0))
        self.status_label = ttk.Label(status_row, textvariable=self.status_var,
                                      style="Muted.TLabel")
        self.status_label.pack(side="left")
        self.stop_button = ttk.Button(status_row, command=self.stop)
        self.stop_button.pack(side="left", padx=(10, 0))
        self.buttons_frame = ttk.Frame(status_row)
        self.buttons_frame.pack(side="right")
        self.run_button = ttk.Button(self.buttons_frame, style="Accent.TButton",
                                     command=self.run_selected)
        self.run_button.pack(side="right")
        self.monitor_button = ttk.Button(self.buttons_frame,
                                         command=self.open_monitor_test)
        self.monitor_button.pack(side="right", padx=(0, 8))
        self.save_button = ttk.Button(self.buttons_frame, command=self.save_report)
        self.save_button.pack(side="right", padx=(0, 8))
        self.copy_button = ttk.Button(self.buttons_frame, command=self.copy_summary)
        self.copy_button.pack(side="right", padx=(0, 8))

    # ------------------------------------------------------------------ #
    # language
    # ------------------------------------------------------------------ #
    def _apply_language(self) -> None:
        lang = i18n.get_language()
        rtl = i18n.is_rtl()
        anchor = "e" if rtl else "w"
        self.root.title(i18n.tr("app.title"))
        self.title_label.configure(text=shape(i18n.tr("app.title")), anchor=anchor)
        self.subtitle_label.configure(text=shape(i18n.tr("app.subtitle")), anchor=anchor)
        self.summary_label.configure(anchor=anchor)
        self.test_heading_text = i18n.tr("hdr.tests")
        self.tests_frame.configure(text=shape(self.test_heading_text))
        self.results_frame.configure(text=shape(i18n.tr("hdr.results")))
        self.details_frame.configure(text=shape(i18n.tr("hdr.details")))
        self.tree.heading("#0", text=shape(i18n.tr("col.test")), anchor=anchor)
        self.tree.heading("result", text=shape(i18n.tr("col.result")), anchor=anchor)
        self.tree.heading("status", text=shape(i18n.tr("col.status")), anchor="center")
        self.run_button.configure(text=shape(i18n.tr("btn.run_selected")))
        self.stop_button.configure(text=shape(i18n.tr("btn.stop")))
        self.monitor_button.configure(text=shape(i18n.tr("btn.monitor")))
        self.save_button.configure(text=shape(i18n.tr("btn.save_html")))
        self.copy_button.configure(text=shape(i18n.tr("btn.copy")))
        self.about_button.configure(text=shape(i18n.tr("app.about")))
        self.lang_button.configure(text=shape("English" if lang == "fa" else "فارسی"))
        self.select_all_button.configure(text=shape(i18n.tr("label.select_all")))
        self.select_none_button.configure(text=shape(i18n.tr("label.select_none")))
        self.disk_size_label.configure(text=shape(i18n.tr("key.file_size")))
        self.stress_label.configure(text=shape(i18n.tr("key.duration")))
        if not self.running:
            self.status_var.set(shape(i18n.tr("msg.ready")))
        self._rebuild_test_list()
        self._refresh_tree()
        self._show_details()
        self._update_summary_label()

    def toggle_language(self) -> None:
        i18n.toggle_language()
        self.data.language = i18n.get_language()
        self._apply_language()
        if self.monitor_test is not None and self.monitor_test.window is not None:
            self.monitor_test._draw()

    # ------------------------------------------------------------------ #
    # test list
    # ------------------------------------------------------------------ #
    def _rebuild_test_list(self) -> None:
        for child in self.tests_frame.winfo_children():
            child.destroy()
        self.vars.clear()
        rtl = i18n.is_rtl()
        anchor = "e" if rtl else "w"
        for item in runner.CATALOGUE:
            if not runner.available(item):
                continue
            test_id = item["id"]
            if test_id not in self.vars:
                self.vars[test_id] = tk.BooleanVar(value=bool(item.get("default")))
            row = ttk.Frame(self.tests_frame, style="Card.TFrame")
            row.pack(fill="x", pady=(0, 6))
            check = ttk.Checkbutton(
                row,
                variable=self.vars[test_id],
                text=shape(i18n.tr(item["title_key"])),
                style="TCheckbutton",
            )
            check.pack(anchor=anchor, fill="x")
            desc = ttk.Label(
                row,
                text=shape(i18n.tr(item["desc_key"])),
                style="Card.TLabel",
                foreground=MUTED,
                wraplength=280,
                justify="right" if rtl else "left",
                font=("Segoe UI", 9),
            )
            desc.pack(anchor=anchor, fill="x", padx=(24, 4) if not rtl else (4, 24))
        self._update_estimate()

    def _set_all(self, value: bool) -> None:
        for var in self.vars.values():
            var.set(value)
        self._update_estimate()

    def _update_estimate(self) -> None:
        selected = [test_id for test_id, var in self.vars.items() if var.get()]
        seconds = runner.estimated_seconds(selected)
        if seconds:
            self.status_var.set(
                f"{shape(i18n.tr('label.progress'))}: ~{util.human_duration(seconds)}"
            )
        elif not self.running:
            self.status_var.set(shape(i18n.tr("msg.ready")))

    def _on_disk_size(self, _event=None) -> None:
        index = self.disk_size_combo.current()
        if 0 <= index < len(DISK_SIZES):
            self.disk_size_mb.set(DISK_SIZES[index][1])

    def _on_stress_minutes(self, _event=None) -> None:
        index = self.stress_combo.current()
        if 0 <= index < len(STRESS_MINUTES):
            self.stress_minutes.set(STRESS_MINUTES[index][1])

    # ------------------------------------------------------------------ #
    # running
    # ------------------------------------------------------------------ #
    def _options(self) -> Dict[str, Any]:
        return {
            "disk_size": self.disk_size_mb.get() * 1024 * 1024,
            "stress_duration": self.stress_minutes.get() * 60.0,
            "memory_size": None,
            "cpu_duration": 2.5,
        }

    def run_selected(self) -> None:
        if self.running:
            return
        selected = [test_id for test_id, var in self.vars.items() if var.get()]
        if not selected:
            messagebox.showinfo("PCScope", i18n.tr("msg.no_tests"))
            return
        for test_id in selected:
            self.data.results.pop(test_id, None)
            if test_id in self.data.order:
                self.data.order.remove(test_id)
        self.stop_flag.clear()
        self.running = True
        self.progress_var.set(0.0)
        self._refresh_tree()
        self.worker_thread = threading.Thread(
            target=self._worker, args=(selected,), daemon=True
        )
        self.worker_thread.start()

    def stop(self) -> None:
        if not self.running:
            return
        self.stop_flag.set()
        self.status_var.set(shape(i18n.tr("msg.stopped")))

    def _worker(self, selected: List[str]) -> None:
        self.data.begin()
        total = len(selected)
        for index, test_id in enumerate(selected):
            if self.stop_flag.is_set():
                break
            self.queue.put(("start", {"id": test_id, "index": index, "total": total}))

            def progress(fraction: float, key: str = "") -> None:
                base = index / max(total, 1)
                span = 1.0 / max(total, 1)
                self.queue.put(("progress", {"value": (base + span * fraction) * 100.0,
                                             "index": index, "total": total}))

            def stop() -> bool:
                return self.stop_flag.is_set()

            def on_sample(sample: Dict[str, Any]) -> None:
                self.queue.put(("sample", sample))

            try:
                result = runner.run(test_id, progress=progress, stop=stop,
                                    on_sample=on_sample, options=self._options())
            except Exception as exc:  # noqa: BLE001 - never let a probe kill the run
                item = runner.BY_ID.get(test_id, {})
                result = Result(id=test_id, title_key=item.get("title_key", test_id))
                result.error = str(exc)
                result.finish(FAIL, str(exc))
            self.data.add(result)
            self.queue.put(("result", result))
        self.data.end()
        self.queue.put(("done", None))

    # ------------------------------------------------------------------ #
    # queue pump (main thread)
    # ------------------------------------------------------------------ #
    def _pump(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                self._handle(kind, payload)
        except queue.Empty:
            pass
        self.root.after(120, self._pump)

    def _handle(self, kind: str, payload: Any) -> None:
        if kind == "start":
            self.current_test = payload["id"]
            item = runner.BY_ID.get(self.current_test, {})
            name = i18n.tr(item.get("title_key", self.current_test))
            self.status_var.set(
                shape(i18n.tr("msg.running", name=name))
                + f"  ({payload['index'] + 1}/{payload['total']})"
            )
            if self.current_test == "stress":
                self.samples = []
                self._show_chart(True)
            self._refresh_tree()
        elif kind == "progress":
            self.progress_var.set(max(0.0, min(100.0, payload["value"])))
        elif kind == "result":
            self._refresh_tree()
            self._show_details(payload.id)
        elif kind == "sample":
            self.samples.append(payload)
            self._draw_chart()
        elif kind == "done":
            self.running = False
            self.progress_var.set(100.0)
            self._show_chart(False)
            duration = self.data.duration() or 0
            self.status_var.set(shape(i18n.tr("msg.done", secs=util.human_duration(duration))))
            self._refresh_tree()

    # ------------------------------------------------------------------ #
    # results rendering
    # ------------------------------------------------------------------ #
    def _refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for item in runner.CATALOGUE:
            test_id = item["id"]
            if not runner.available(item):
                continue
            result = self.data.get(test_id)
            status = result.status if result else PENDING
            summary = ""
            if result:
                summary = i18n.tr(result.summary) if result.summary_is_key else result.summary
            if self.running and self.current_test == test_id and status != PENDING:
                pass
            self.tree.insert(
                "",
                "end",
                iid=test_id,
                text=shape(i18n.tr(item["title_key"])),
                values=(shape(summary), shape(i18n.status_word(status))),
                tags=(status,),
            )
        self._update_summary_label()

    def _update_summary_label(self) -> None:
        counts = self.data.counts()
        if not counts:
            self.summary_var.set("")
            self.summary_label.configure(text=self._computer_text())
            return
        parts = [f"{i18n.status_word(status)}: {count}" for status, count in counts.items()]
        computer = self._computer_text()
        text = "  •  ".join(parts)
        self.summary_label.configure(text=shape(f"{computer}   {text}" if computer else text))

    def _computer_text(self) -> str:
        return self.data.computer or ""

    def _show_details(self, test_id: Optional[str] = None) -> None:
        if test_id is None:
            selection = self.tree.selection()
            test_id = selection[0] if selection else None
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        rtl = i18n.is_rtl()
        result = self.data.get(test_id) if test_id else None
        if result is None:
            self.details.insert("end", shape(i18n.tr("msg.no_results")) + "\n", ("muted", "rtl") if rtl else ("muted",))
        else:
            item = runner.BY_ID.get(result.id, {})
            title = i18n.tr(item.get("title_key", result.id))
            self.details.insert("end", shape(f"{title}\n"), ("head", "rtl") if rtl else ("head",))
            verdict = i18n.tr(result.summary) if result.summary_is_key else result.summary
            if verdict:
                self.details.insert("end", shape(f"{i18n.tr('col.result')}: {verdict}\n\n"))
            for row in result.rows:
                label = i18n.key_raw(row.label) if row.label in i18n._STRINGS else row.label
                value = i18n.tr(row.value) if row.value in i18n._STRINGS else row.value
                note = ""
                if row.note:
                    note = f"   ({i18n.key_raw(row.note) if row.note in i18n._STRINGS else row.note})"
                if str(value).strip():
                    self.details.insert("end", shape(f"{label}: {value}{note}\n"))
                else:
                    self.details.insert("end", shape(f"{label}{note}\n"))
            if result.error:
                self.details.insert("end", shape(f"\n{result.error}\n"), ("muted",))
        self.details.configure(state="disabled")

    # ------------------------------------------------------------------ #
    # stress chart
    # ------------------------------------------------------------------ #
    def _show_chart(self, visible: bool) -> None:
        if visible and self.chart_hidden:
            self.chart.grid(row=1, column=0, sticky="sew", pady=(8, 0))
            self.details_frame.rowconfigure(1, weight=0)
            self.chart_hidden = False
        elif not visible and not self.chart_hidden:
            self.chart.grid_forget()
            self.chart_hidden = True

    def _draw_chart(self) -> None:
        if self.chart_hidden:
            return
        chart = self.chart
        chart.delete("all")
        width = chart.winfo_width() or 600
        height = chart.winfo_height() or 120
        temps = [s["temp"] for s in self.samples if s.get("temp") is not None]
        if not temps:
            chart.create_text(width / 2, height / 2, text=shape(i18n.tr("verdict.no_sensor")),
                              fill=MUTED, font=("Segoe UI", 10))
            return
        low, high = min(temps), max(temps)
        if high - low < 5:
            low, high = low - 2.5, high + 2.5
        pad = 18
        span = max(len(temps) - 1, 1)
        points = []
        for index, temp in enumerate(temps):
            x = pad + (width - 2 * pad) * index / span
            y = height - pad - (height - 2 * pad) * (temp - low) / max(high - low, 1e-6)
            points.append((x, y))
        chart.create_line(pad, height - pad, width - pad, height - pad, fill="#233246")
        for fraction, value in ((1.0, high), (0.5, (high + low) / 2), (0.0, low)):
            y = height - pad - (height - 2 * pad) * fraction
            chart.create_line(pad, y, width - pad, y, fill="#1b2331")
            chart.create_text(pad - 4, y, text=f"{value:.0f}", fill=MUTED,
                              font=("Segoe UI", 8), anchor="e")
        if len(points) > 1:
            chart.create_line(*[coord for point in points for coord in point],
                              fill="#f97316", width=2, smooth=True)
        chart.create_text(width - pad, pad, text=f"{temps[-1]:.1f} °C", fill="#f97316",
                          font=("Segoe UI", 10, "bold"), anchor="ne")

    # ------------------------------------------------------------------ #
    # actions
    # ------------------------------------------------------------------ #
    def save_report(self) -> None:
        if not [r for r in self.data.values() if r.status not in (PENDING, RUNNING)]:
            messagebox.showinfo("PCScope", i18n.tr("msg.no_results"))
            return
        default = report.default_filenames()["html"]
        path = filedialog.asksaveasfilename(
            title=i18n.tr("msg.save_title"),
            initialdir=util.default_report_dir(),
            initialfile=default,
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Text", "*.txt"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            lowered = path.lower()
            if lowered.endswith(".txt"):
                report.write_text(self.data, path)
            elif lowered.endswith(".json"):
                report.write_json(self.data, path)
            else:
                report.write_html(self.data, path)
        except OSError as exc:
            messagebox.showerror("PCScope", i18n.tr("msg.save_failed", err=str(exc)))
            return
        self.status_var.set(shape(i18n.tr("msg.saved", path=path)))

    def copy_summary(self) -> None:
        if not [r for r in self.data.values() if r.status not in (PENDING, RUNNING)]:
            messagebox.showinfo("PCScope", i18n.tr("msg.no_results"))
            return
        text = report.summary_text(self.data)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set(shape(i18n.tr("msg.copied")))

    def open_monitor_test(self) -> None:
        if self.monitor_test is None or self.monitor_test.window is None:
            self.monitor_test = monitor.MonitorTest(self.root)
        self.monitor_test.open()

    def show_about(self) -> None:
        messagebox.showinfo(
            "PCScope",
            f"PCScope {util.APP_VERSION}\n"
            f"{i18n.tr('app.subtitle')}\n\n"
            "Python + Tkinter + psutil\n"
            "License: PolyForm Noncommercial 1.0.0 (same as this repository)",
        )

    # ------------------------------------------------------------------ #
    # startup info
    # ------------------------------------------------------------------ #
    def _load_system_info_async(self) -> None:
        def worker() -> None:
            try:
                result = runner.run("system")
                self.data.computer = next(
                    (str(row.value) for row in result.rows if row.label == "key.machine"), ""
                )
                self.data.language = i18n.get_language()
                self.data.add(result)
                self.queue.put(("result", result))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()


def launch(lang: Optional[str] = None) -> None:
    """Create the window and run the Tk main loop."""
    if lang:
        i18n.set_language(lang)
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = App(root)
    root.mainloop()
