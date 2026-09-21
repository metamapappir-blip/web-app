"""Result model shared by the GUI, the CLI and the report writers.

Every probe returns a :class:`Result`. A result carries a machine status
(``pass``/``warn``/``fail``/``info``/``skipped``), a one-line human summary and
a list of detail rows. Detail rows store a *translation key* as their label so a
report can be rendered later in either language.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

PASS = "pass"
WARN = "warn"
FAIL = "fail"
INFO = "info"
PENDING = "pending"
RUNNING = "running"
SKIPPED = "skipped"

STATUS_ORDER = {FAIL: 0, WARN: 1, PASS: 2, INFO: 3, SKIPPED: 4, PENDING: 5, RUNNING: 6}


@dataclass
class Row:
    """One ``label: value`` line. ``label`` is an i18n key or literal text."""

    label: str
    value: Any = ""
    note: str = ""
    status: Optional[str] = None

    def as_tuple(self) -> Tuple[str, Any, str, Optional[str]]:
        return (self.label, self.value, self.note, self.status)


@dataclass
class Result:
    id: str
    title_key: str
    status: str = PENDING
    summary: str = ""          # already-human text (may be a verdict key)
    summary_is_key: bool = False
    score: Optional[float] = None
    unit: str = ""
    rows: List[Row] = field(default_factory=list)
    duration: Optional[float] = None
    error: str = ""

    # -- construction helpers ------------------------------------------- #
    def add(self, label: str, value: Any = "", note: str = "", status: Optional[str] = None) -> "Result":
        self.rows.append(Row(label, value, note, status))
        return self

    def finish(self, status: str, summary: str = "", summary_is_key: bool = False) -> "Result":
        self.status = status
        self.summary = summary
        self.summary_is_key = summary_is_key
        return self

    # -- serialisation --------------------------------------------------- #
    def to_dict(self, lang: str = "en") -> Dict[str, Any]:
        from . import i18n

        previous = i18n.get_language()
        i18n.set_language(lang)
        try:
            summary = i18n.tr(self.summary) if self.summary_is_key else self.summary
            rows = []
            for row in self.rows:
                label = i18n.key_raw(row.label) if row.label in i18n._STRINGS else row.label
                note = i18n.tr(row.note) if row.note in i18n._STRINGS else row.note
                rows.append(
                    {
                        "label": label,
                        "value": _jsonable(row.value),
                        "note": note,
                        "status": row.status,
                    }
                )
            return {
                "id": self.id,
                "title": i18n.tr(self.title_key) if self.title_key in i18n._STRINGS else self.title_key,
                "status": self.status,
                "summary": summary,
                "score": self.score,
                "unit": self.unit,
                "duration": self.duration,
                "error": self.error,
                "rows": rows,
            }
        finally:
            i18n.set_language(previous)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class ResultSet:
    """Ordered collection of results with a few aggregate helpers."""

    def __init__(self) -> None:
        self.results: Dict[str, Result] = {}
        self.order: List[str] = []
        self.started: Optional[float] = None
        self.finished: Optional[float] = None
        self.computer: str = ""
        self.language: str = "en"

    # -- lifecycle -------------------------------------------------------- #
    def begin(self) -> None:
        self.started = time.time()
        self.finished = None

    def end(self) -> None:
        self.finished = time.time()

    def add(self, result: Result) -> Result:
        if result.id not in self.results:
            self.order.append(result.id)
        self.results[result.id] = result
        return result

    def get(self, result_id: str) -> Optional[Result]:
        return self.results.get(result_id)

    def values(self) -> List[Result]:
        return [self.results[i] for i in self.order if i in self.results]

    def clear(self) -> None:
        self.results.clear()
        self.order.clear()
        self.started = None
        self.finished = None

    # -- aggregates ------------------------------------------------------- #
    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for res in self.values():
            if res.status in (PENDING, RUNNING):
                continue
            out[res.status] = out.get(res.status, 0) + 1
        return out

    def overall(self) -> str:
        counts = self.counts()
        if not counts:
            return PENDING
        if counts.get(FAIL):
            return FAIL
        if counts.get(WARN):
            return WARN
        if counts.get(PASS):
            return PASS
        return INFO

    def duration(self) -> Optional[float]:
        if self.started is None:
            return None
        end = self.finished if self.finished is not None else time.time()
        return end - self.started

    def to_dict(self, lang: Optional[str] = None) -> Dict[str, Any]:
        lang = lang or self.language
        return {
            "app": "PCScope",
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "language": lang,
            "computer": self.computer,
            "duration": self.duration(),
            "overall": self.overall(),
            "counts": self.counts(),
            "results": [res.to_dict(lang) for res in self.values()],
        }


def grade_thresholds(value: Optional[float], good: float, fair: float, low: float) -> str:
    """Map a *higher is better* value onto the excellent/good/fair/slow scale."""
    if value is None:
        return "verdict.normal"
    if value >= good:
        return "verdict.excellent"
    if value >= fair:
        return "verdict.good"
    if value >= low:
        return "verdict.fair"
    return "verdict.slow"
