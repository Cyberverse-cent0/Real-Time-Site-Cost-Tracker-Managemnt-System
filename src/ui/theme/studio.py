# studio.py
"""Theme Studio — full personalization surface.

Sections: Theme (presets + modes), Colors, Interface, Typography,
Accessibility — with a live preview pane. Every control mutates a working
ThemeSpec that is applied through the ThemeEngine immediately, so the whole
application is the preview. Themes can be exported/imported as JSON files.
"""
import json
import tkinter as tk
import tkinter.colorchooser as colorchooser
import tkinter.font as tkfont
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox

from ui.theme.engine import get_engine
from ui.theme.presets import ACCENTS, NAMED_PRESETS, resolve_accent
from ui.theme.spec import (ANIMATIONS, CUSTOM_COLOR_KEYS, DENSITIES, FONT_SCALES,
                           MODES, RADII, SIDEBARS, ThemeSpec)
from ui.theme.tokens import build_tokens
from ui.widgets import Bar, Badge, Card

ANIMATION_LABELS = {"full": "Full", "reduced": "Reduced", "none": "None"}
SCALE_LABELS = {"small": "Small", "medium": "Medium", "large": "Large"}
MODE_LABELS = {"light": "Light", "dark": "Dark", "system": "System",
               "amoled": "AMOLED", "high_contrast": "High contrast", "custom": "Custom"}
COLOR_LABELS = {
    "primary": "Primary", "secondary": "Secondary", "bg": "Background",
    "surface": "Surface", "surface_hover": "Surface hover", "text": "Text",
    "text_muted": "Muted text", "border": "Border",
    "success": "Success", "warning": "Warning", "danger": "Danger",
}

SECTIONS = [("theme", "Theme"), ("colors", "Colors"), ("interface", "Interface"),
            ("typography", "Typography"), ("accessibility", "Accessibility")]

_active_studio: "ThemeStudio | None" = None


class ThemeStudio(tk.Toplevel):
    def __init__(self, root: tk.Misc):
        super().__init__(root)
        self.title("Theme Studio")
        self.transient(root)
        self.geometry("860x600")
        self.minsize(780, 540)

        self.working: ThemeSpec = get_engine().spec.clamped()
        self._section = "theme"
        self._widgets: dict[str, tk.Widget] = {}

        self._build()
        get_engine().add_listener(self, lambda: self._restyle_chrome())
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda e: self._close())

    # ================= layout =================
    def _build(self) -> None:
        t = get_engine().tokens
        self._header = tk.Frame(self, background=t["bg"])
        self._header.pack(fill="x", padx=t["space"]["md"], pady=(t["space"]["sm"], 0))
        ttk.Label(self._header, text="Theme Studio", style="H1.TLabel").pack(side="left")
        ttk.Label(self._header, text="  Changes apply live",
                  style="Caption.TLabel").pack(side="left", pady=(10, 0))

        main = tk.Frame(self, background=t["bg"])
        main.pack(fill="both", expand=True, padx=t["space"]["md"], pady=t["space"]["sm"])
        self._main = main

        # left nav
        self._nav = tk.Frame(main, background=t["bg"])
        self._nav.pack(side="left", fill="y", padx=(0, t["space"]["md"]))
        self._nav_buttons: dict[str, ttk.Button] = {}
        for key, label in SECTIONS:
            btn = ttk.Button(self._nav, text=label,
                             style="Accent.TButton" if key == self._section else "Ghost.TButton",
                             width=16, command=lambda k=key: self._show_section(k))
            btn.pack(fill="x", pady=2)
            self._nav_buttons[key] = btn

        # right: controls + preview
        right = tk.Frame(main, background=t["bg"])
        right.pack(side="left", fill="both", expand=True)
        self._content = tk.Frame(right, background=t["bg"])
        self._content.pack(fill="both", expand=True)

        ttk.Label(right, text="Live preview", style="Caption.TLabel").pack(anchor="w")
        self._preview_host = tk.Frame(right, background=t["bg"])
        self._preview_host.pack(fill="x", pady=(2, 0))
        get_engine().add_listener(self._preview_host, self._build_preview)

        # footer
        self._footer = tk.Frame(self, background=t["bg"])
        self._footer.pack(fill="x", padx=t["space"]["md"], pady=(0, t["space"]["md"]))
        ttk.Button(self._footer, text="Import…", command=self._import).pack(side="left")
        ttk.Button(self._footer, text="Export…", command=self._export).pack(side="left",
                                                                            padx=(8, 0))
        ttk.Button(self._footer, text="Reset to defaults",
                   command=self._reset).pack(side="left", padx=(8, 0))
        ttk.Button(self._footer, text="Done", style="Accent.TButton",
                   command=self._close).pack(side="right")

        self._show_section("theme")
        self._build_preview()

    # ================= sections =================
    def _show_section(self, key: str) -> None:
        self._section = key
        for w in self._content.winfo_children():
            w.destroy()
        for k, btn in self._nav_buttons.items():
            btn.configure(style="Accent.TButton" if k == key else "Ghost.TButton")
        builder = getattr(self, f"_section_{key}")
        builder()

    def _section_theme(self) -> None:
        t = get_engine().tokens
        self._label("Presets")
        chip_row = tk.Frame(self._content, background=t["bg"])
        chip_row.pack(fill="x", pady=(0, t["space"]["sm"]))
        for key, (label, kw) in NAMED_PRESETS.items():
            ttk.Button(chip_row, text=label, style="Secondary.TButton",
                       command=lambda k=key: self._apply_preset(k)).pack(
                side="left", padx=(0, 6))

        self._label("Mode")
        frame = tk.Frame(self._content, background=t["bg"])
        frame.pack(fill="x")
        var = tk.StringVar(value=self.working.mode)
        for value, label in MODE_LABELS.items():
            if value == "custom":
                continue  # custom is reached by editing colors
            ttk.Radiobutton(frame, text=label, value=value, variable=var,
                            command=lambda: self._mutate(mode=var.get())).pack(
                side="left", padx=(0, t["space"]["md"]))

    def _section_colors(self) -> None:
        t = get_engine().tokens
        self._label("Accent presets")
        row = tk.Frame(self._content, background=t["bg"])
        row.pack(fill="x", pady=(0, t["space"]["sm"]))
        for name, (label, primary, _sec) in ACCENTS.items():
            active = self.working.accent == name
            hex_now = resolve_accent(self.working.accent)[0]
            chip = tk.Canvas(row, width=34, height=34, highlightthickness=0, bd=0,
                             background=t["bg"], cursor="hand2")
            c = 17
            chip.create_oval(c - 12, c - 12, c + 12, c + 12, fill=primary, outline="")
            if active or (self.working.accent.startswith("#") and hex_now == primary):
                chip.create_oval(c - 15, c - 15, c + 15, c + 15,
                                 outline=t["text"], width=2)
            chip.create_text(c, 40, text=label, fill=t["text_muted"],
                             font=t["fonts"]["caption"])
            chip.configure(height=52)
            chip.bind("<Button-1>", lambda e, n=name: self._mutate(accent=n,
                                                                   custom_colors={}))
            chip.pack(side="left", padx=(0, 10))

        self._label("Custom colors", "Edits switch the theme to Custom mode "
                                     "and keep your current palette as a base")
        grid = tk.Frame(self._content, background=t["bg"])
        grid.pack(fill="x")
        resolved = self._resolved_palette()
        for i, key in enumerate(("primary", "secondary", "bg", "surface", "text",
                                 "border", "success", "warning", "danger")):
            color = self.working.custom_colors.get(key) or resolved.get(key, "#000000")
            ttk.Button(grid, text=f"{COLOR_LABELS[key]}  {color}",
                       style="Secondary.TButton", width=24,
                       command=lambda k=key: self._pick_custom(k)).grid(
                row=i // 3, column=i % 3, padx=(0, 8), pady=3, sticky="ew")
        grid.columnconfigure((0, 1, 2), weight=1)

    def _section_interface(self) -> None:
        self._combo("Border radius", dict(zip(RADII, RADII)), self.working.radius,
                    lambda v: self._mutate(radius=v))
        self._combo("UI density", dict(zip(DENSITIES, DENSITIES)), self.working.density,
                    lambda v: self._mutate(density=v))
        self._combo("Sidebar", dict(zip(SIDEBARS, SIDEBARS)), self.working.sidebar,
                    lambda v: self._mutate(sidebar=v))
        self._label("Animations")
        frame = tk.Frame(self._content, background=get_engine().tokens["bg"])
        frame.pack(fill="x")
        var = tk.StringVar(value=self.working.animations)
        for value in ANIMATIONS:
            ttk.Radiobutton(frame, text=ANIMATION_LABELS[value], value=value,
                            variable=var,
                            command=lambda: self._mutate(animations=var.get())).pack(
                side="left", padx=(0, get_engine().tokens["space"]["md"]))

    def _section_typography(self) -> None:
        families = ["System default"] + sorted(set(tkfont.families(self)))
        current = self.working.font_family or "System default"
        self._combo("Font family", {f: f for f in families}, current,
                    lambda v: self._mutate(font_family="" if v == "System default" else v))
        self._label("Font size")
        frame = tk.Frame(self._content, background=get_engine().tokens["bg"])
        frame.pack(fill="x")
        var = tk.StringVar(value=self.working.font_scale)
        for value in FONT_SCALES:
            ttk.Radiobutton(frame, text=SCALE_LABELS[value], value=value, variable=var,
                            command=lambda: self._mutate(font_scale=var.get())).pack(
                side="left", padx=(0, get_engine().tokens["space"]["md"]))

    def _section_accessibility(self) -> None:
        checks = [
            ("High contrast", "high_contrast"),
            ("Reduce motion", "reduce_motion"),
            ("Larger text", "larger_text"),
            ("Focus indicators", "focus_indicators"),
        ]
        for label, field in checks:
            var = tk.BooleanVar(value=getattr(self.working, field))
            def toggle(_field=field, _var=var):
                self._mutate(**{_field: _var.get()})
            ttk.Checkbutton(self._content, text=label, variable=var,
                            command=toggle).pack(anchor="w", pady=2)

    # ================= section helpers =================
    def _label(self, text: str, caption: str = "") -> None:
        t = get_engine().tokens
        ttk.Label(self._content, text=text, style="H3.TLabel").pack(anchor="w",
                                                                    pady=(4, 0))
        if caption:
            ttk.Label(self._content, text=caption, style="Caption.TLabel",
                      wraplength=520, justify="left").pack(anchor="w")

    def _combo(self, label: str, options: dict[str, str], current: str, setter) -> None:
        row = tk.Frame(self._content, background=get_engine().tokens["bg"])
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label).pack(side="left")
        combo = ttk.Combobox(row, state="readonly", width=22,
                             values=list(options.values()))
        combo.set(options.get(current, next(iter(options.values()))))
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>",
                   lambda e: setter(_key_of(options, combo.get())))

    # ================= live preview =================
    def _build_preview(self) -> None:
        for w in self._preview_host.winfo_children():
            w.destroy()
        t = get_engine().tokens
        card = Card(self._preview_host)
        card.pack(fill="x")
        inner = tk.Frame(card, background=t["surface"])
        inner.pack(fill="x")

        top = tk.Frame(inner, background=t["surface"])
        top.pack(fill="x")
        ttk.Label(top, text="Riverside Offices — Phase 2", style="Card.H3.TLabel").pack(
            side="left")
        Badge(top, "On budget", "success").pack(side="right")

        ttk.Label(inner, text="Budget used across labor, materials and equipment.",
                  style="Card.Muted.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Label(inner, text="$128,400 / $180,000", style="Card.H2.TLabel").pack(
            anchor="w", pady=(2, 0))
        Bar(inner, fraction=0.71, tone="primary", show_label=True).pack(
            fill="x", expand=True, pady=(6, 6))
        btns = tk.Frame(inner, background=t["surface"])
        btns.pack(fill="x")
        ttk.Button(btns, text="Log expense", style="Accent.TButton").pack(side="left")
        ttk.Button(btns, text="View report", style="Card.TButton").pack(
            side="left", padx=(8, 0))

    # ================= actions =================
    def _mutate(self, **kw) -> None:
        data = self.working.to_dict()
        data.update(kw)
        self.working = ThemeSpec.from_dict(data)
        get_engine().apply(self.working)
        if self._section in ("theme", "colors", "interface", "typography",
                             "accessibility"):
            self._show_section(self._section)  # refresh controls (selections moved)

    def _apply_preset(self, key: str) -> None:
        _label, kw = NAMED_PRESETS[key]
        data = self.working.to_dict()
        data.update(kw)
        self.working = ThemeSpec.from_dict(data)
        get_engine().apply(self.working)
        self._show_section("theme")

    def _resolved_palette(self) -> dict[str, str]:
        """Current effective colors — the base when entering Custom mode."""
        t = get_engine().tokens
        keys = ("primary", "secondary", "bg", "surface", "surface_hover", "text",
                "text_muted", "border", "success", "warning", "danger")
        return {k: t[k] for k in keys if k in t}

    def _pick_custom(self, key: str) -> None:
        resolved = self._resolved_palette()
        current = self.working.custom_colors.get(key) or resolved.get(key, "#FFFFFF")
        rgb, hexval = colorchooser.askcolor(color=current, parent=self,
                                            title=f"Pick {COLOR_LABELS[key]}")
        if not hexval:
            return
        custom = dict(self.working.custom_colors)
        if key in ("primary", "secondary"):
            # Accent edits live in the accent slot; palette edits force custom mode.
            base = resolved if self.working.mode != "custom" else custom
            custom = {k: v for k, v in base.items() if k in CUSTOM_COLOR_KEYS}
            custom[key] = hexval
            data = self.working.to_dict()
            data.update(mode="custom", custom_colors=custom)
            if key == "primary":
                data["accent"] = hexval
            self.working = ThemeSpec.from_dict(data)
        else:
            if self.working.mode != "custom":
                custom = {k: v for k, v in resolved.items() if k in CUSTOM_COLOR_KEYS}
            custom[key] = hexval
            data = self.working.to_dict()
            data.update(mode="custom", custom_colors=custom)
            self.working = ThemeSpec.from_dict(data)
        get_engine().apply(self.working)
        self._show_section("colors")

    def _reset(self) -> None:
        self.working = ThemeSpec()
        get_engine().apply(self.working)
        self._show_section(self._section)

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".json",
            filetypes=[("Theme files", "*.json"), ("All files", "*.*")],
            initialfile="my-theme.json", title="Export theme")
        if not path:
            return
        engine = get_engine()
        name = "My Theme"
        if engine.store.export_theme(path, self.working, name):
            messagebox.showinfo("Export", f"Theme exported to\n{path}", parent=self)
        else:
            messagebox.showerror("Export", "Could not write the theme file.", parent=self)

    def _import(self) -> None:
        path = filedialog.askopenfilename(
            parent=self, filetypes=[("Theme files", "*.json"), ("All files", "*.*")],
            title="Import theme")
        if not path:
            return
        engine = get_engine()
        name, spec = engine.store.import_theme(path)
        if spec is None:
            messagebox.showerror("Import", "That file is not a valid theme.", parent=self)
            return
        self.working = spec
        engine.apply(self.working)
        self._show_section(self._section)
        messagebox.showinfo("Import", f'Theme "{name}" applied.', parent=self)

    def _restyle_chrome(self) -> None:
        t = get_engine().tokens
        for frame in (self._header, self._main, self._nav, self._content,
                      self._footer, self._preview_host):
            try:
                frame.configure(background=t["bg"])
            except tk.TclError:
                pass

    def _close(self) -> None:
        global _active_studio
        _active_studio = None
        self.destroy()


def _key_of(options: dict[str, str], label: str) -> str:
    for k, v in options.items():
        if v == label:
            return k
    return next(iter(options))


def open_theme_studio() -> ThemeStudio:
    global _active_studio
    if _active_studio is not None and _active_studio.winfo_exists():
        _active_studio.lift()
        _active_studio.focus_set()
        return _active_studio
    engine = get_engine()
    _active_studio = ThemeStudio(engine.root)
    return _active_studio
