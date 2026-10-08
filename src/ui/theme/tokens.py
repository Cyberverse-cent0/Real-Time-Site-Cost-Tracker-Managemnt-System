# tokens.py
"""Compile a ThemeSpec into concrete DesignTokens.

Tokens are semantic ("surface", "primary_subtle", "space_md") — UI code
never references raw hex values, so switching themes means recompiling
tokens and re-applying styles, not rewriting components.
"""
from . import color as C
from .presets import ACCENTS, MODE_PALETTES, CUSTOM_BASE, resolve_accent
from .spec import ThemeSpec

DENSITY_SCALES: dict[str, dict[int]] = {
    "compact":     {"xs": 4,  "sm": 6,  "md": 8,  "lg": 10, "xl": 14, "row": 26, "widget": 28},
    "comfortable": {"xs": 6,  "sm": 8,  "md": 12, "lg": 16, "xl": 22, "row": 32, "widget": 34},
    "spacious":    {"xs": 8,  "sm": 10, "md": 16, "lg": 20, "xl": 28, "row": 38, "widget": 40},
}

RADIUS_SCALES: dict[str, dict[str, int]] = {
    "none":     {"sm": 0,  "md": 0,  "lg": 0},
    "small":    {"sm": 2,  "md": 4,  "lg": 6},
    "medium":   {"sm": 4,  "md": 8,  "lg": 12},
    "rounded":  {"sm": 6,  "md": 10, "lg": 16},
    "pill":     {"sm": 8,  "md": 999, "lg": 999},
}

FONT_SCALE_FACTORS = {"small": 0.9, "medium": 1.0, "large": 1.12}

SIDEBAR_WIDTHS = {"expanded": 208, "compact": 56}

LARGER_TEXT_BUMP = 2  # extra points when accessibility "larger text" is on


def build_tokens(spec: ThemeSpec, *, system_prefers_dark: bool = False,
                 default_font_family: str = "Helvetica") -> dict:
    """Compile ThemeSpec -> DesignTokens dict (plain, serializable values)."""
    spec = spec.clamped()

    # ---- 1. Base palette for the (resolved) mode ----
    mode = spec.mode
    if mode == "system":
        mode = "dark" if system_prefers_dark else "light"

    if mode == "custom":
        palette = dict(CUSTOM_BASE)
        palette.update(spec.custom_colors)
    else:
        palette = dict(MODE_PALETTES[mode])

    # Accessibility: high contrast overlay forces the contrast palette
    # (custom colors still win so users keep their accent choices readable).
    if spec.high_contrast and mode != "custom":
        palette.update({k: v for k, v in MODE_PALETTES["high_contrast"].items()})

    # ---- 2. Accent family ----
    primary, secondary = resolve_accent(spec.accent)
    if mode == "custom" and "primary" in spec.custom_colors:
        primary = spec.custom_colors["primary"]
    if mode == "custom" and "secondary" in spec.custom_colors:
        secondary = spec.custom_colors["secondary"]
    # High contrast needs a saturated, readable accent against pure white/black.
    if spec.high_contrast:
        primary = _max_contrast_accent(primary, palette["bg"])

    family = C.derive_family(primary, surface=palette["surface"],
                             text_muted=palette["text_muted"], border=palette["border"])

    # ---- 3. Typography ----
    family_name = spec.font_family or default_font_family
    base = round(10 * FONT_SCALE_FACTORS[spec.font_scale]) + \
        (LARGER_TEXT_BUMP if spec.larger_text else 0)
    fonts = {
        "family": family_name,
        "caption": (family_name, max(8, base - 1)),
        "caption_bold": (family_name, max(8, base - 1), "bold"),
        "body": (family_name, base),
        "body_bold": (family_name, base, "bold"),
        "h3": (family_name, base + 2),
        "h2": (family_name, base + 4, "bold"),
        "h1": (family_name, base + 7, "bold"),
    }

    # ---- 4. Motion ----
    if spec.reduce_motion:
        spec_animations = "none"
    else:
        spec_animations = spec.animations
    motion = {
        "animations_enabled": spec_animations != "none",
        "hover_animations": spec_animations == "full" or spec_animations == "reduced",
        "transition_animations": spec_animations == "full",
    }

    return {
        "mode": mode,
        "mode_requested": spec.mode,
        "accent": spec.accent,
        **palette,
        **family,
        "secondary": secondary,
        "secondary_subtle": C.subtle_variant(secondary, palette["surface"]),
        "secondary_contrast": C.contrast_text(secondary),
        "success_subtle": C.subtle_variant(palette["success"], palette["surface"]),
        "warning_subtle": C.subtle_variant(palette["warning"], palette["surface"]),
        "danger_subtle": C.subtle_variant(palette["danger"], palette["surface"]),
        "radius": dict(RADIUS_SCALES[spec.radius]),
        "space": dict(DENSITY_SCALES[spec.density]),
        "row_height": DENSITY_SCALES[spec.density]["row"],
        "widget_height": DENSITY_SCALES[spec.density]["widget"],
        "sidebar_width": SIDEBAR_WIDTHS["expanded"],
        "sidebar_compact_width": SIDEBAR_WIDTHS["compact"],
        "fonts": fonts,
        "focus_indicators": spec.focus_indicators,
        **motion,
    }


def _max_contrast_accent(primary: str, bg: str) -> str:
    """Darken/lighten an accent until it has solid contrast against bg."""
    best, best_ratio = primary, C.contrast_ratio(primary, bg)
    if best_ratio >= 4.5:
        return primary
    target = "#000000" if C.is_dark(bg) else "#FFFFFF"
    for step in range(1, 10):
        cand = C.mix(primary, target, step / 10.0)
        ratio = C.contrast_ratio(cand, bg)
        if ratio > best_ratio:
            best, best_ratio = cand, ratio
        if ratio >= 5.5:
            return cand
    return best
