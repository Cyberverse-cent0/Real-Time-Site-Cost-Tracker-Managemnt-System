# customtkinter_theme.py
"""CustomTkinter-inspired theme definitions for modern UI styling.

This module provides color palettes, shadow systems, and styling constants
that mimic the look and feel of CustomTkinter while using pure tkinter.
"""
import dataclasses
from typing import Tuple, Dict


@dataclasses.dataclass
class ColorPalette:
    """Modern color palette with light and dark variants."""
    
    # Primary colors
    primary: str = "#1a5fb4"           # Modern blue
    primary_hover: str = "#3584e4"     # Lighter blue
    primary_active: str = "#1c71d8"     # Active blue
    
    # Secondary colors
    secondary: str = "#9141ac"         # Purple
    secondary_hover: str = "#b286d0"   # Lighter purple
    secondary_active: str = "#9a61b3" # Active purple
    
    # Background colors (light mode)
    bg: str = "#fafafa"                # Very light gray
    bg_card: str = "#ffffff"           # Pure white
    bg_sidebar: str = "#2d2d2d"        # Dark sidebar
    bg_input: str = "#f0f0f0"          # Light gray input
    
    # Background colors (dark mode)
    bg_dark: str = "#1e1e1e"            # Dark gray
    bg_card_dark: str = "#2d2d2d"       # Slightly lighter
    bg_sidebar_dark: str = "#121212"    # Very dark sidebar
    bg_input_dark: str = "#3d3d3d"      # Dark input
    
    # Text colors
    text: str = "#2d2d2d"              # Dark text
    text_muted: str = "#6d6d6d"        # Muted text
    text_light: str = "#dcdcdc"        # Light text for dark backgrounds
    text_white: str = "#ffffff"         # Pure white
    
    # Semantic colors
    success: str = "#26a269"           # Green
    warning: str = "#e5a50a"           # Orange
    danger: str = "#c01c28"            # Red
    info: str = "#3584e4"              # Blue
    
    # Border colors
    border: str = "#d0d0d0"            # Light border
    border_focus: str = "#3584e4"      # Focus border
    border_dark: str = "#404040"        # Dark border
    
    # Hover states
    hover: str = "#e8e8e8"             # Light hover
    hover_dark: str = "#3d3d3d"         # Dark hover


@dataclasses.dataclass
class ShadowStyle:
    """Shadow/elevation system for depth effects."""
    
    none: str = ""
    sm: str = "0 1px 2px rgba(0,0,0,0.05)"
    md: str = "0 4px 6px rgba(0,0,0,0.1)"
    lg: str = "0 10px 15px rgba(0,0,0,0.1)"
    xl: str = "0 20px 25px rgba(0,0,0,0.15)"
    
    # Shadow colors for different tones
    shadow_color: str = "rgba(0,0,0,0.1)"
    shadow_color_dark: str = "rgba(0,0,0,0.3)"


@dataclasses.dataclass
class CornerStyle:
    """Rounded corner styles for modern UI."""
    
    none: int = 0
    xs: int = 2
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16
    full: int = 9999


@dataclasses.dataclass
class Elevation:
    """Elevation levels for z-index depth."""
    
    level0: int = 0
    level1: int = 1
    level2: int = 2
    level3: int = 3
    level4: int = 4
    level5: int = 5


# Light mode palette
LIGHT_PALETTE = ColorPalette(
    primary="#1a5fb4",
    primary_hover="#3584e4",
    primary_active="#1c71d8",
    secondary="#9141ac",
    secondary_hover="#b286d0",
    secondary_active="#9a61b3",
    bg="#fafafa",
    bg_card="#ffffff",
    bg_sidebar="#2d2d2d",
    bg_input="#f0f0f0",
    text="#2d2d2d",
    text_muted="#6d6d6d",
    text_light="#dcdcdc",
    text_white="#ffffff",
    success="#26a269",
    warning="#e5a50a",
    danger="#c01c28",
    info="#3584e4",
    border="#d0d0d0",
    border_focus="#3584e4",
    hover="#e8e8e8",
)

# Dark mode palette
DARK_PALETTE = ColorPalette(
    primary="#3584e4",
    primary_hover="#62a0ea",
    primary_active="#1c71d8",
    secondary="#c061cb",
    secondary_hover="#d65d9e",
    secondary_active="#9141ac",
    bg="#1e1e1e",
    bg_card="#2d2d2d",
    bg_sidebar="#121212",
    bg_input="#3d3d3d",
    text="#dcdcdc",
    text_muted="#a0a0a0",
    text_light="#f0f0f0",
    text_white="#ffffff",
    success="#26a269",
    warning="#e5a50a",
    danger="#c01c28",
    info="#3584e4",
    border="#404040",
    border_focus="#3584e4",
    hover="#3d3d3d",
    border_dark="#404040",
    hover_dark="#4d4d4d",
)

# Shadow styles
SHADOWS = ShadowStyle()

# Corner styles
CORNERS = CornerStyle()

# Elevation levels
ELEVATION = Elevation()


def get_palette(dark_mode: bool = False) -> ColorPalette:
    """Get the appropriate color palette based on mode."""
    return DARK_PALETTE if dark_mode else LIGHT_PALETTE


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """Interpolate between two hex colors by a factor (0.0 to 1.0)."""
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    interpolated = tuple(
        int(rgb1[i] + (rgb2[i] - rgb1[i]) * factor)
        for i in range(3)
    )
    
    return rgb_to_hex(interpolated)


def lighten_color(color: str, factor: float = 0.1) -> str:
    """Lighten a hex color by a factor (0.0 to 1.0)."""
    return interpolate_color(color, "#ffffff", factor)


def darken_color(color: str, factor: float = 0.1) -> str:
    """Darken a hex color by a factor (0.0 to 1.0)."""
    return interpolate_color(color, "#000000", factor)


def create_gradient(start_color: str, end_color: str, steps: int = 10) -> list[str]:
    """Create a gradient of colors from start to end."""
    return [interpolate_color(start_color, end_color, i / (steps - 1)) for i in range(steps)]


def apply_shadow(widget, level: str = "md", dark_mode: bool = False) -> str:
    """Get shadow style string for a widget (simulated in tkinter)."""
    shadow_map = {
        "none": SHADOWS.none,
        "sm": SHADOWS.sm,
        "md": SHADOWS.md,
        "lg": SHADOWS.lg,
        "xl": SHADOWS.xl,
    }
    return shadow_map.get(level, SHADOWS.md)


# Modern color schemes inspired by popular design systems
GRUVBOX_PALETTE = ColorPalette(
    primary="#fb4934",
    primary_hover="#fabd2f",
    primary_active="#282828",
    bg="#282828",
    bg_card="#32302f",
    bg_sidebar="#1d2021",
    bg_input="#1d2021",
    text="#ebdbb2",
    text_muted="#928374",
    text_light="#d5c4a1",
    text_white="#fbf1c7",
    success="#98971a",
    warning="#d79921",
    danger="#fb4934",
    info="#458588",
    border="#504945",
    border_focus="#d3869b",
    hover="#3c3836",
)

DRACULA_PALETTE = ColorPalette(
    primary="#8be9fd",
    primary_hover="#6272a4",
    primary_active="#ff79c6",
    bg="#282a36",
    bg_card="#44475a",
    bg_sidebar="#1e1f29",
    bg_input="#44475a",
    text="#f8f8f2",
    text_muted="#6272a4",
    text_light="#f8f8f2",
    text_white="#ffffff",
    success="#50fa7b",
    warning="#f1fa8c",
    danger="#ff5555",
    info="#8be9fd",
    border="#44475a",
    border_focus="#bd93f9",
    hover="#44475a",
)

NORD_PALETTE = ColorPalette(
    primary="#88c0d0",
    primary_hover="#81a1c1",
    primary_active="#5e81ac",
    bg="#2e3440",
    bg_card="#3b4252",
    bg_sidebar="#2e3440",
    bg_input="#434c5e",
    text="#eceff4",
    text_muted="#d8dee9",
    text_light="#eceff4",
    text_white="#ffffff",
    success="#a3be8c",
    warning="#ebcb8b",
    danger="#bf616a",
    info="#88c0d0",
    border="#4c566a",
    border_focus="#88c0d0",
    hover="#434c5e",
)


def get_scheme(name: str) -> ColorPalette:
    """Get a color scheme by name."""
    schemes = {
        "light": LIGHT_PALETTE,
        "dark": DARK_PALETTE,
        "gruvbox": GRUVBOX_PALETTE,
        "dracula": DRACULA_PALETTE,
        "nord": NORD_PALETTE,
    }
    return schemes.get(name.lower(), LIGHT_PALETTE)
