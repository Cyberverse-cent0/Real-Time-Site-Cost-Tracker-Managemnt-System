# appearance.py
"""Quick Appearance popover — reachable from the top bar of any screen.

Mode + accent + density/radius/sidebar at a glance, with a jump into the
full Theme Studio. Every change applies live through the ThemeEngine.
"""
import tkinter as tk
import tkinter.ttk as ttk

from ui.theme.engine import get_engine
from ui.theme.presets import ACCENTS
from ui.theme.spec import DENSITIES, RADII, SIDEBARS, ThemeSpec

MODE_LABELS = [
    ("light", "Light"), ("dark", "Dark"), ("system", "System"),
    ("amoled", "AMOLED"), ("high_contrast", "High contrast"),
]
DENSITY_LABELS = {"compact": "Compact", "comfortable": "Comfortable", "spacious": "Spacious"}
RADIUS_LABELS = {"none": "None", "small": "Small", "medium": "Medium",
                 "rounded": "Rounded", "pill": "Pill"}
SIDEBAR_LABELS = {"expanded": "Expanded", "compact": "Compact", "hidden": "Hidden"}


class _Swatch(tk.Canvas):
    """Clickable accent dot with a selection ring."""

    def __init__(self, parent, hex_color: str, on_click, selected_fn, size: int = 26):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bd=0)
        self._color = hex_color
        self._size = size
        self._on_click = on_click
        self._selected_fn = selected_fn
        self._draw()
        get_engine().add_listener(self, self._draw)
        self.bind("<Button-1>", lambda e: on_click())
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))

    def _hover(self, on: bool) -> None:
        if get_engine().tokens["hover_animations"]:
            self.configure(cursor="hand2" if on else "")

    def _draw(self) -> None:
        t = get_engine().tokens
        s = self._size
        self.configure(background=t["bg"])
        self.delete("all")
        c = s // 2
        r = s // 2 - 6
        self.create_oval(c - r, c - r, c + r, c + r, fill=self._color, outline="")
        if self._selected_fn():
            ring = t["text"] if t["mode"] != "light" else t["text"]
            self.create_oval(c - r - 3, c - r - 3, c + r + 3, c + r + 3,
                             outline=ring, width=2)


class AppearancePanel(tk.Toplevel):
    def __init__(self, anchor: tk.Widget):
        super().__init__(anchor)
        self.overrideredirect(True)
        self.transient(anchor.winfo_toplevel())
        self._anchor = anchor
        engine = get_engine()
        t = engine.tokens

        outer = tk.Frame(self, background=t["border"])
        outer.pack(fill="both", expand=True)
        self._body = tk.Frame(outer, background=t["bg"],
                              padx=t["space"]["md"], pady=t["space"]["md"])
        self._body.pack(fill="both", expand=True, padx=1, pady=1)
        engine.add_listener(self, self._restyle)
        self.bind("<Escape>", lambda e: self._safe_destroy())
        self._anchor.bind("<Destroy>", lambda e: self._safe_destroy(), add="+")

        self._build()
        self._position()
        # Popover pattern: local grab redirects clicks; a click that lands
        # outside the panel bounds closes it.
        self.grab_set()
        self.bind("<Button-1>", self._on_click_outside, add="+")
        self.focus_set()
        self.lift()

    # ---- construction ----
    def _build(self) -> None:
        engine = get_engine()
        spec = engine.spec

        ttk.Label(self._body, text="Appearance", style="H3.TLabel").pack(anchor="w")

        # Mode
        self._section("Mode")
        mode_frame = tk.Frame(self._body, background=get_engine().tokens["bg"])
        mode_frame.pack(fill="x")
        self._mode_var = tk.StringVar(value=spec.mode if spec.mode in
                                      dict(MODE_LABELS) else "light")
        for i, (value, label) in enumerate(MODE_LABELS):
            rb = ttk.Radiobutton(mode_frame, text=label, value=value,
                                 variable=self._mode_var, command=self._apply)
            rb.grid(row=i // 3, column=i % 3, sticky="w",
                    padx=(0, get_engine().tokens["space"]["sm"]), pady=1)
        engine.add_listener(mode_frame,
                            lambda: mode_frame.configure(background=engine.tokens["bg"]))

        # Accent
        self._section("Accent")
        swatch_row = tk.Frame(self._body, background=get_engine().tokens["bg"])
        swatch_row.pack(fill="x")
        for name, (label, primary, _sec) in ACCENTS.items():
            _Swatch(swatch_row, primary,
                    on_click=lambda n=name: self._set_accent(n),
                    selected_fn=lambda n=name: self._is_accent_selected(n)
                    ).pack(side="left", padx=1)
        engine.add_listener(swatch_row,
                            lambda: swatch_row.configure(background=engine.tokens["bg"]))

        # Interface
        self._section("Interface")
        self._combo_row("Density", DENSITY_LABELS, spec.density, self._set_density)
        self._combo_row("Radius", RADIUS_LABELS, spec.radius, self._set_radius)
        self._combo_row("Sidebar", SIDEBAR_LABELS, spec.sidebar, self._set_sidebar)

        ttk.Button(self._body, text="Open Theme Studio", style="Accent.TButton",
                   command=self._open_studio).pack(fill="x", pady=(
                       get_engine().tokens["space"]["md"], 0))

    def _section(self, title: str) -> None:
        t = get_engine().tokens
        ttk.Label(self._body, text=title, style="Caption.TLabel").pack(
            anchor="w", pady=(t["space"]["sm"], 1))

    def _combo_row(self, label: str, labels: dict, current: str, setter) -> None:
        row = tk.Frame(self._body, background=get_engine().tokens["bg"])
        row.pack(fill="x", pady=1)
        ttk.Label(row, text=label).pack(side="left")
        combo = ttk.Combobox(row, state="readonly", width=14,
                             values=[labels[k] for k in labels])
        combo.set(labels.get(current, next(iter(labels.values()))))
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>",
                   lambda e, c=combo, labs=labels, s=setter:
                       s(_key_for(labs, c.get())))
        get_engine().add_listener(row, lambda: row.configure(
            background=get_engine().tokens["bg"]))

    # ---- change handlers ----
    def _apply(self) -> None:
        get_engine().apply(ThemeSpec(
            mode=self._mode_var.get(),
            accent=get_engine().spec.accent,
            custom_colors=get_engine().spec.custom_colors,
            density=get_engine().spec.density,
            radius=get_engine().spec.radius,
            sidebar=get_engine().spec.sidebar,
            animations=get_engine().spec.animations,
            font_family=get_engine().spec.font_family,
            font_scale=get_engine().spec.font_scale,
            high_contrast=get_engine().spec.high_contrast,
            reduce_motion=get_engine().spec.reduce_motion,
            larger_text=get_engine().spec.larger_text,
            focus_indicators=get_engine().spec.focus_indicators,
        ))

    def _mutate(self, **kw) -> None:
        data = get_engine().spec.to_dict()
        data.update(kw)
        get_engine().apply(ThemeSpec.from_dict(data))

    def _set_accent(self, name: str) -> None:
        self._mutate(accent=name, custom_colors={})  # named accent clears custom overrides

    def _set_density(self, value: str) -> None:
        self._mutate(density=value)

    def _set_radius(self, value: str) -> None:
        self._mutate(radius=value)

    def _set_sidebar(self, value: str) -> None:
        self._mutate(sidebar=value)

    def _is_accent_selected(self, name: str) -> bool:
        return get_engine().spec.accent == name

    def _open_studio(self) -> None:
        self._safe_destroy()
        from ui.theme.studio import open_theme_studio
        open_theme_studio()

    # ---- window management ----
    def _restyle(self) -> None:
        t = get_engine().tokens
        for outer_frame in (self,):
            outer_frame.configure(background=t["border"])
        self._body.configure(background=t["bg"])

    def _position(self) -> None:
        self.update_idletasks()
        x = self._anchor.winfo_rootx() + self._anchor.winfo_width() - self.winfo_width()
        y = self._anchor.winfo_rooty() + self._anchor.winfo_height() + 6
        screen_w = self.winfo_screenwidth()
        x = max(8, min(x, screen_w - self.winfo_width() - 8))
        self.geometry(f"+{x}+{y}")

    def _on_click_outside(self, event: tk.Event) -> None:
        if event.x < 0 or event.x >= self.winfo_width() or \
                event.y < 0 or event.y >= self.winfo_height():
            self._safe_destroy()

    def _safe_destroy(self) -> None:
        try:
            if self.winfo_exists():
                self.grab_release()
                self.destroy()
        except tk.TclError:
            pass


def _key_for(labels: dict, label: str) -> str:
    for k, v in labels.items():
        if v == label:
            return k
    return next(iter(labels))


def open_appearance_panel(anchor: tk.Widget) -> AppearancePanel:
    return AppearancePanel(anchor)
