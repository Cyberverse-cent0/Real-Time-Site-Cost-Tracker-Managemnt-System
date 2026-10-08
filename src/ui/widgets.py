# widgets.py
"""Token-driven shared widgets.

Every widget reads colors/fonts/spacing from ThemeEngine tokens at draw
time and registers as a listener, so a theme switch restyles them without
rebuilding the UI.
"""
import tkinter as tk
import tkinter.ttk as ttk

from ui.theme.engine import get_engine

TONES = ("primary", "success", "warning", "danger", "muted")


def _tone_color(tone: str, subtle: bool = False) -> tuple[str, str]:
    """Return (fill, text) colors for a semantic tone."""
    t = get_engine().tokens
    key = tone if tone in TONES else "primary"
    if key == "muted":
        return t["surface_hover"], t["text_muted"]
    fill = t[f"{key}_subtle"] if subtle else t[key]
    text = t["text"] if key == "primary" else t[key]
    if key == "primary":
        text = t["primary"]
    return fill, text


def round_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int,
               r: int, **kwargs) -> int:
    """Draw an approximation of a rounded rectangle (r=0 -> plain rect)."""
    r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    if r <= 1:
        return canvas.create_rectangle(x1, y1, x2, y2, kwargs)
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class Card(tk.Frame):
    """Surface panel with a token-colored 1px border."""

    def __init__(self, parent: tk.Widget, pad: tuple[int, int] | None = None, **kw):
        super().__init__(parent, **kw)
        if pad is None:
            pad = (get_engine().tokens["space"]["md"],) * 2
        self._pad = pad
        self.restyle()
        get_engine().add_listener(self, self.restyle)

    def restyle(self) -> None:
        t = get_engine().tokens
        pad = (t["space"]["md"],) * 2
        self._pad = pad
        self.configure(background=t["surface"], highlightthickness=1,
                       highlightbackground=t["border"], padx=pad[0], pady=pad[1])


class Bar(tk.Canvas):
    """Horizontal progress bar drawn on canvas with token-driven radius."""

    def __init__(self, parent: tk.Widget, fraction: float = 0.0, tone: str = "primary",
                 height: int | None = None, show_label: bool = False):
        t = get_engine().tokens
        self._height = height or max(8, t["space"]["md"])
        super().__init__(parent, height=self._height, highlightthickness=0, bd=0)
        self._fraction = max(0.0, min(1.0, fraction))
        self._tone = tone
        self._show_label = show_label
        self._draw()
        get_engine().add_listener(self, self._draw)
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, fraction: float, tone: str | None = None) -> None:
        self._fraction = max(0.0, min(1.0, fraction))
        if tone:
            self._tone = tone
        self._draw()

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        self._draw()

    def _tone_fill(self) -> str:
        t = get_engine().tokens
        key = self._tone if self._tone in TONES else "primary"
        return t[key] if key != "muted" else t["text_muted"]

    def _draw(self) -> None:
        t = get_engine().tokens
        self.configure(background=t["surface_hover"], height=self._height)
        self.delete("all")
        w = max(self.winfo_width(), 40)
        h = self._height
        r = min(t["radius"]["sm"], h // 2)
        round_rect(self, 1, 1, w - 1, h - 1, r, fill=t["surface_hover"], outline="")
        fill_w = int((w - 2) * self._fraction) + 1
        if fill_w > 2:
            round_rect(self, 1, 1, fill_w, h - 1, r, fill=self._tone_fill(), outline="")
        if self._show_label:
            pct = f"{int(round(self._fraction * 100))}%"
            self.create_text(w - 4, h / 2, anchor="e", text=pct,
                             fill=t["text"], font=t["fonts"]["caption_bold"])


class Badge(tk.Label):
    """Small tinted pill (status / category chip)."""

    def __init__(self, parent: tk.Widget, text: str, tone: str = "primary"):
        super().__init__(parent, text=text, padx=10, pady=2)
        self._tone = tone
        self.restyle()
        get_engine().add_listener(self, self.restyle)

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        self.restyle()

    def set_text(self, text: str) -> None:
        self.configure(text=text)

    def restyle(self) -> None:
        t = get_engine().tokens
        fill, fg = _tone_color(self._tone, subtle=True)
        self.configure(background=fill, foreground=fg, font=t["fonts"]["caption_bold"])


class StatCard(Card):
    """Metric card: caption title, big value, optional caption + progress bar."""

    def __init__(self, parent: tk.Widget, title: str, value: str = "—",
                 caption: str = "", fraction: float | None = None, tone: str = "primary"):
        super().__init__(parent)
        self._title_lbl = ttk.Label(self, text=title, style="Card.Caption.TLabel")
        self._title_lbl.pack(anchor="w")
        self._value_var = tk.StringVar(value=value)
        self._value_lbl = ttk.Label(self, textvariable=self._value_var, style="Card.H2.TLabel")
        self._value_lbl.pack(anchor="w", pady=(2, 0))
        self._caption_var = tk.StringVar(value=caption)
        self._caption_lbl = ttk.Label(self, textvariable=self._caption_var,
                                      style="Card.Caption.TLabel")
        self._caption_lbl.pack(anchor="w")
        self._fraction = fraction
        self._bar = Bar(self, fraction=fraction or 0.0, tone=tone)
        if fraction is not None:
            self._bar.pack(fill="x", expand=True, pady=(t_space("sm"), 0))

    def set(self, value: str, caption: str = "", fraction: float | None = None,
            tone: str | None = None) -> None:
        self._value_var.set(value)
        self._caption_var.set(caption)
        if fraction is not None:
            if self._fraction is None:
                self._bar.pack(fill="x", expand=True, pady=(t_space("sm"), 0))
            self._bar.set(fraction, tone)
        self._fraction = fraction


def t_space(key: str) -> int:
    return get_engine().tokens["space"].get(key, 8)


def section_header(parent: tk.Widget, title: str, caption: str = "") -> tk.Frame:
    """Page section heading with an optional muted sub-line."""
    row = tk.Frame(parent, background=get_engine().tokens["bg"])
    ttk.Label(row, text=title, style="H2.TLabel").pack(anchor="w")
    if caption:
        ttk.Label(row, text=caption, style="Caption.TLabel").pack(anchor="w")
    engine = get_engine()
    engine.add_listener(row, lambda: row.configure(background=engine.tokens["bg"]))
    return row
