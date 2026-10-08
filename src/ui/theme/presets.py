# presets.py
"""Built-in palettes, accent presets, and full named themes."""

# ---- Accent presets: name -> (label, primary, secondary) ----
ACCENTS: dict[str, tuple[str, str, str]] = {
    "ocean":   ("Ocean",   "#2563EB", "#06B6D4"),
    "emerald": ("Emerald", "#059669", "#14B8A6"),
    "violet":  ("Violet",  "#7C3AED", "#A855F7"),
    "rose":    ("Rose",    "#E11D48", "#F43F5E"),
    "amber":   ("Amber",   "#D97706", "#F59E0B"),
    "slate":   ("Slate",   "#475569", "#64748B"),
    "cyan":    ("Cyan",    "#0891B2", "#22D3EE"),
    "indigo":  ("Indigo",  "#4F46E5", "#818CF8"),
}

# ---- Mode palettes (High contrast overlay handled in tokens.py) ----
MODE_PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#FFFFFF", "surface": "#F8FAFC", "surface_hover": "#F1F5F9",
        "text": "#0F172A", "text_muted": "#64748B", "border": "#E2E8F0",
        "success": "#16A34A", "warning": "#D97706", "danger": "#DC2626",
    },
    "dark": {
        "bg": "#0F172A", "surface": "#1E293B", "surface_hover": "#334155",
        "text": "#F8FAFC", "text_muted": "#94A3B8", "border": "#334155",
        "success": "#22C55E", "warning": "#F59E0B", "danger": "#EF4444",
    },
    "amoled": {
        "bg": "#000000", "surface": "#0A0A0A", "surface_hover": "#171717",
        "text": "#FFFFFF", "text_muted": "#A1A1AA", "border": "#262626",
        "success": "#22C55E", "warning": "#F59E0B", "danger": "#EF4444",
    },
    "high_contrast": {
        "bg": "#FFFFFF", "surface": "#FFFFFF", "surface_hover": "#E5E5E5",
        "text": "#000000", "text_muted": "#1F2937", "border": "#000000",
        "success": "#15803D", "warning": "#B45309", "danger": "#B91C1C",
    },
}

# Base palette custom themes start from.
CUSTOM_BASE = MODE_PALETTES["dark"]

# ---- Full named presets: name -> (label, ThemeSpec kwargs) ----
NAMED_PRESETS: dict[str, tuple[str, dict]] = {
    "default":       ("Default", {"mode": "light", "accent": "ocean"}),
    "midnight":      ("Midnight", {"mode": "dark", "accent": "indigo"}),
    "ocean_dark":    ("Ocean", {"mode": "dark", "accent": "ocean"}),
    "forest":        ("Forest", {"mode": "dark", "accent": "emerald"}),
    "purple":        ("Purple", {"mode": "dark", "accent": "violet"}),
    "rose_light":    ("Rose", {"mode": "light", "accent": "rose"}),
    "cyber":         ("Cyber", {
        "mode": "custom",
        "accent": "#06B6D4",
        "radius": "rounded",
        "custom_colors": {
            "bg": "#0B1120", "surface": "#111827", "surface_hover": "#1F2937",
            "text": "#F8FAFC", "text_muted": "#94A3B8", "border": "#1F2937",
            "primary": "#06B6D4", "secondary": "#8B5CF6",
            "success": "#22C55E", "warning": "#F59E0B", "danger": "#EF4444",
        },
    }),
    "minimal":       ("Minimal", {"mode": "light", "accent": "slate", "radius": "small"}),
    "high_contrast": ("High Contrast", {
        "mode": "high_contrast", "accent": "indigo", "focus_indicators": True,
    }),
}


def resolve_accent(accent: str) -> tuple[str, str]:
    """Return (primary, secondary) for an accent preset name or hex value."""
    from . import color as color_mod

    if accent in ACCENTS:
        return ACCENTS[accent][1], ACCENTS[accent][2]
    if color_mod.is_hex_color(accent):
        return accent, color_mod.lighten(accent, 0.25)
    # Unknown value — fall back to Ocean.
    return ACCENTS["ocean"][1], ACCENTS["ocean"][2]
