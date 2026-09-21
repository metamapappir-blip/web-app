"""Bilingual (English / Persian) string table for PCScope.

Tkinter on Windows does not shape or reorder Arabic-script text, so Persian
strings are passed through :func:`shape` before they reach a widget. The raw
(Unicode) strings stay untouched for the HTML report, where the browser does
bidi and shaping on its own.
"""

from __future__ import annotations

from typing import Dict, List, Optional

LANGS = ("en", "fa")

# key -> (english, persian)
_STRINGS: Dict[str, List[str]] = {
    "app.title": ["PCScope - PC Hardware Diagnostics", "پی‌سی‌اسکوپ - تست سخت‌افزار کامپیوتر"],
    "app.subtitle": [
        "Check, benchmark and stress-test your computer",
        "بررسی، بنچمارک و تست استرس قطعات کامپیوتر",
    ],
    "app.version": ["Version", "نسخه"],
    "app.about": ["About", "درباره"],
    "app.quit": ["Quit", "خروج"],

    "btn.run_selected": ["Run selected", "اجرای موارد انتخاب‌شده"],
    "btn.run_all": ["Run all", "اجرای همه"],
    "btn.stop": ["Stop", "توقف"],
    "btn.save_txt": ["Save report (TXT)", "ذخیره گزارش (TXT)"],
    "btn.save_html": ["Save report (HTML)", "ذخیره گزارش (HTML)"],
    "btn.save_json": ["Save report (JSON)", "ذخیره گزارش (JSON)"],
    "btn.copy": ["Copy summary", "کپی خلاصه"],
    "btn.monitor": ["Monitor test", "تست مانیتور"],
    "btn.refresh": ["Refresh info", "به‌روزرسانی اطلاعات"],
    "btn.language": ["English", "English"],
    "btn.close": ["Close", "بستن"],
    "btn.open_report": ["Open report", "باز کردن گزارش"],

    "hdr.tests": ["Tests", "تست‌ها"],
    "hdr.results": ["Results", "نتایج"],
    "hdr.details": ["Details", "جزئیات"],
    "hdr.summary": ["System", "سیستم"],

    "col.test": ["Test", "تست"],
    "col.result": ["Result", "نتیجه"],
    "col.status": ["Status", "وضعیت"],

    "status.pass": ["OK", "سالم"],
    "status.warn": ["Warning", "هشدار"],
    "status.fail": ["Problem", "مشکل"],
    "status.info": ["Info", "اطلاعات"],
    "status.running": ["Running", "در حال اجرا"],
    "status.pending": ["Not run", "اجرا نشده"],
    "status.skipped": ["Skipped", "رد شده"],
    "status.unsupported": ["Not available", "در دسترس نیست"],

    "msg.ready": ["Ready.", "آماده."],
    "msg.running": ["Running: {name}", "در حال اجرا: {name}"],
    "msg.done": ["Done in {secs}.", "پایان در {secs}."],
    "msg.stopped": ["Stopped by user.", "توسط کاربر متوقف شد."],
    "msg.saved": ["Report saved to:\n{path}", "گزارش ذخیره شد:\n{path}"],
    "msg.copied": ["Summary copied to clipboard.", "خلاصه در کلیپ‌بورد کپی شد."],
    "msg.no_tests": ["Select at least one test.", "حداقل یک تست را انتخاب کنید."],
    "msg.no_results": ["Run a test first.", "ابتدا یک تست اجرا کنید."],
    "msg.save_failed": ["Could not save the report:\n{err}", "ذخیره گزارش ناموفق بود:\n{err}"],
    "msg.save_title": ["Save report", "ذخیره گزارش"],

    "label.progress": ["Progress", "پیشرفت"],
    "label.system": ["System", "سیستم"],
    "label.select_all": ["Select all", "انتخاب همه"],
    "label.select_none": ["Clear", "لغو انتخاب"],
    "label.long_warning": [
        "Disk, memory and stress tests move a lot of data and take time. Close other apps first.",
        "تست‌های دیسک، حافظه و استرس حجم زیادی داده جابه‌جا می‌کنند و زمان‌بر هستند. برنامه‌های دیگر را ببندید.",
    ],

    # ---- test catalogue -------------------------------------------------- #
    "test.system": ["System information", "اطلاعات سیستم"],
    "test.system.desc": [
        "CPU, motherboard, memory, storage, GPU and OS inventory",
        "مشخصات پردازنده، مادربرد، رم، دیسک، کارت گرافیک و ویندوز",
    ],
    "test.cpu": ["CPU benchmark", "بنچمارک پردازنده"],
    "test.cpu.desc": [
        "Single-core and multi-core integer throughput plus core scaling",
        "توان پردازش تک‌هسته و چندهسته به‌همراه بررسی مقیاس‌پذیری هسته‌ها",
    ],
    "test.memory": ["Memory (RAM) test", "تست حافظه رم"],
    "test.memory.desc": [
        "Read/write bandwidth and a data-integrity check",
        "سرعت خواندن/نوشتن و بررسی صحت داده‌ها",
    ],
    "test.disk": ["Disk speed test", "تست سرعت دیسک"],
    "test.disk.desc": [
        "Sequential and random 4K read/write throughput on the system drive",
        "سرعت خواندن/نوشتن پیاپی و تصادفی ۴کی روی درایو سیستم",
    ],
    "test.disk_health": ["Disk health", "سلامت دیسک"],
    "test.disk_health.desc": [
        "Drive model, type, free space and reported health status",
        "مدل، نوع، فضای آزاد و وضعیت سلامت گزارش‌شده درایوها",
    ],
    "test.gpu": ["GPU and display", "کارت گرافیک و نمایشگر"],
    "test.gpu.desc": [
        "Graphics adapter, driver, resolution and refresh rate",
        "کارت گرافیک، درایور، رزولوشن و نرخ نوسازی",
    ],
    "test.network": ["Network test", "تست شبکه"],
    "test.network.desc": [
        "Adapter info, latency, packet loss and download/upload speed",
        "اطلاعات کارت شبکه، تاخیر، افت بسته و سرعت دانلود/آپلود",
    ],
    "test.battery": ["Battery health", "سلامت باتری"],
    "test.battery.desc": [
        "Charge level, wear level and cycle count",
        "میزان شارژ، استهلاک و تعداد چرخه شارژ",
    ],
    "test.thermal": ["Temperature and fans", "دما و فن"],
    "test.thermal.desc": [
        "Available thermal sensors (needs admin on many laptops)",
        "سنسورهای دمای در دسترس (در بسیاری از لپ‌تاپ‌ها نیاز به اجرا با دسترسی مدیر دارد)",
    ],
    "test.monitor": ["Monitor / dead pixel test", "تست مانیتور / پیکسل سوخته"],
    "test.monitor.desc": [
        "Full-screen solid colours to spot dead or stuck pixels",
        "نمایش تمام‌صفحه رنگ‌های یکدست برای یافتن پیکسل سوخته یا گیرکرده",
    ],
    "test.audio": ["Speaker test", "تست اسپیکر"],
    "test.audio.desc": [
        "Plays short tones on the default output device",
        "پخش صداهای کوتاه روی خروجی پیش‌فرض",
    ],
    "test.stress": ["Stability stress test", "تست استرس پایداری"],
    "test.stress.desc": [
        "Sustained CPU load while sampling clocks and temperatures",
        "بار مداوم پردازنده همراه با نمونه‌برداری از فرکانس و دما",
    ],

    # ---- shared result vocabulary ---------------------------------------- #
    "key.cpu": ["Processor", "پردازنده"],
    "key.cpu_cores": ["Cores / threads", "هسته / رشته"],
    "key.cpu_base": ["Base clock", "فرکانس پایه"],
    "key.cpu_current": ["Current clock", "فرکانس فعلی"],
    "key.motherboard": ["Motherboard", "مادربرد"],
    "key.bios": ["BIOS", "بایوس"],
    "key.ram_total": ["Installed memory", "حافظه نصب‌شده"],
    "key.ram_modules": ["Memory modules", "ماژول‌های حافظه"],
    "key.ram_type": ["Memory type", "نوع حافظه"],
    "key.os": ["Operating system", "سیستم‌عامل"],
    "key.uptime": ["Uptime", "زمان روشن بودن"],
    "key.machine": ["Computer", "کامپیوتر"],
    "key.gpu": ["Graphics", "کارت گرافیک"],
    "key.driver": ["Driver version", "نسخه درایور"],
    "key.vram": ["Video memory", "حافظه گرافیکی"],
    "key.display": ["Display", "نمایشگر"],
    "key.refresh": ["Refresh rate", "نرخ نوسازی"],
    "key.disk": ["Disk", "دیسک"],
    "key.disk_type": ["Media type", "نوع رسانه"],
    "key.disk_free": ["Free space", "فضای آزاد"],
    "key.disk_total": ["Capacity", "ظرفیت"],
    "key.network": ["Network adapter", "کارت شبکه"],
    "key.ip": ["IP address", "آدرس آی‌پی"],
    "key.mac": ["MAC address", "آدرس مک"],
    "key.wifi": ["Wi-Fi network", "شبکه وای‌فای"],
    "key.latency": ["Latency", "تاخیر"],
    "key.loss": ["Packet loss", "افت بسته"],
    "key.download": ["Download", "دانلود"],
    "key.upload": ["Upload", "آپلود"],
    "key.score": ["Score", "امتیاز"],
    "key.bandwidth": ["Bandwidth", "پهنای باند"],
    "key.integrity": ["Integrity", "صحت داده"],
    "key.duration": ["Duration", "مدت"],
    "key.temperature": ["Temperature", "دما"],
    "key.state": ["State", "وضعیت"],
    "key.wear": ["Wear level", "میزان استهلاک"],
    "key.cycles": ["Charge cycles", "چرخه شارژ"],
    "key.design_capacity": ["Design capacity", "ظرفیت طراحی"],
    "key.full_capacity": ["Full charge capacity", "ظرفیت شارژ کامل"],
    "key.time_left": ["Time remaining", "زمان باقی‌مانده"],
    "key.power": ["Power", "توان"],
    "key.file_size": ["Test file", "فایل تست"],
    "key.issues": ["Notes", "نکات"],
    "key.cache": ["Cache", "حافظه کش"],
    "key.written": ["Data verified", "داده بررسی‌شده"],
    "key.iops": ["Random 4K IOPS", "آی‌او‌پی‌اس تصادفی ۴کی"],
    "key.threads": ["Threads", "رشته‌ها"],
    "key.scaling": ["Multi-core scaling", "مقیاس‌پذیری چندهسته‌ای"],
    "key.clocks": ["Clock during test", "فرکانس حین تست"],
    "key.min": ["Minimum", "کمینه"],
    "key.max": ["Maximum", "بیشینه"],
    "key.average": ["Average", "میانگین"],
    "key.samples": ["Samples", "نمونه‌ها"],
    "key.result": ["Result", "نتیجه"],

    "note.low_ram": [
        "Less than 4 GB of memory installed",
        "کمتر از ۴ گیگابایت حافظه نصب شده",
    ],
    "note.few_cores": [
        "Two physical cores or fewer",
        "دو هسته فیزیکی یا کمتر",
    ],
    "note.low_disk": [
        "Less than 10% free space on a drive",
        "کمتر از ۱۰٪ فضای آزاد روی یک درایو",
    ],
    "note.cache_small": ["Windows disk cache may inflate read speed", "کش ویندوز ممکن است سرعت خواندن را بالاتر نشان دهد"],
    "note.single_core": ["single-core", "تک‌هسته"],
    "note.multi_core": ["multi-core", "چندهسته"],
    "note.write": ["write", "نوشتن"],
    "note.read": ["read", "خواندن"],
    "note.compare": ["compare pass", "مرحله مقایسه"],
    "note.seq_write": ["sequential write", "نوشتن پیاپی"],
    "note.seq_read": ["sequential read", "خواندن پیاپی"],
    "note.mixed_4k": ["4K mixed (OS cache)", "۴کی ترکیبی (کش سیستم‌عامل)"],
    "note.tcp": ["TCP handshake", "اتصال TCP"],
    "note.best": ["best", "بهترین"],
    "note.ping_avg": ["ping average", "میانگین پینگ"],
    "note.temp": ["temperature", "دما"],
    "note.avg": ["average", "میانگین"],
    "note.cpu_load": ["CPU load", "بار پردازنده"],
    "note.health": ["health", "سلامت"],
    "note.low_scaling": [
        "Multi-core score is low for this core count",
        "امتیاز چندهسته‌ای برای این تعداد هسته کم است",
    ],
    "note.multicore_unavailable": [
        "Multi-core test could not start",
        "تست چندهسته‌ای اجرا نشد",
    ],
    "note.throttle": [
        "Clock dropped below 75% under load",
        "فرکانس زیر بار به کمتر از ۷۵٪ رسید",
    ],
    "note.ping_blocked": [
        "ICMP ping is blocked on this network (TCP still works)",
        "پینگ ICMP در این شبکه مسدود است (اتصال TCP برقرار است)",
    ],
    "note.admin_required": [
        "Run as administrator for more sensors",
        "برای دسترسی به سنسورهای بیشتر با دسترسی مدیر اجرا کنید",
    ],

    "verdict.excellent": ["Excellent", "عالی"],
    "verdict.good": ["Good", "خوب"],
    "verdict.fair": ["Fair", "متوسط"],
    "verdict.slow": ["Slow", "کند"],
    "verdict.normal": ["Normal", "عادی"],
    "verdict.high": ["High", "بالا"],
    "verdict.idle": ["Idle", "بیکار"],
    "verdict.present": ["Available", "موجود"],
    "verdict.plugged": ["Plugged in", "متصل به برق"],
    "verdict.discharging": ["On battery", "روی باتری"],
    "verdict.charging": ["Charging", "در حال شارژ"],
    "verdict.passed": ["No errors found", "خطایی یافت نشد"],
    "verdict.failed": ["Errors found", "خطا یافت شد"],
    "verdict.offline": ["No internet connection", "اتصال اینترنت ندارد"],
    "verdict.no_sensor": ["No sensor reported", "هیچ سنسوری گزارش نشد"],
    "verdict.desktop": ["No battery (desktop)", "باتری ندارد (کامپیوتر رومیزی)"],
    "verdict.stable": ["Stable", "پایدار"],
    "verdict.throttled": ["Thermal throttling detected", "افت فرکانس حرارتی مشاهده شد"],
    "verdict.ok": ["Completed", "انجام شد"],
    "verdict.cancelled": ["Cancelled", "لغو شد"],

    # ---- monitor test ----------------------------------------------------- #
    "monitor.title": ["Monitor test", "تست مانیتور"],
    "monitor.help": [
        "Colours cycle automatically every 3 seconds.\n"
        "Space = pause, N = next colour, Esc = exit.\n"
        "Look for pixels that stay black, white or stuck on one colour.",
        "رنگ‌ها هر ۳ ثانیه به‌طور خودکار عوض می‌شوند.\n"
        "Space = توقف، N = رنگ بعدی، Esc = خروج.\n"
        "دنبال پیکسل‌هایی بگردید که سیاه، سفید یا روی یک رنگ گیر کرده‌اند.",
    ],
    "monitor.next": ["Next: {name}", "بعدی: {name}"],

    "colour.black": ["Black", "مشکی"],
    "colour.white": ["White", "سفید"],
    "colour.red": ["Red", "قرمز"],
    "colour.green": ["Green", "سبز"],
    "colour.blue": ["Blue", "آبی"],
    "colour.gray": ["Gray", "خاکستری"],
    "colour.magenta": ["Magenta", "ارغوانی"],
    "colour.cyan": ["Cyan", "فیروزه‌ای"],
    "colour.yellow": ["Yellow", "زرد"],

    # ---- report ----------------------------------------------------------- #
    "report.title": ["PCScope hardware report", "گزارش سخت‌افزار پی‌سی‌اسکوپ"],
    "report.generated": ["Generated", "تاریخ تهیه"],
    "report.computer": ["Computer", "کامپیوتر"],
    "report.summary": ["Summary", "خلاصه"],
    "report.section": ["Section", "بخش"],
    "report.value": ["Value", "مقدار"],
    "report.note": ["Note", "توضیح"],
    "report.legend": [
        "OK = nothing to fix, Warning = keep an eye on it, Problem = act on it, Info = informational.",
        "سالم = موردی نیست، هشدار = زیر نظر بگیرید، مشکل = نیاز به رسیدگی، اطلاعات = صرفاً اطلاعی.",
    ],
    "report.disclaimer": [
        "Numbers depend on drivers, power profile, background load and cooling. "
        "Compare them with the same machine over time rather than with other PCs.",
        "اعداد به درایورها، پروفایل برق، بار پس‌زمینه و خنک‌کنندگی وابسته است. "
        "این اعداد را با همین دستگاه در زمان‌های مختلف مقایسه کنید، نه با کامپیوترهای دیگر.",
    ],
}

_FALLBACK = "en"
_current = "en"

# Optional Arabic-script shaping (Tkinter cannot render Persian on its own).
_reshape = None
_bidi_display = None
_shaping_ready = False


def _load_shaping() -> None:
    global _reshape, _bidi_display, _shaping_ready
    if _shaping_ready:
        return
    _shaping_ready = True
    try:
        import arabic_reshaper  # type: ignore

        _reshape = arabic_reshaper.reshape
    except Exception:
        _reshape = None
    try:
        from bidi.algorithm import get_display  # type: ignore

        _bidi_display = get_display
    except Exception:
        _bidi_display = None


def shaping_available() -> bool:
    _load_shaping()
    return _reshape is not None and _bidi_display is not None


def shape(text: str) -> str:
    """Reshape/reorder Persian text so Tkinter can draw it correctly."""
    if not text or _current != "fa":
        return text
    _load_shaping()
    try:
        if _reshape is not None:
            text = _reshape(text)
        if _bidi_display is not None:
            text = _bidi_display(text)
    except Exception:
        return text
    return text


def set_language(lang: str) -> None:
    global _current
    _current = lang if lang in LANGS else _FALLBACK


def get_language() -> str:
    return _current


def is_rtl() -> bool:
    return _current == "fa"


def toggle_language() -> str:
    set_language("fa" if _current == "en" else "en")
    return _current


def tr(key: str, **kwargs) -> str:
    """Translate ``key`` for the active language (raw Unicode, unshaped)."""
    values = _STRINGS.get(key)
    if not values:
        return key
    text = values[0] if _current == "en" else (values[1] or values[0])
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def t(key: str, **kwargs) -> str:
    """Translate and shape - use this for anything drawn by Tkinter."""
    return shape(tr(key, **kwargs))


def key_label(key: str) -> str:
    """Translate a detail-row label such as ``key.cpu`` (shaped for Tk)."""
    return t(key) if key in _STRINGS else key


def key_raw(key: str) -> str:
    """Translate a detail-row label for the HTML/text report (unshaped)."""
    return tr(key) if key in _STRINGS else key


def verdict_word(key: str) -> str:
    return t(key)


def verdict_raw(key: str) -> str:
    return tr(key)


def status_word(status: str) -> str:
    """Shaped for Tkinter widgets."""
    return t(f"status.{status}")


def status_word_raw(status: str) -> str:
    """Raw Unicode - for terminals, text files and HTML (browsers do bidi)."""
    return tr(f"status.{status}")
