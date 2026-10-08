# theme.py
"""App-facing theme facade over the design-token engine.

Everything the views import (``theme.colors.bg_card``, ``theme.spacing.md``,
``get_font``, ``apply_button_style`` …) keeps working, but every value now
reads from the ThemeEngine's compiled DesignTokens at access time — so a
theme switch (quick panel, Theme Studio, preference profiles) restyles the
whole application without touching the view code.

The user's preferences live in ``preferences.py`` (PreferencesEngine, JSON
per user). This module bridges the two:
    UserPreferences --user_prefs_to_spec--> ThemeSpec --> DesignTokens
and on theme edits from the engine side (Studio / quick panel):
    ThemeSpec --sync_spec_to_prefs--> UserPreferences (saved as JSON)
"""
import dataclasses
import tkinter as tk
from typing import Optional

from ui.theme import color as C
from ui.theme.engine import get_engine
from ui.theme.presets import ACCENTS
from ui.theme.spec import ThemeSpec

from .preferences import (
    PreferencesEngine,
    ThemeMode,
    ColorScheme,
    UIDensity,
    IconSize,
    ButtonSize,
    CornerRadius,
    FontFamily,
    MonospaceFont,
    SidebarBehavior,
)


# ======================================================================
# Live proxies — attribute access resolves against the current tokens
# ======================================================================
class _ColorProxy:
    _MAP = {
        "primary": "primary",
        "primary_light": "primary_hover",
        "primary_dark": "primary_active",
        "secondary": "secondary",
        "bg_main": "bg",
        "bg_card": "surface",
        "bg_input": "surface",
        "text_primary": "text",
        "text_secondary": "text_muted",
        "success": "success",
        "warning": "warning",
        "error": "danger",
        "info": "secondary",
        "border": "border",
        "border_focus": "primary",
        "hover": "surface_hover",
        "active": "border",
        "active_button": "primary",
        "accent_color": "primary",
    }

    # Fallback colors for when theme engine is not initialized
    _FALLBACK_COLORS = {
        "primary": "#0ea5e9",
        "primary_light": "#38bdf8",
        "primary_dark": "#0284c7",
        "secondary": "#6366f1",
        "secondary_dark": "#4f46e5",
        "bg_main": "#f8fafc",
        "bg_sidebar": "#1e293b",
        "bg_card": "#ffffff",
        "bg_input": "#ffffff",
        "text_primary": "#0f172a",
        "text_secondary": "#64748b",
        "text_light": "#cbd5e1",
        "text_white": "#ffffff",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#3b82f6",
        "border": "#e2e8f0",
        "border_focus": "#0ea5e9",
        "hover": "#f1f5f9",
        "active": "#e2e8f0",
        "active_button": "#0ea5e9",
        "accent_color": "#0ea5e9",
    }

    def __getattr__(self, name: str) -> str:
        try:
            t = get_engine().tokens
            if name == "text_white":
                return t["primary_contrast"]
            if name == "bg_sidebar":
                return _sidebar_background(t)
            if name == "text_light":
                return C.contrast_text(_sidebar_background(t), min_ratio=6.0)
            if name == "secondary_dark":
                return C.darken(t["secondary"], 0.15)
            if name in self._MAP:
                mapped = self._MAP[name]
                if mapped in t:
                    return t[mapped]
                # If mapped token doesn't exist, use fallback
                return self._FALLBACK_COLORS.get(name, "#000000")
            raise AttributeError(f"Unknown color token: {name!r}")
        except (RuntimeError, KeyError):
            # Theme engine not initialized or token missing, use fallback
            return self._FALLBACK_COLORS.get(name, "#000000")


def _sidebar_background(t: dict) -> str:
    mode = t.get("mode", "light")
    if mode == "light":
        return "#1E293B"
    if mode == "high_contrast":
        return "#000000"
    if mode == "amoled":
        return t["bg"]
    if C.is_dark(t["bg"]):
        return t["surface"]
    return "#1E293B"


class _FontProxy:
    _SIZES = {
        "title_large": 9, "title_medium": 6, "title_small": 3,
        "body_large": 1, "body_normal": 0, "body_small": -1, "caption": -2,
    }

    # Fallback fonts for when theme engine is not initialized
    _FALLBACK_FONTS = {
        "title_large": 24,
        "title_medium": 20,
        "title_small": 16,
        "body_large": 14,
        "body_normal": 12,
        "body_small": 10,
        "caption": 9,
        "primary": "Segoe UI",
        "secondary": "Roboto",
        "mono": "Consolas",
        "bold": True,
        "normal": False,
    }

    def __getattr__(self, name: str):
        try:
            base = get_engine().tokens["fonts"]["body"][1]
            if name in self._SIZES:
                return base + self._SIZES[name]
            if name in ("primary", "secondary", "mono"):
                return get_engine().tokens["fonts"]["family"]
            if name == "bold":
                return True
            if name == "normal":
                return False
            raise AttributeError(f"Unknown font token: {name!r}")
        except (RuntimeError, KeyError):
            # Theme engine not initialized or token missing, use fallback
            return self._FALLBACK_FONTS.get(name, 12)


class _SpacingProxy:
    _MAP = {"xs": "xs", "sm": "sm", "md": "md", "lg": "lg", "xl": "xl"}

    # Fallback spacing for when theme engine is not initialized
    _FALLBACK_SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48,
        "row": 16,
    }

    def __getattr__(self, name: str) -> int:
        try:
            space = get_engine().tokens["space"]
            if name in self._MAP:
                return space[self._MAP[name]]
            if name == "xxl":
                return space["xl"] + space["md"]
            if name == "row":
                return space["row"]
            raise AttributeError(f"Unknown spacing token: {name!r}")
        except (RuntimeError, KeyError):
            # Theme engine not initialized or token missing, use fallback
            return self._FALLBACK_SPACING.get(name, 16)


class _RadiusProxy:
    _MAP = {"none": "sm", "sm": "sm", "md": "md", "lg": "lg", "xl": "lg", "full": "lg"}

    # Fallback radius for when theme engine is not initialized
    _FALLBACK_RADIUS = {
        "none": 0,
        "sm": 4,
        "md": 8,
        "lg": 12,
        "xl": 16,
        "full": 9999,
    }

    def __getattr__(self, name: str) -> int:
        try:
            radius = get_engine().tokens["radius"]
            if name in self._MAP:
                return radius[self._MAP[name]]
            raise AttributeError(f"Unknown radius token: {name!r}")
        except (RuntimeError, KeyError):
            # Theme engine not initialized or token missing, use fallback
            return self._FALLBACK_RADIUS.get(name, 8)


@dataclasses.dataclass
class Shadows:
    """Shadow presets (kept for API compatibility)."""
    none: str = ""
    sm: str = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    md: str = "0 4px 6px -1px rgb(0 0 0 / 0.1)"
    lg: str = "0 10px 15px -3px rgb(0 0 0 / 0.1)"
    xl: str = "0 20px 25px -5px rgb(0 0 0 / 0.1)"


class _Theme:
    """Facade object with the historical attributes, all live."""

    def __init__(self):
        self.colors = _ColorProxy()
        self.fonts = _FontProxy()
        self.spacing = _SpacingProxy()
        self.border_radius = _RadiusProxy()
        self.shadows = Shadows()

    # --- dimensions (scale with density) ---
    @property
    def sidebar_width(self) -> int:
        try:
            engine = get_engine()
            width = {"expanded": 208, "compact": 56, "hidden": 0}.get(engine.spec.sidebar, 208)
            return width
        except (RuntimeError, KeyError):
            return 220

    @property
    def sidebar_collapsed_width(self) -> int:
        return 56

    @property
    def header_height(self) -> int:
        try:
            return max(56, get_engine().tokens["widget_height"] + 24)
        except (RuntimeError, KeyError):
            return 64

    @property
    def card_padding(self) -> int:
        try:
            return get_engine().tokens["space"]["md"]
        except (RuntimeError, KeyError):
            return 20

    @property
    def button_height(self) -> int:
        try:
            return get_engine().tokens["widget_height"]
        except (RuntimeError, KeyError):
            return 40

    @property
    def button_padding_x(self) -> int:
        try:
            return get_engine().tokens["space"]["lg"]
        except (RuntimeError, KeyError):
            return 20

    @property
    def input_height(self) -> int:
        try:
            return get_engine().tokens["widget_height"]
        except (RuntimeError, KeyError):
            return 40

    @property
    def input_padding_x(self) -> int:
        try:
            return get_engine().tokens["space"]["sm"]
        except (RuntimeError, KeyError):
            return 12

    @property
    def icon_size(self) -> int:
        try:
            prefs = get_preferences()
            if prefs is not None:
                return {"small": 16, "medium": 24, "large": 32}[
                    prefs.preferences.size.icon_size.value]
        except (RuntimeError, KeyError, AttributeError):
            pass
        return 24

    @property
    def animations_enabled(self) -> bool:
        try:
            return get_engine().tokens["animations_enabled"]
        except (RuntimeError, KeyError):
            return True

    @property
    def spec(self) -> ThemeSpec:
        try:
            return get_engine().spec
        except RuntimeError:
            return ThemeSpec()


# Global theme instance (API-compatible with the previous static dataclass)
theme = _Theme()

# Global preferences engine (initialized at login by init_preferences)
_preferences_engine: Optional[PreferencesEngine] = None


# ======================================================================
# Preferences <-> ThemeSpec bridge
# ======================================================================
_SCHEME_TO_ACCENT = {
    ColorScheme.BLUE: "ocean",
    ColorScheme.CYAN: "cyan",
    ColorScheme.PURPLE: "violet",
    ColorScheme.GREEN: "emerald",
    ColorScheme.ORANGE: "amber",
    ColorScheme.RED: "rose",
}
_ACCENT_TO_SCHEME = {v: k for k, v in _SCHEME_TO_ACCENT.items()}
_SCHEME_DEFAULT_HEX = {
    ColorScheme.BLUE: "#0ea5e9", ColorScheme.CYAN: "#06b6d4",
    ColorScheme.PURPLE: "#8b5cf6", ColorScheme.GREEN: "#22c55e",
    ColorScheme.ORANGE: "#f97316", ColorScheme.RED: "#ef4444",
}
_MODE_MAP = {
    ThemeMode.LIGHT: "light", ThemeMode.DARK: "dark", ThemeMode.SYSTEM: "system",
    ThemeMode.AMOLED: "amoled", ThemeMode.HIGH_CONTRAST: "high_contrast",
}
_MODE_MAP_BACK = {v: k for k, v in _MODE_MAP.items()}
_DENSITY_MAP = {
    UIDensity.COMPACT: "compact", UIDensity.NORMAL: "comfortable",
    UIDensity.SPACIOUS: "spacious",
}
_DENSITY_MAP_BACK = {"compact": UIDensity.COMPACT,
                     "comfortable": UIDensity.NORMAL, "spacious": UIDensity.SPACIOUS}
_RADIUS_MAP = {
    CornerRadius.SHARP: "none", CornerRadius.SMALL: "small",
    CornerRadius.MEDIUM: "medium", CornerRadius.LARGE: "rounded",
    CornerRadius.PILL: "pill",
}
_RADIUS_MAP_BACK = {"none": CornerRadius.SHARP, "small": CornerRadius.SMALL,
                    "medium": CornerRadius.MEDIUM, "rounded": CornerRadius.LARGE,
                    "pill": CornerRadius.PILL}
_SIDEBAR_MAP = {
    SidebarBehavior.EXPANDED: "expanded", SidebarBehavior.COLLAPSED: "compact",
    SidebarBehavior.AUTO_HIDE: "compact",
}
_SIDEBAR_MAP_BACK = {"expanded": SidebarBehavior.EXPANDED,
                     "compact": SidebarBehavior.COLLAPSED,
                     "hidden": SidebarBehavior.AUTO_HIDE}
_FONT_FAMILY_MAP = {
    FontFamily.INTER: "Inter", FontFamily.ROBOTO: "Roboto",
    FontFamily.NOTO_SANS: "Noto Sans", FontFamily.SYSTEM_UI: "",
    FontFamily.IBM_PLEX: "IBM Plex Sans",
}
_FONT_FAMILY_BACK = {v: k for k, v in _FONT_FAMILY_MAP.items()}


def user_prefs_to_spec(prefs) -> ThemeSpec:
    """Derive the ThemeSpec from the user's UserPreferences."""
    appearance = prefs.appearance
    accent = appearance.accent_color
    if appearance.color_scheme == ColorScheme.CUSTOM:
        if not C.is_hex_color(accent):
            accent = "ocean"
    elif appearance.color_scheme in _SCHEME_TO_ACCENT:
        # A hand-picked hex that differs from the scheme default counts as custom.
        if C.is_hex_color(accent) and accent.lower() != \
                _SCHEME_DEFAULT_HEX[appearance.color_scheme].lower():
            accent = accent
        else:
            accent = _SCHEME_TO_ACCENT[appearance.color_scheme]
    else:
        accent = "ocean"

    font_size = prefs.typography.font_size
    font_scale = "small" if font_size <= 11 else ("large" if font_size >= 15 else "medium")

    return ThemeSpec(
        mode=_MODE_MAP.get(prefs.appearance.theme, "light"),
        accent=accent,
        density=_DENSITY_MAP.get(prefs.size.density, "comfortable"),
        radius=_RADIUS_MAP.get(prefs.shape.corner_radius, "medium"),
        sidebar=_SIDEBAR_MAP.get(prefs.layout.sidebar_behavior, "expanded"),
        animations="none" if prefs.accessibility.reduce_motion else "full",
        font_family=_FONT_FAMILY_MAP.get(prefs.typography.font_family, ""),
        font_scale=font_scale,
        high_contrast=prefs.accessibility.high_contrast,
        reduce_motion=prefs.accessibility.reduce_motion,
        larger_text=prefs.accessibility.larger_text,
        focus_indicators=prefs.accessibility.always_show_focus or True,
    )


def sync_spec_to_prefs(spec: ThemeSpec, prefs_engine: PreferencesEngine) -> None:
    """Write ThemeSpec changes (Studio / quick panel) back into UserPreferences."""
    prefs = prefs_engine.preferences
    appearance = prefs.appearance

    if spec.mode in _MODE_MAP_BACK:
        appearance.theme = _MODE_MAP_BACK[spec.mode]
    if spec.accent in _ACCENT_TO_SCHEME:
        appearance.color_scheme = _ACCENT_TO_SCHEME[spec.accent]
        appearance.accent_color = ACCENTS[spec.accent][1]
    elif C.is_hex_color(spec.accent):
        appearance.color_scheme = ColorScheme.CUSTOM
        appearance.accent_color = spec.accent

    prefs.size.density = _DENSITY_MAP_BACK.get(spec.density, UIDensity.NORMAL)
    prefs.shape.corner_radius = _RADIUS_MAP_BACK.get(spec.radius, CornerRadius.MEDIUM)
    prefs.layout.sidebar_behavior = _SIDEBAR_MAP_BACK.get(
        spec.sidebar, SidebarBehavior.EXPANDED)

    prefs.accessibility.high_contrast = spec.high_contrast
    prefs.accessibility.reduce_motion = spec.reduce_motion or spec.animations == "none"
    prefs.accessibility.larger_text = spec.larger_text

    if spec.font_family in _FONT_FAMILY_BACK:
        prefs.typography.font_family = _FONT_FAMILY_BACK[spec.font_family]
    prefs.typography.font_size = {"small": 11, "medium": 12, "large": 15}[spec.font_scale]

    prefs_engine.save()


def _on_prefs_changed(prefs) -> None:
    """Observer: preferences changed (profile applied / Apply clicked)."""
    engine = get_engine()
    engine.apply(user_prefs_to_spec(prefs), persist=False)


def init_preferences(username: str) -> PreferencesEngine:
    """Initialize the preferences engine for a user and wire the bridge."""
    global _preferences_engine
    _preferences_engine = PreferencesEngine(username)
    _preferences_engine.register_observer(_on_prefs_changed)
    engine = get_engine()
    engine.set_current_user(username)
    engine.set_persistence_callback(
        lambda spec: sync_spec_to_prefs(spec, _preferences_engine)
        if _preferences_engine else None)
    engine.apply(user_prefs_to_spec(_preferences_engine.preferences), persist=False)
    return _preferences_engine


def get_preferences() -> Optional[PreferencesEngine]:
    """Get the current preferences engine."""
    return _preferences_engine


def refresh_theme() -> None:
    """Re-apply the current preferences (called after preference edits)."""
    if _preferences_engine is not None:
        _on_prefs_changed(_preferences_engine.preferences)
    else:
        get_engine().apply(ThemeSpec(), persist=False)


# ======================================================================
# Styling helpers (unchanged API, token-driven values)
# ======================================================================
def get_font(size: int, family: Optional[str] = None, bold: bool = False) -> tuple:
    """Get a font tuple for tkinter widgets."""
    font_family = family or theme.fonts.primary
    weight = "bold" if bold else "normal"
    return (font_family, int(size), weight)


def apply_button_style(button: tk.Button, variant: str = "primary", size: str = "medium") -> None:
    """Apply consistent button styling."""
    colors = theme.colors

    if variant == "primary":
        bg, fg, active_bg = colors.primary, colors.text_white, colors.primary_dark
    elif variant == "secondary":
        bg, fg, active_bg = colors.secondary, colors.text_white, colors.secondary_dark
    elif variant == "success":
        bg, fg, active_bg = colors.success, "#FFFFFF", C.darken(colors.success, 0.15)
    elif variant == "danger":
        bg, fg, active_bg = colors.error, "#FFFFFF", C.darken(colors.error, 0.15)
    elif variant == "outline":
        bg, fg, active_bg = colors.bg_card, colors.primary, colors.hover
    else:  # ghost
        bg, fg, active_bg = colors.bg_main, colors.text_primary, colors.hover

    height = theme.button_height
    if size == "small":
        height = int(height * 0.8)
    elif size == "large":
        height = int(height * 1.2)

    button.config(
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=fg,
        relief="flat",
        height=height // 10,  # tkinter uses character units
        padx=theme.button_padding_x,
        font=get_font(theme.fonts.body_normal, bold=True),
        cursor="hand2",
        borderwidth=0,
    )


def apply_entry_style(entry) -> None:
    """Apply consistent entry/input field styling."""
    colors = theme.colors
    entry.config(
        bg=colors.bg_input,
        fg=colors.text_primary,
        insertbackground=colors.text_primary,
        relief="solid",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=colors.border,
        highlightcolor=colors.border_focus,
        font=get_font(theme.fonts.body_normal),
    )


def apply_label_style(label: tk.Label, variant: str = "body") -> None:
    """Apply consistent label styling."""
    colors = theme.colors
    fonts = theme.fonts

    if variant == "title":
        label.config(font=get_font(fonts.title_large, bold=True), fg=colors.text_primary)
    elif variant == "subtitle":
        label.config(font=get_font(fonts.title_medium, bold=True), fg=colors.text_primary)
    elif variant == "heading":
        label.config(font=get_font(fonts.title_small, bold=True), fg=colors.text_primary)
    elif variant == "body":
        label.config(font=get_font(fonts.body_normal), fg=colors.text_primary)
    elif variant == "caption":
        label.config(font=get_font(fonts.caption), fg=colors.text_secondary)
    elif variant == "muted":
        label.config(font=get_font(fonts.body_normal), fg=colors.text_secondary)


def create_card_frame(parent: tk.Widget, **kwargs) -> tk.Frame:
    """Create a styled card frame."""
    colors = theme.colors
    frame = tk.Frame(parent, bg=colors.bg_card, relief="flat", borderwidth=0, **kwargs)
    frame.config(highlightbackground=colors.border, highlightthickness=1)
    return frame


def load_icon(icon_path: str, size: tuple[int, int] = (24, 24)) -> Optional[tk.PhotoImage]:
    """Load a raster icon; SVGs are not supported by tk.PhotoImage (returns None)."""
    if str(icon_path).lower().endswith(".svg"):
        return None
    try:
        return tk.PhotoImage(file=icon_path)
    except Exception:
        return None
