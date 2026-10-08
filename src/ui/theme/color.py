# color.py
"""Color utilities: parsing, mixing, and WCAG contrast.

This is the ContrastEngine + ColorGenerator of the theme system:
  * ContrastEngine  – picks readable text colors for any background
  * derive_family() – generates hover/active/subtle/muted/border/contrast
                      variants from a single accent color, so changing the
                      accent re-tints the whole interface automatically.
"""


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Parse '#RRGGBB' (case-insensitive) into an (r, g, b) tuple."""
    v = value.strip().lstrip("#")
    if len(v) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {value!r}")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Format an (r, g, b) tuple as '#RRGGBB'."""
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, round(r))),
        max(0, min(255, round(g))),
        max(0, min(255, round(b))),
    )


def is_hex_color(value: str) -> bool:
    try:
        hex_to_rgb(value)
        return True
    except ValueError:
        return False


def mix(c1: str, c2: str, t: float) -> str:
    """Blend c1 -> c2 by t (0.0 = c1, 1.0 = c2)."""
    t = max(0.0, min(1.0, t))
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(*(a[i] * (1 - t) + b[i] * t for i in range(3)))


def lighten(color: str, t: float) -> str:
    return mix(color, "#FFFFFF", t)


def darken(color: str, t: float) -> str:
    return mix(color, "#000000", t)


def _linearize_channel(v: int) -> float:
    s = v / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """WCAG 2.0 relative luminance (0.0 black .. 1.0 white)."""
    r, g, b = ( _linearize_channel(v) for v in hex_to_rgb(color) )
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(c1: str, c2: str) -> float:
    """WCAG contrast ratio between two colors (1.0 .. 21.0)."""
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def is_dark(color: str) -> bool:
    return relative_luminance(color) < 0.5


# ---------- ContrastEngine ----------
def contrast_text(background: str, candidates: tuple[str, ...] = ("#000000", "#FFFFFF"),
                  min_ratio: float = 4.5) -> str:
    """Return the most readable candidate text color for a background.

    If no candidate reaches `min_ratio`, the best one is progressively
    blended toward pure black/white until it does — this prevents themes
    with unreadable text (e.g. an amber accent with white text).
    """
    best, best_ratio = None, -1.0
    for cand in candidates:
        ratio = contrast_ratio(background, cand)
        if ratio > best_ratio:
            best, best_ratio = cand, ratio
    if best_ratio >= min_ratio or best is None:
        return best  # type: ignore[return-value]

    blend_target = "#000000" if contrast_ratio(background, "#000000") > \
        contrast_ratio(background, "#FFFFFF") else "#FFFFFF"
    for step in range(1, 12):
        blended = mix(best, blend_target, step / 12.0)
        if contrast_ratio(background, blended) >= min_ratio:
            return blended
    return blend_target


# ---------- ColorGenerator ----------
def derive_family(primary: str, *, surface: str, text_muted: str, border: str) -> dict[str, str]:
    """Generate the full semantic family for a primary accent color.

    Dark surfaces get lighter hover states, light surfaces darker ones,
    so buttons remain visible in every mode.
    """
    on_dark = is_dark(surface)
    if on_dark:
        hover = lighten(primary, 0.14)
        active = lighten(primary, 0.24)
    else:
        hover = darken(primary, 0.14)
        active = darken(primary, 0.24)
    return {
        "primary": primary,
        "primary_hover": hover,
        "primary_active": active,
        "primary_subtle": mix(primary, surface, 0.86),   # tinted backgrounds / badges
        "primary_muted": mix(primary, text_muted, 0.55),  # de-emphasized accents
        "primary_border": mix(primary, border, 0.55),
        "primary_contrast": contrast_text(primary),       # auto black/white text
    }


def subtle_variant(color: str, surface: str) -> str:
    """Tinted background variant for semantic colors (badges, banners)."""
    return mix(color, surface, 0.86)
