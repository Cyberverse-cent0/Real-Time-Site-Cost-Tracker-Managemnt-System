# context_menu.py
"""Context-sensitive popup menus driven by the design-token engine.

A menu is described declaratively as a list of ``ContextItem`` specs and is
built fresh at popup time, so every popup uses the *current* theme tokens
(theme switches restyle popups with zero extra wiring) and the *current*
data state (items may be added/enabled/disabled conditionally by the
builder). Nothing persistent is created, so there are no listeners or
menus to clean up when views are rebuilt.

Quick start:
    from ui.context_menu import (
        ContextItem, separator, bind_context_menu, bind_treeview_context_menu,
        attach_entry_menu, copy_text,
    )

    # Any widget: builder is evaluated on every right-click.
    bind_context_menu(widget, lambda: [ContextItem("Refresh", refresh)])

    # Treeview: right-click first selects the row under the cursor.
    bind_treeview_context_menu(tree, lambda iid: row_menu(iid))

    # Entry fields: Cut/Copy/Paste/Select all (sensitive=True hides Cut/Copy).
    attach_entry_menu(entry)
    attach_entry_menu(password_entry, sensitive=True)
"""
import tkinter as tk
import tkinter.ttk as ttk
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

try:
    from ui.theme.engine import get_engine
except ImportError:  # pragma: no cover - flat sys.path layout (src/ on path)
    from theme.engine import get_engine


# ----------------------------------------------------------------------
# Item specification
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ContextItem:
    """One entry in a context menu.

    kind:       command | checkbutton | radiobutton | separator | submenu | header
    tone:       normal | danger (danger renders the label in the danger color)
    glyph:      short unicode prefix shown before the label ("" for none)
    accelerator: shortcut hint displayed next to the label (display only)
    variable/value/onvalue/offvalue: check/radio binding
    items:      submenu entries (kind="submenu")
    """
    label: str = ""
    command: Optional[Callable[[], None]] = None
    kind: str = "command"
    accelerator: str = ""
    glyph: str = ""
    tone: str = "normal"
    state: str = "normal"          # normal | disabled
    variable: Optional[tk.Variable] = None
    value: object = None           # radiobutton value
    onvalue: object = True         # checkbutton checked value
    offvalue: object = False       # checkbutton unchecked value
    items: tuple["ContextItem", ...] = field(default_factory=tuple)


def separator() -> ContextItem:
    """A separator line."""
    return ContextItem(kind="separator")


def header(label: str) -> ContextItem:
    """A disabled caption line used as a section title inside the menu."""
    return ContextItem(kind="header", label=label)


# ----------------------------------------------------------------------
# Token access
# ----------------------------------------------------------------------

_FALLBACK_TOKENS = {
    "surface": "#ffffff", "surface_hover": "#f1f5f9", "bg": "#f8fafc",
    "text": "#0f172a", "text_muted": "#64748b", "border": "#e2e8f0",
    "danger": "#ef4444", "primary": "#0ea5e9",
    "fonts": {
        "body": ("Helvetica", 10),
        "caption_bold": ("Helvetica", 9, "bold"),
    },
}


def _tokens() -> dict:
    """Current design tokens (with a graceful fallback before engine init)."""
    try:
        return get_engine().tokens
    except RuntimeError:
        return _FALLBACK_TOKENS


def _label_of(item: ContextItem) -> str:
    return f"{item.glyph}  {item.label}" if item.glyph else item.label


# ----------------------------------------------------------------------
# Menu construction
# ----------------------------------------------------------------------

def build_menu(parent: tk.Widget, items: Sequence[ContextItem]) -> tk.Menu:
    """Build a token-styled tk.Menu from ContextItem specs."""
    t = _tokens()
    menu = tk.Menu(
        parent,
        tearoff=False,
        background=t["surface"],
        foreground=t["text"],
        activebackground=t["surface_hover"],
        activeforeground=t["text"],
        disabledforeground=t["text_muted"],
        selectcolor=t["surface"],
        borderwidth=1,
        relief="solid",
        font=t["fonts"]["body"],
    )
    for item in items or ():
        _add_item(menu, item, t)
    return menu


def _add_item(menu: tk.Menu, item: ContextItem, t: dict) -> None:
    kind = item.kind

    if kind == "separator":
        menu.add_separator()
        return

    label = _label_of(item)
    fg = t["danger"] if item.tone == "danger" else t["text"]
    state = item.state if item.state in ("normal", "disabled") else "normal"
    font = t["fonts"]["caption_bold"] if kind == "header" else t["fonts"]["body"]

    if kind == "header":
        menu.add_command(label=label, state="disabled", font=font)
        return

    base = {"label": label, "state": state, "font": font}
    if item.accelerator:
        base["accelerator"] = item.accelerator

    if kind == "command":
        menu.add_command(command=item.command, foreground=fg, **base)
    elif kind == "checkbutton":
        menu.add_checkbutton(variable=item.variable, onvalue=item.onvalue,
                             offvalue=item.offvalue, command=item.command,
                             foreground=fg, **base)
    elif kind == "radiobutton":
        menu.add_radiobutton(variable=item.variable, value=item.value,
                             command=item.command, foreground=fg, **base)
    elif kind == "submenu":
        menu.add_cascade(menu=build_menu(menu, item.items), **base)


def popup_context_menu(widget: tk.Widget, items: Optional[Sequence[ContextItem]],
                       event: tk.Event | None = None, *, x: int = 0, y: int = 0) -> bool:
    """Build and show a context menu for ``items``.

    Position is the pointer (``event``) or a widget-relative ``x``/``y``.
    Returns True when a menu was shown (empty builders pop up nothing).
    """
    if not items:
        return False
    menu = build_menu(widget, items)
    if event is not None:
        pos_x, pos_y = event.x_root, event.y_root
    else:
        pos_x = widget.winfo_rootx() + x
        pos_y = widget.winfo_rooty() + y
    try:
        menu.tk_popup(pos_x, pos_y)
    finally:
        menu.grab_release()
    return True


# ----------------------------------------------------------------------
# Bindings
# ----------------------------------------------------------------------

_POPUP_SEQUENCES = ("<Button-3>", "<Button-2>")  # right-click (+ Button-2 platforms)


def bind_context_menu(widget: tk.Widget, builder: Callable[[], Optional[Sequence[ContextItem]]]) -> None:
    """Bind a context menu to ``widget`` for right-click.

    ``builder`` runs on every popup so the menu always reflects the current
    theme and data. If it returns None/empty, nothing pops up. Builder
    exceptions are swallowed so a broken handler never crashes the popup.
    """
    def handler(event: tk.Event) -> str:
        try:
            items = builder()
        except Exception:
            items = None
        if items:
            popup_context_menu(widget, items, event)
        return "break"

    for seq in _POPUP_SEQUENCES:
        widget.bind(seq, handler)


def bind_context_menu_all(widget: tk.Widget,
                          builder: Callable[[], Optional[Sequence[ContextItem]]],
                          *, skip_buttons: bool = True) -> None:
    """Recursively bind a context menu to ``widget`` and its children.

    ttk widgets are skipped (they usually need their own row-aware handler,
    see ``bind_treeview_context_menu``), as are Buttons when
    ``skip_buttons`` is set and Entry fields always are (use
    ``attach_entry_menu`` for those).
    """
    for target in (widget, *widget.winfo_children()):
        if isinstance(target, (ttk.Widget, tk.Entry)):
            continue
        if skip_buttons and isinstance(target, tk.Button):
            continue
        bind_context_menu(target, builder)
        bind_context_menu_all(target, builder, skip_buttons=skip_buttons)


def bind_treeview_context_menu(tree: ttk.Treeview,
                               builder: Callable[[Optional[str]], Optional[Sequence[ContextItem]]]) -> None:
    """Bind a row-aware context menu to a Treeview.

    The row under the pointer is selected first, then ``builder(iid)`` (iid
    is None when the empty area below the rows was clicked) produces the
    items, so the menu contents are row-sensitive.
    """
    def handler(event: tk.Event) -> str:
        iid = tree.identify_row(event.y)
        if iid:
            tree.selection_set(iid)
            tree.focus(iid)
        else:
            tree.selection_remove(*tree.selection())
        try:
            items = builder(iid)
        except Exception:
            items = None
        if items:
            popup_context_menu(tree, items, event)
        return "break"

    for seq in _POPUP_SEQUENCES:
        tree.bind(seq, handler)


# ----------------------------------------------------------------------
# Entry-field edit menu
# ----------------------------------------------------------------------

def copy_text(widget: tk.Widget, text: object) -> None:
    """Copy ``text`` to the system clipboard."""
    widget.clipboard_clear()
    widget.clipboard_append(str(text))


def _entry_state(entry: tk.Entry) -> dict:
    editable = str(entry.cget("state")) != "disabled"
    try:
        has_selection = bool(entry.selection_present())
    except Exception:
        has_selection = False
    try:
        has_clipboard = bool(entry.clipboard_get())
    except Exception:
        has_clipboard = False
    return {"editable": editable, "selection": has_selection, "clipboard": has_clipboard}


def _select_all(entry: tk.Entry) -> None:
    entry.focus_set()
    entry.selection_range(0, "end")
    entry.icursor("end")


def attach_entry_menu(entry: tk.Entry, *, sensitive: bool = False,
                      extra_items: Sequence[ContextItem] = ()) -> None:
    """Attach the standard edit menu (Cut/Copy/Paste/Select all) to an Entry.

    ``sensitive=True`` (password fields) omits Cut/Copy so hidden text is
    never exposed; Paste/Select all/Clear remain available. Bound on
    right-click only, so X11 middle-click paste keeps working.
    """
    def handler(event: tk.Event) -> str:
        st = _entry_state(entry)
        items: list[ContextItem] = []

        if not sensitive:
            items.append(ContextItem(
                "Cut", lambda: entry.event_generate("<<Cut>>"),
                accelerator="Ctrl+X", glyph="✂",
                state="normal" if st["editable"] and st["selection"] else "disabled"))
            items.append(ContextItem(
                "Copy", lambda: entry.event_generate("<<Copy>>"),
                accelerator="Ctrl+C", glyph="⧉",
                state="normal" if st["selection"] else "disabled"))
        items.append(ContextItem(
            "Paste", lambda: entry.event_generate("<<Paste>>"),
            accelerator="Ctrl+V", glyph="📋",
            state="normal" if st["editable"] and st["clipboard"] else "disabled"))
        items.extend(extra_items)
        items.append(separator())
        items.append(ContextItem(
            "Select all", lambda: _select_all(entry), glyph="▤",
            state="normal" if st["editable"] else "disabled"))
        if st["editable"]:
            items.append(ContextItem("Clear", lambda: entry.delete(0, "end")))

        popup_context_menu(entry, items, event)
        return "break"

    entry.bind("<Button-3>", handler)
