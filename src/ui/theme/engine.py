# engine.py
"""ThemeEngine — compiles ThemeSpec into DesignTokens and applies them live.

Application flow:  Login -> load user prefs -> ThemeSpec -> DesignTokens
                   -> ttk styles + option database + global fonts
                   -> listener callbacks restyle custom widgets.

Changing the theme is therefore "swap the variables", never "rewrite the
components": every widget reads semantic tokens at (re)draw time.
"""
import os
import subprocess
import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk

from . import color as C
from .spec import ThemeSpec
from .tokens import build_tokens
from .store import AppearanceStore

_SYSTEM_WATCH_MS = 20_000  # re-check OS dark mode every 20 s


def detect_system_dark() -> bool:
    """Best-effort OS dark-mode detection (GNOME gsettings, then GTK config)."""
    try:
        out = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, timeout=2,
        )
        scheme = (out.stdout or "").strip().strip("'\"")
        if "dark" in scheme.lower():
            return True
        if "light" in scheme.lower():
            return False
    except (OSError, subprocess.SubprocessError):
        pass

    ini = os.path.expanduser("~/.config/gtk-3.0/settings.ini")
    try:
        with open(ini, "r", encoding="utf-8") as fh:
            for line in fh:
                if "prefer-dark" in line and "true" in line.lower():
                    return True
    except OSError:
        pass
    return False


class ThemeEngine:
    def __init__(self, root: tk.Tk, store: AppearanceStore | None = None):
        self.root = root
        self.store = store or AppearanceStore()
        self.spec = ThemeSpec()
        self.tokens: dict = {}
        self._listeners: list[tuple[tk.Misc, callable]] = []
        self._persistence_callback: callable | None = None
        self._system_dark = detect_system_dark()
        self._watch_job: str | None = None

        self.style = ttk.Style(root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:  # pragma: no cover - unusual builds
            pass
        self._base_font_family = tkfont.nametofont("TkDefaultFont").actual("family")

    def set_persistence_callback(self, callback: callable) -> None:
        """Route theme persistence to the app's preference store.

        When set, apply(spec, persist=True) calls callback(spec) instead of
        writing to the DB store — used by the app bridge so theme edits made
        anywhere (Studio, quick panel) land in the user's JSON preferences.
        """
        self._persistence_callback = callback

    # ---- lifecycle ----
    def boot(self, spec: ThemeSpec | None = None) -> None:
        """Initial apply before the mainloop (no persistence)."""
        self.apply(spec or ThemeSpec(), persist=False)

    def apply(self, spec: ThemeSpec, persist: bool = True) -> None:
        """Compile + apply a new ThemeSpec everywhere, right now."""
        self.spec = spec.clamped()
        self._system_dark = detect_system_dark()
        self.tokens = build_tokens(
            self.spec,
            system_prefers_dark=self._system_dark,
            default_font_family=self._base_font_family,
        )
        self._apply_global_fonts()
        self._apply_option_db()
        self._apply_ttk_styles()
        self.root.configure(background=self.tokens["bg"])
        self._notify()
        self._schedule_system_watch()
        if persist:
            if self._persistence_callback is not None:
                self._persistence_callback(self.spec)
            elif self.store.current_user:
                self.store.save(self.store.current_user, self.spec)

    # ---- per-user profiles ----
    def set_current_user(self, username: str | None) -> None:
        """Track the logged-in user (theme loading is done by the app bridge)."""
        self.store.set_current_user(username)

    # ---- listeners (custom-drawn widgets restyle themselves) ----
    def add_listener(self, widget: tk.Misc, callback: callable) -> None:
        self._listeners.append((widget, callback))

    def remove_listener(self, widget: tk.Misc) -> None:
        self._listeners = [(w, cb) for w, cb in self._listeners if w is not widget]

    def _notify(self) -> None:
        alive = []
        for widget, cb in self._listeners:
            try:
                if widget.winfo_exists():
                    cb()
                    alive.append((widget, cb))
            except tk.TclError:
                pass  # widget died -> drop its listener
        self._listeners = alive

    # ---- system theme watching ----
    def _schedule_system_watch(self) -> None:
        if self._watch_job:
            try:
                self.root.after_cancel(self._watch_job)
            except tk.TclError:
                pass
            self._watch_job = None
        if self.spec.mode != "system":
            return

        def check():
            dark = detect_system_dark()
            if dark != self._system_dark:
                self._system_dark = dark
                self.tokens = build_tokens(
                    self.spec, system_prefers_dark=dark,
                    default_font_family=self._base_font_family,
                )
                self._apply_global_fonts()
                self._apply_option_db()
                self._apply_ttk_styles()
                self.root.configure(background=self.tokens["bg"])
                self._notify()
            self._schedule_system_watch()

        self._watch_job = self.root.after(_SYSTEM_WATCH_MS, check)

    # ---- application internals ----
    def _apply_global_fonts(self) -> None:
        t, fonts = self.tokens, self.tokens["fonts"]
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkTooltipFont"):
            try:
                tkfont.nametofont(name).configure(
                    family=fonts["family"], size=fonts["body"][1])
            except tk.TclError:
                pass

    def _apply_option_db(self) -> None:
        """Theme classic tk widgets (used inside canvas-heavy components)."""
        t = self.tokens
        opt = self.root.option_add
        opt("*Background", t["bg"])
        opt("*Foreground", t["text"])
        opt("*Button.background", t["surface"])
        opt("*Button.foreground", t["text"])
        opt("*Button.relief", "flat")
        opt("*Label.background", t["bg"])
        opt("*Label.foreground", t["text"])
        opt("*Checkbutton.background", t["bg"])
        opt("*Checkbutton.foreground", t["text"])
        opt("*Entry.background", t["surface"])
        opt("*Entry.foreground", t["text"])
        opt("*Entry.insertBackground", t["text"])
        opt("*TCombobox*Listbox.background", t["surface"])
        opt("*TCombobox*Listbox.foreground", t["text"])
        opt("*TCombobox*Listbox.selectBackground", t["primary_subtle"])
        opt("*TCombobox*Listbox.selectForeground", t["text"])

    def _apply_ttk_styles(self) -> None:
        t = self.tokens
        s = self.style
        f = t["fonts"]
        pad = (t["space"]["sm"], t["space"]["xs"] + 2)

        s.configure(".", background=t["bg"], foreground=t["text"],
                    bordercolor=t["border"], lightcolor=t["bg"], darkcolor=t["bg"],
                    troughcolor=t["surface_hover"], font=f["body"],
                    focuscolor=t["primary"])

        s.configure("TFrame", background=t["bg"])
        s.configure("TLabel", background=t["bg"], foreground=t["text"])
        s.configure("Muted.TLabel", foreground=t["text_muted"])
        s.configure("Caption.TLabel", font=f["caption"], foreground=t["text_muted"])
        s.configure("H3.TLabel", font=f["h3"])
        s.configure("H2.TLabel", font=f["h2"])
        s.configure("H1.TLabel", font=f["h1"])
        s.configure("Inverse.TLabel", background=t["primary"],
                    foreground=t["primary_contrast"], font=f["body_bold"])

        s.configure("TLabelframe", background=t["bg"], bordercolor=t["border"],
                    relief="solid", borderwidth=1)
        s.configure("TLabelframe.Label", background=t["bg"],
                    foreground=t["text_muted"], font=f["caption_bold"])

        s.configure("TButton", background=t["surface"], foreground=t["text"],
                    bordercolor=t["border"], lightcolor=t["surface"],
                    darkcolor=t["surface"], relief="flat", padding=pad,
                    focuscolor=t["primary"], font=f["body"])
        s.map("TButton",
              background=[("disabled", t["surface"]),
                          ("pressed !disabled", t["surface_hover"]),
                          ("active !disabled", t["surface_hover"])],
              foreground=[("disabled", t["text_muted"])],
              focuscolor=[("focus", t["primary"] if t["focus_indicators"] else t["surface"])])

        s.configure("Accent.TButton", background=t["primary"],
                    foreground=t["primary_contrast"], bordercolor=t["primary"],
                    lightcolor=t["primary"], darkcolor=t["primary"],
                    font=f["body_bold"])
        s.map("Accent.TButton",
              background=[("disabled", t["primary_muted"]),
                          ("pressed !disabled", t["primary_active"]),
                          ("active !disabled", t["primary_hover"])],
              bordercolor=[("active !disabled", t["primary_hover"])])

        s.configure("Secondary.TButton", background=t["surface"],
                    foreground=t["text"], bordercolor=t["secondary"],
                    lightcolor=t["surface"], darkcolor=t["surface"])
        s.map("Secondary.TButton",
              background=[("disabled", t["surface"]),
                          ("pressed !disabled", t["surface_hover"]),
                          ("active !disabled", t["surface_hover"])])

        s.configure("Danger.TButton", background=t["danger"],
                    foreground=t["bg"], bordercolor=t["danger"],
                    lightcolor=t["danger"], darkcolor=t["danger"])
        s.map("Danger.TButton",
              background=[("disabled", t["danger_subtle"]),
                          ("pressed !disabled", C.darken(t["danger"], 0.18)),
                          ("active !disabled", C.darken(t["danger"], 0.18))])

        s.configure("Ghost.TButton", background=t["bg"],
                    foreground=t["text_muted"], bordercolor=t["bg"],
                    lightcolor=t["bg"], darkcolor=t["bg"])
        s.map("Ghost.TButton",
              background=[("active !disabled", t["surface_hover"]),
                          ("pressed !disabled", t["surface_hover"])],
              foreground=[("active !disabled", t["text"])])

        s.configure("TEntry", fieldbackground=t["surface"], foreground=t["text"],
                    background=t["bg"], bordercolor=t["border"],
                    lightcolor=t["border"], darkcolor=t["border"],
                    insertcolor=t["text"], padding=pad)
        s.map("TEntry",
              bordercolor=[("focus", t["primary"] if t["focus_indicators"] else t["border"])],
              lightcolor=[("focus", t["primary"] if t["focus_indicators"] else t["border"])],
              fieldbackground=[("disabled", t["surface_hover"])],
              foreground=[("disabled", t["text_muted"])])

        s.configure("TCombobox", fieldbackground=t["surface"], foreground=t["text"],
                    background=t["surface"], bordercolor=t["border"],
                    lightcolor=t["border"], darkcolor=t["border"],
                    arrowcolor=t["text_muted"], padding=pad)
        s.map("TCombobox",
              bordercolor=[("focus", t["primary"] if t["focus_indicators"] else t["border"])],
              fieldbackground=[("readonly", t["surface"]),
                               ("disabled", t["surface_hover"])],
              foreground=[("disabled", t["text_muted"])])

        s.configure("TSpinbox", fieldbackground=t["surface"], foreground=t["text"],
                    bordercolor=t["border"], arrowcolor=t["text_muted"],
                    lightcolor=t["border"], darkcolor=t["border"])
        s.map("TSpinbox",
              bordercolor=[("focus", t["primary"] if t["focus_indicators"] else t["border"])])

        s.configure("TCheckbutton", background=t["bg"], foreground=t["text"],
                    focuscolor=t["primary"], font=f["body"], indicatorforeground=t["primary"])
        s.map("TCheckbutton", background=[("active", t["bg"])])
        s.configure("TRadiobutton", background=t["bg"], foreground=t["text"],
                    focuscolor=t["primary"], font=f["body"])
        s.map("TRadiobutton", background=[("active", t["bg"])])

        s.configure("Treeview", background=t["surface"], fieldbackground=t["surface"],
                    foreground=t["text"], rowheight=t["row_height"],
                    bordercolor=t["border"], lightcolor=t["surface"],
                    darkcolor=t["surface"], font=f["body"])
        s.map("Treeview",
              background=[("selected", t["primary_subtle"])],
              foreground=[("selected", t["text"])])
        s.configure("Treeview.Heading", background=t["surface_hover"],
                    foreground=t["text_muted"], relief="flat",
                    font=f["caption_bold"], padding=(t["space"]["sm"], t["space"]["xs"]))
        s.map("Treeview.Heading", background=[("active", t["border"])])

        s.configure("TProgressbar", troughcolor=t["surface_hover"],
                    background=t["primary"], lightcolor=t["primary"],
                    darkcolor=t["primary"], bordercolor=t["border"],
                    thickness=t["space"]["md"])
        s.configure("Success.TProgressbar", background=t["success"],
                    lightcolor=t["success"], darkcolor=t["success"])
        s.configure("Warning.TProgressbar", background=t["warning"],
                    lightcolor=t["warning"], darkcolor=t["warning"])
        s.configure("Danger.TProgressbar", background=t["danger"],
                    lightcolor=t["danger"], darkcolor=t["danger"])

        for orient in ("Vertical", "Horizontal"):
            name = f"{orient}.TScrollbar"
            s.configure(name, background=t["border"], troughcolor=t["bg"],
                        bordercolor=t["bg"], lightcolor=t["bg"], darkcolor=t["bg"],
                        arrowcolor=t["text_muted"])
            s.map(name, background=[("active", t["text_muted"])])

        s.configure("TNotebook", background=t["bg"], bordercolor=t["border"])
        s.configure("TNotebook.Tab", background=t["bg"], foreground=t["text_muted"],
                    padding=(t["space"]["md"], t["space"]["xs"]), font=f["body"])
        s.map("TNotebook.Tab",
              background=[("selected", t["surface"])],
              foreground=[("selected", t["text"])])

        s.configure("TSeparator", background=t["border"])

        # On-surface variants (widgets placed inside Cards)
        s.configure("Card.TFrame", background=t["surface"])
        s.configure("Card.TLabel", background=t["surface"], foreground=t["text"])
        s.configure("Card.Muted.TLabel", background=t["surface"], foreground=t["text_muted"])
        s.configure("Card.Caption.TLabel", background=t["surface"],
                    foreground=t["text_muted"], font=f["caption"])
        s.configure("Card.H3.TLabel", background=t["surface"], font=f["h3"])
        s.configure("Card.H2.TLabel", background=t["surface"], font=f["h2"])
        s.configure("Card.Inverse.TLabel", background=t["primary_subtle"],
                    foreground=t["primary"], font=f["body_bold"])
        s.configure("Card.TButton", background=t["bg"], foreground=t["text"],
                    bordercolor=t["border"], lightcolor=t["bg"], darkcolor=t["bg"],
                    padding=pad)
        s.map("Card.TButton",
              background=[("disabled", t["surface"]),
                          ("pressed !disabled", t["surface_hover"]),
                          ("active !disabled", t["surface_hover"])],
              foreground=[("disabled", t["text_muted"])])


# ---- module-level singleton access ----
_engine: ThemeEngine | None = None


def init_engine(root: tk.Tk, store: AppearanceStore | None = None) -> ThemeEngine:
    global _engine
    _engine = ThemeEngine(root, store)
    _engine.boot()
    return _engine


def get_engine() -> ThemeEngine:
    if _engine is None:
        raise RuntimeError("ThemeEngine not initialized — call init_engine(root) first")
    return _engine


def get_engine() -> ThemeEngine:
    if _engine is None:
        raise RuntimeError("ThemeEngine not initialized — call init_engine(root) first")
    return _engine
