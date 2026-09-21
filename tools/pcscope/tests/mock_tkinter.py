"""A tiny stand-in for tkinter so the UI can be smoke-tested on a headless box.

It is deliberately dumb: it records what the UI asks for and returns plausible
values, which is enough to catch attribute typos, bad keyword arguments and
broken control flow without an X server.
"""

from __future__ import annotations

import sys
import types
from typing import Any, Dict, List, Optional, Tuple

CALLS: List[Tuple[str, Any]] = []


class TclError(Exception):
    pass


class Widget:
    def __init__(self, master=None, **kwargs: Any):
        self.master = master
        self.kwargs: Dict[str, Any] = dict(kwargs)
        self.children: List["Widget"] = []
        self._values: Dict[str, Any] = {}
        self._after_jobs: List[Any] = []
        self._width = 900
        self._height = 600
        if master is not None and hasattr(master, "children"):
            master.children.append(self)
        CALLS.append(("create", self.__class__.__name__, dict(kwargs)))

    # -- geometry -------------------------------------------------------- #
    def pack(self, **kwargs: Any) -> None:
        CALLS.append(("pack", self, kwargs))

    def grid(self, **kwargs: Any) -> None:
        CALLS.append(("grid", self, kwargs))

    def grid_forget(self) -> None:
        CALLS.append(("grid_forget", self, None))

    def pack_forget(self) -> None:
        CALLS.append(("pack_forget", self, None))

    def place(self, **kwargs: Any) -> None:
        CALLS.append(("place", self, kwargs))

    def grid_propagate(self, flag: bool) -> None:
        pass

    def columnconfigure(self, index: Any, **kwargs: Any) -> None:
        pass

    def rowconfigure(self, index: Any, **kwargs: Any) -> None:
        pass

    # -- configuration ---------------------------------------------------- #
    def configure(self, **kwargs: Any) -> None:
        self._values.update(kwargs)

    config = configure

    def cget(self, key: str) -> Any:
        return self._values.get(key, self.kwargs.get(key))

    def __getitem__(self, key: str) -> Any:
        return self.cget(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.configure(**{key: value})

    # -- introspection ---------------------------------------------------- #
    def winfo_children(self) -> List["Widget"]:
        return list(self.children)

    def winfo_width(self) -> int:
        return self._width

    def winfo_height(self) -> int:
        return self._height

    def winfo_screenwidth(self) -> int:
        return 1920

    def winfo_screenheight(self) -> int:
        return 1080

    def winfo_exists(self) -> bool:
        return True

    # -- events ----------------------------------------------------------- #
    def bind(self, sequence: str, func: Any = None) -> None:
        CALLS.append(("bind", sequence, func))

    def protocol(self, name: str, func: Any = None) -> None:
        pass

    def event_generate(self, *args: Any, **kwargs: Any) -> None:
        pass

    def focus_set(self) -> None:
        pass

    def lift(self) -> None:
        pass

    def after(self, delay: int, func: Any = None, *args: Any) -> str:
        job = f"job{len(self._after_jobs)}"
        self._after_jobs.append((job, func, args))
        if func is not None:
            CALLS.append(("after", delay, func))
        return job

    def after_cancel(self, job: Any) -> None:
        pass

    def update(self) -> None:
        pass

    def update_idletasks(self) -> None:
        pass

    def destroy(self) -> None:
        CALLS.append(("destroy", self, None))

    def quit(self) -> None:
        pass

    def mainloop(self, *args: Any, **kwargs: Any) -> None:
        CALLS.append(("mainloop", self, None))

    def title(self, text: Optional[str] = None) -> None:
        self._values["title"] = text

    def geometry(self, text: Optional[str] = None) -> None:
        pass

    def minsize(self, *args: Any) -> None:
        pass

    def attributes(self, *args: Any, **kwargs: Any) -> None:
        pass

    def clipboard_clear(self) -> None:
        pass

    def clipboard_append(self, text: str) -> None:
        CALLS.append(("clipboard", text, None))


class Tk(Widget):
    pass


class Toplevel(Widget):
    pass


class Canvas(Widget):
    def create_text(self, *args: Any, **kwargs: Any) -> int:
        CALLS.append(("create_text", args, kwargs))
        return 1

    def create_line(self, *args: Any, **kwargs: Any) -> int:
        CALLS.append(("create_line", args, kwargs))
        return 2

    def coords(self, *args: Any, **kwargs: Any) -> None:
        pass

    def itemconfigure(self, item: Any, **kwargs: Any) -> None:
        pass

    def delete(self, *args: Any) -> None:
        pass


class Text(Widget):
    def __init__(self, master=None, **kwargs: Any):
        super().__init__(master, **kwargs)
        self._buffer: List[str] = []
        self._state = kwargs.get("state", "normal")

    def insert(self, index: Any, chars: Any, *args: Any) -> None:
        if str(self._state) == "disabled":
            raise TclError("text is disabled")
        self._buffer.append(str(chars))
        CALLS.append(("text_insert", chars, args))

    def delete(self, start: Any, end: Any = None) -> None:
        self._buffer.clear()

    def get(self, start: Any, end: Any = None) -> str:
        return "".join(self._buffer)

    def see(self, index: Any) -> None:
        pass

    def tag_configure(self, name: str, **kwargs: Any) -> None:
        pass

    def yview(self, *args: Any) -> None:
        pass

    def configure(self, **kwargs: Any) -> None:
        if "state" in kwargs:
            self._state = kwargs["state"]
        super().configure(**kwargs)

    config = configure


class Variable:
    def __init__(self, master=None, value: Any = None, name: Optional[str] = None):
        self._value = value

    def set(self, value: Any) -> None:
        self._value = value

    def get(self) -> Any:
        return self._value

    def trace_add(self, *args: Any, **kwargs: Any) -> None:
        pass


class StringVar(Variable):
    pass


class BooleanVar(Variable):
    def __init__(self, master=None, value: Any = False, name: Optional[str] = None):
        super().__init__(master, value)


class IntVar(Variable):
    def __init__(self, master=None, value: Any = 0, name: Optional[str] = None):
        super().__init__(master, value)


class DoubleVar(Variable):
    def __init__(self, master=None, value: Any = 0.0, name: Optional[str] = None):
        super().__init__(master, value)


class Style:
    def __init__(self, master=None):
        pass

    def theme_use(self, name: str) -> None:
        if name != "clam":
            raise TclError("unknown theme")

    def configure(self, style: str, **kwargs: Any) -> None:
        CALLS.append(("style_configure", style, kwargs))

    def map(self, style: str, **kwargs: Any) -> None:
        CALLS.append(("style_map", style, kwargs))

    def lookup(self, style: str, option: str) -> str:
        return ""


class Treeview(Widget):
    def __init__(self, master=None, **kwargs: Any):
        super().__init__(master, **kwargs)
        self._rows: Dict[str, Dict[str, Any]] = {}
        self._headings: Dict[str, Dict[str, Any]] = {}
        self._selected: List[str] = []

    def heading(self, column: str, **kwargs: Any) -> None:
        self._headings.setdefault(column, {}).update(kwargs)

    def column(self, column: str, **kwargs: Any) -> None:
        pass

    def insert(self, parent: str, index: Any, iid: Optional[str] = None, **kwargs: Any) -> str:
        iid = iid or f"row{len(self._rows)}"
        self._rows[iid] = dict(kwargs)
        return iid

    def delete(self, *items: Any) -> None:
        if not items:
            self._rows.clear()
            return
        for item in items:
            self._rows.pop(item, None)

    def get_children(self, item: str = "") -> Tuple[str, ...]:
        return tuple(self._rows)

    def item(self, item: str) -> Dict[str, Any]:
        return self._rows.get(item, {})

    def selection(self) -> Tuple[str, ...]:
        return tuple(self._selected)

    def selection_set(self, item: str) -> None:
        self._selected = [item]

    def tag_configure(self, name: str, **kwargs: Any) -> None:
        pass

    def yview(self, *args: Any) -> None:
        pass


class Combobox(Widget):
    def __init__(self, master=None, **kwargs: Any):
        super().__init__(master, **kwargs)
        self._index = -1

    def current(self, index: Optional[int] = None) -> Any:
        if index is None:
            return self._index
        self._index = index
        return None

    def set(self, value: str) -> None:
        self._values["value"] = value


class Progressbar(Widget):
    pass


class Scrollbar(Widget):
    def set(self, *args: Any) -> None:
        pass


class messagebox:  # noqa: N801 - mirrors the tkinter namespace
    @staticmethod
    def showinfo(title: str, message: str, **kwargs: Any) -> str:
        CALLS.append(("showinfo", title, message))
        return "ok"

    @staticmethod
    def showerror(title: str, message: str, **kwargs: Any) -> str:
        CALLS.append(("showerror", title, message))
        return "ok"

    @staticmethod
    def showwarning(title: str, message: str, **kwargs: Any) -> str:
        return "ok"


class filedialog:  # noqa: N801
    answers: Dict[str, Any] = {}

    @staticmethod
    def asksaveasfilename(**kwargs: Any) -> str:
        CALLS.append(("save_dialog", kwargs.get("title"), kwargs.get("initialfile")))
        return filedialog.answers.get("save", "")

    @staticmethod
    def askdirectory(**kwargs: Any) -> str:
        return filedialog.answers.get("dir", "")

    @staticmethod
    def askopenfilename(**kwargs: Any) -> str:
        return filedialog.answers.get("open", "")


def install() -> types.ModuleType:
    """Register the mock as ``tkinter``/``tkinter.ttk`` and return the module."""
    tkinter = types.ModuleType("tkinter")
    for name, obj in (
        ("Tk", Tk), ("Toplevel", Toplevel), ("Canvas", Canvas), ("Text", Text),
        ("StringVar", StringVar), ("BooleanVar", BooleanVar), ("IntVar", IntVar),
        ("DoubleVar", DoubleVar), ("Variable", Variable), ("TclError", TclError),
        ("Frame", Widget), ("Label", Widget), ("Button", Widget), ("Checkbutton", Widget),
        ("Radiobutton", Widget), ("Entry", Widget), ("Listbox", Widget), ("Menu", Widget),
        ("LabelFrame", Widget), ("PanedWindow", Widget), ("Spinbox", Widget), ("Scale", Widget),
        ("PhotoImage", Widget), ("NORMAL", "normal"), ("DISABLED", "disabled"),
        ("END", "end"), ("RIGHT", "right"), ("LEFT", "left"), ("CENTER", "center"),
        ("W", "w"), ("E", "e"), ("N", "n"), ("S", "s"), ("BOTH", "both"), ("X", "x"), ("Y", "y"),
    ):
        setattr(tkinter, name, obj)

    ttk = types.ModuleType("tkinter.ttk")
    for name, obj in (
        ("Frame", Widget), ("Label", Widget), ("Button", Widget), ("Checkbutton", Widget),
        ("LabelFrame", Widget), ("Combobox", Combobox), ("Progressbar", Progressbar),
        ("Scrollbar", Scrollbar), ("Treeview", Treeview), ("Style", Style),
        ("Notebook", Widget), ("Separator", Widget), ("Entry", Widget), ("PanedWindow", Widget),
        ("Radiobutton", Widget), ("Sizegrip", Widget),
    ):
        setattr(ttk, name, obj)

    filedialog_module = types.ModuleType("tkinter.filedialog")
    for name in ("asksaveasfilename", "askdirectory", "askopenfilename"):
        setattr(filedialog_module, name, getattr(filedialog, name))
    messagebox_module = types.ModuleType("tkinter.messagebox")
    for name in ("showinfo", "showerror", "showwarning", "askyesno", "askokcancel"):
        handler = getattr(messagebox, name, None) or (lambda *a, **k: "ok")
        setattr(messagebox_module, name, handler)

    tkinter.ttk = ttk  # type: ignore[attr-defined]
    tkinter.filedialog = filedialog_module  # type: ignore[attr-defined]
    tkinter.messagebox = messagebox_module  # type: ignore[attr-defined]

    sys.modules["tkinter"] = tkinter
    sys.modules["tkinter.ttk"] = ttk
    sys.modules["tkinter.filedialog"] = filedialog_module
    sys.modules["tkinter.messagebox"] = messagebox_module
    sys.modules["_tkinter"] = types.ModuleType("_tkinter")
    return tkinter
