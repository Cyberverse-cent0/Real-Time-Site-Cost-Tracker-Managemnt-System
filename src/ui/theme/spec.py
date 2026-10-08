# spec.py
"""ThemeSpec — the serializable set of user appearance preferences.

A ThemeSpec is the single source of truth for how the app looks. It is
stored per-user in the database (AppearanceStore), exported/imported as
JSON theme files, and compiled into concrete DesignTokens by tokens.py.
"""
from dataclasses import dataclass, field, asdict

MODES = ("light", "dark", "system", "amoled", "high_contrast", "custom")
DENSITIES = ("compact", "comfortable", "spacious")
RADII = ("none", "small", "medium", "rounded", "pill")
SIDEBARS = ("expanded", "compact", "hidden")
ANIMATIONS = ("full", "reduced", "none")
FONT_SCALES = ("small", "medium", "large")

# Keys allowed inside custom_colors (mode == "custom" / Theme Studio overrides)
CUSTOM_COLOR_KEYS = (
    "bg", "surface", "surface_hover", "text", "text_muted", "border",
    "primary", "secondary", "success", "warning", "danger",
)


@dataclass
class ThemeSpec:
    mode: str = "light"
    accent: str = "ocean"              # preset name ("ocean") or hex ("#2563EB")
    custom_colors: dict = field(default_factory=dict)  # partial palette overrides
    density: str = "comfortable"
    radius: str = "medium"
    sidebar: str = "expanded"
    animations: str = "full"
    font_family: str = ""              # "" = system default
    font_scale: str = "medium"
    # Accessibility
    high_contrast: bool = False        # force the high-contrast palette overlay
    reduce_motion: bool = False        # force all animations off
    larger_text: bool = False          # bump font sizes up
    focus_indicators: bool = True      # visible focus rings on inputs/buttons

    def clamped(self) -> "ThemeSpec":
        """Return a copy with unknown/invalid values replaced by defaults."""
        from . import color as color_mod

        def pick(value, options, default):
            return value if value in options else default

        accent = self.accent
        if not accent.startswith("#") and not _is_named_accent(accent):
            accent = "ocean"
        if accent.startswith("#") and not color_mod.is_hex_color(accent):
            accent = "ocean"

        cleaned_colors = {
            k: v for k, v in (self.custom_colors or {}).items()
            if k in CUSTOM_COLOR_KEYS and isinstance(v, str) and color_mod.is_hex_color(v)
        }
        return ThemeSpec(
            mode=pick(self.mode, MODES, "light"),
            accent=accent,
            custom_colors=cleaned_colors,
            density=pick(self.density, DENSITIES, "comfortable"),
            radius=pick(self.radius, RADII, "medium"),
            sidebar=pick(self.sidebar, SIDEBARS, "expanded"),
            animations=pick(self.animations, ANIMATIONS, "full"),
            font_family=self.font_family or "",
            font_scale=pick(self.font_scale, FONT_SCALES, "medium"),
            high_contrast=bool(self.high_contrast),
            reduce_motion=bool(self.reduce_motion),
            larger_text=bool(self.larger_text),
            focus_indicators=bool(self.focus_indicators),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ThemeSpec":
        known = {f: data[f] for f in cls.__dataclass_fields__ if f in data}
        return cls(**known).clamped()


def _is_named_accent(name: str) -> bool:
    from .presets import ACCENTS
    return name in ACCENTS
