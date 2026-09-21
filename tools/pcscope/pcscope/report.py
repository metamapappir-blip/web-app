"""Report writers: plain text, self-contained HTML and JSON."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from . import i18n, util
from .results import FAIL, INFO, PASS, SKIPPED, WARN, ResultSet

_STATUS_COLORS = {
    PASS: "#16a34a",
    WARN: "#d97706",
    FAIL: "#dc2626",
    INFO: "#0284c7",
    SKIPPED: "#64748b",
}

_HTML_CSS = """
:root { color-scheme: light; }
body { margin: 0; padding: 32px; background: #f6f8fb; color: #0f172a;
       font: 15px/1.65 "Segoe UI", Tahoma, system-ui, sans-serif; }
.wrap { max-width: 960px; margin: 0 auto; }
h1 { margin: 0 0 4px; font-size: 26px; }
.sub { color: #64748b; margin-bottom: 24px; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
        padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.card h2 { margin: 0 0 4px; font-size: 18px; }
.card .verdict { font-weight: 600; margin-bottom: 12px; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: start; padding: 6px 8px; border-bottom: 1px solid #eef2f7; font-size: 14px; }
th { color: #64748b; font-weight: 600; }
td.v { font-variant-numeric: tabular-nums; }
td.note { color: #64748b; font-size: 13px; }
.pill { display: inline-block; padding: 2px 10px; border-radius: 999px; color: #fff;
        font-size: 12px; font-weight: 600; }
.meta { color: #64748b; font-size: 13px; }
.legend { margin-top: 8px; color: #64748b; font-size: 13px; }
.foot { color: #94a3b8; font-size: 12px; margin-top: 24px; }
[dir="rtl"] body { font-family: "Segoe UI", Tahoma, "Vazirmatn", sans-serif; }
"""


def _status_color(status: str) -> str:
    return _STATUS_COLORS.get(status, "#64748b")


def _escape(text: Any) -> str:
    text = "" if text is None else str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _label(lang: str, key: str) -> str:
    previous = i18n.get_language()
    i18n.set_language(lang)
    try:
        return i18n.key_raw(key)
    finally:
        i18n.set_language(previous)


def _verdict(lang: str, value: str, is_key: bool) -> str:
    if not is_key:
        return value
    previous = i18n.get_language()
    i18n.set_language(lang)
    try:
        return i18n.tr(value)
    finally:
        i18n.set_language(previous)


def export_payload(data: ResultSet, lang: Optional[str] = None) -> Dict[str, Any]:
    return data.to_dict(lang or data.language or "en")


def write_json(data: ResultSet, path: str, lang: Optional[str] = None) -> str:
    payload = export_payload(data, lang)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def write_text(data: ResultSet, path: str, lang: Optional[str] = None) -> str:
    lang = lang or data.language or "en"
    previous = i18n.get_language()
    i18n.set_language(lang)
    try:
        lines: List[str] = []
        lines.append("=" * 68)
        lines.append(f"{i18n.tr('report.title')}  -  PCScope {util.APP_VERSION}")
        lines.append("=" * 68)
        lines.append(f"{i18n.tr('report.generated')}: {util.now_stamp()}")
        if data.computer:
            lines.append(f"{i18n.tr('report.computer')}: {data.computer}")
        duration = data.duration()
        if duration:
            lines.append(f"{i18n.tr('key.duration')}: {util.human_duration(duration)}")
        counts = data.counts()
        if counts:
            summary = "  ".join(
                f"{i18n.status_word_raw(status)}: {count}" for status, count in counts.items()
            )
            lines.append(f"{i18n.tr('report.summary')}: {summary}")
        lines.append("")
        for res in data.values():
            if res.status in ("pending", "running"):
                continue
            lines.append("-" * 68)
            lines.append(f"[{i18n.status_word_raw(res.status)}] {i18n.tr(res.title_key)}")
            if res.summary:
                lines.append(f"    {i18n.tr(res.summary) if res.summary_is_key else res.summary}")
            for row in res.rows:
                label = i18n.key_raw(row.label) if row.label in i18n._STRINGS else row.label
                value = _verdict(lang, row.value, row.value in i18n._STRINGS)
                note = ""
                if row.note:
                    note = f"  ({i18n.key_raw(row.note) if row.note in i18n._STRINGS else row.note})"
                if not str(value).strip():
                    lines.append(f"    {label}{note}")
                else:
                    lines.append(f"    {label}: {value}{note}")
            if res.duration:
                lines.append(f"    {i18n.key_raw('key.duration')}: {util.human_duration(res.duration)}")
            lines.append("")
        lines.append(i18n.tr("report.legend"))
        lines.append(i18n.tr("report.disclaimer"))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    finally:
        i18n.set_language(previous)
    return path


def write_html(data: ResultSet, path: str, lang: Optional[str] = None) -> str:
    lang = lang or data.language or "en"
    previous = i18n.get_language()
    i18n.set_language(lang)
    rtl = lang == "fa"
    try:
        parts: List[str] = []
        parts.append("<!DOCTYPE html>")
        parts.append(f'<html lang="{lang}" dir="{"rtl" if rtl else "ltr"}">')
        parts.append("<head><meta charset=\"utf-8\">")
        parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
        parts.append(f"<title>{_escape(i18n.tr('report.title'))}</title>")
        parts.append(f"<style>{_HTML_CSS}</style>")
        parts.append("</head><body><div class='wrap'>")
        parts.append(f"<h1>{_escape(i18n.tr('report.title'))}</h1>")
        parts.append(
            f"<div class='sub'>PCScope {util.APP_VERSION} &middot; "
            f"{_escape(i18n.tr('report.generated'))}: {_escape(util.now_stamp())}"
            + (f" &middot; {_escape(data.computer)}" if data.computer else "")
            + "</div>"
        )

        counts = data.counts()
        if counts:
            chips = " ".join(
                f"<span class='pill' style='background:{_status_color(status)}'>"
                f"{_escape(i18n.status_word_raw(status))}: {count}</span>"
                for status, count in counts.items()
            )
            parts.append(f"<div class='card'><div>{chips}</div>")
            duration = data.duration()
            if duration:
                parts.append(
                    f"<div class='meta' style='margin-top:8px'>"
                    f"{_escape(i18n.key_raw('key.duration'))}: "
                    f"{_escape(util.human_duration(duration))}</div>"
                )
            parts.append("</div>")

        for res in data.values():
            if res.status in ("pending", "running"):
                continue
            parts.append("<div class='card'>")
            pill = (
                f"<span class='pill' style='background:{_status_color(res.status)}'>"
                f"{_escape(i18n.status_word_raw(res.status))}</span>"
            )
            parts.append(f"<h2>{_escape(i18n.tr(res.title_key))} {pill}</h2>")
            if res.summary:
                verdict = _verdict(lang, res.summary, res.summary_is_key)
                parts.append(f"<div class='verdict'>{_escape(verdict)}</div>")
            if res.rows:
                parts.append("<table>")
                for row in res.rows:
                    label = i18n.key_raw(row.label) if row.label in i18n._STRINGS else row.label
                    value = _verdict(lang, row.value, row.value in i18n._STRINGS)
                    note = ""
                    if row.note:
                        note = i18n.key_raw(row.note) if row.note in i18n._STRINGS else row.note
                    row_color = _status_color(row.status) if row.status else ""
                    value_html = (
                        f"<span style='color:{row_color}'>{_escape(value)}</span>"
                        if row_color and row.status in (WARN, FAIL)
                        else _escape(value)
                    )
                    parts.append(
                        f"<tr><td>{_escape(label)}</td>"
                        f"<td class='v'>{value_html}</td>"
                        f"<td class='note'>{_escape(note)}</td></tr>"
                    )
                parts.append("</table>")
            footer: List[str] = []
            if res.duration:
                footer.append(f"{i18n.key_raw('key.duration')}: {util.human_duration(res.duration)}")
            if res.error:
                footer.append(_escape(res.error))
            if footer:
                parts.append(f"<div class='meta' style='margin-top:8px'>{' &middot; '.join(footer)}</div>")
            parts.append("</div>")

        parts.append(f"<div class='card'><div class='legend'>{_escape(i18n.tr('report.legend'))}</div></div>")
        parts.append(f"<div class='foot'>{_escape(i18n.tr('report.disclaimer'))}</div>")
        parts.append("</div></body></html>")

        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(parts))
    finally:
        i18n.set_language(previous)
    return path


def summary_text(data: ResultSet, lang: Optional[str] = None) -> str:
    """Short plain-text digest, used by the clipboard button."""
    lang = lang or data.language or "en"
    previous = i18n.get_language()
    i18n.set_language(lang)
    try:
        lines = [f"PCScope {util.APP_VERSION} - {util.now_stamp()}"]
        if data.computer:
            lines.append(data.computer)
        for res in data.values():
            if res.status in ("pending", "running"):
                continue
            verdict = _verdict(lang, res.summary, res.summary_is_key)
            lines.append(f"- {i18n.tr(res.title_key)}: {verdict}")
        counts = data.counts()
        if counts:
            lines.append(
                "  ".join(f"{i18n.status_word_raw(k)}: {v}" for k, v in counts.items())
            )
        return "\n".join(lines)
    finally:
        i18n.set_language(previous)


def default_filenames(stamp: Optional[str] = None) -> Dict[str, str]:
    stamp = stamp or util.stamp_for_filename()
    base = f"pcscope-report-{stamp}"
    return {"txt": base + ".txt", "html": base + ".html", "json": base + ".json"}


def save_all(data: ResultSet, directory: str, lang: Optional[str] = None) -> Dict[str, str]:
    """Write txt/html/json next to each other and return their paths."""
    os.makedirs(directory, exist_ok=True)
    names = default_filenames()
    return {
        "txt": write_text(data, os.path.join(directory, names["txt"]), lang),
        "html": write_html(data, os.path.join(directory, names["html"]), lang),
        "json": write_json(data, os.path.join(directory, names["json"]), lang),
    }
