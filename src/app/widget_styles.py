# widget_styles.py
"""Modern widget styling functions with CustomTkinter-inspired design.

Provides styling functions for buttons, cards, entries, and frames with
rounded corners, shadows, hover effects, and focus states.
"""
import tkinter as tk
from typing import Optional

from .theme import theme, get_font
from .customtkinter_theme import CORNERS, get_palette, lighten_color, darken_color


def apply_ctk_button_style(button: tk.Button, variant: str = "primary", 
                          size: str = "medium", corner_radius: str = "md") -> None:
    """Apply CustomTkinter-inspired button styling with rounded corners and hover effects.
    
    Args:
        button: The button widget to style
        variant: Color variant - "primary", "secondary", "success", "warning", "danger", "ghost"
        size: Size variant - "small", "medium", "large"
        corner_radius: Corner radius - "none", "xs", "sm", "md", "lg", "xl", "full"
    """
    colors = theme.colors
    spacing = theme.spacing
    
    # Get color based on variant
    color_map = {
        "primary": (colors.primary, colors.primary_hover, colors.primary_active),
        "secondary": (colors.secondary, colors.secondary_hover, colors.secondary_active),
        "success": (colors.success, lighten_color(colors.success, 0.1), darken_color(colors.success, 0.1)),
        "warning": (colors.warning, lighten_color(colors.warning, 0.1), darken_color(colors.warning, 0.1)),
        "danger": (colors.error, lighten_color(colors.error, 0.1), darken_color(colors.error, 0.1)),
        "ghost": (colors.bg_card, colors.hover, colors.active),
    }
    
    bg, hover_bg, active_bg = color_map.get(variant, color_map["primary"])
    
    # Text color
    fg = colors.text_white if variant != "ghost" else colors.text_primary
    
    # Size mapping
    size_map = {
        "small": {"height": 32, "padding_x": 12, "font_size": 10},
        "medium": {"height": 40, "padding_x": 20, "font_size": 12},
        "large": {"height": 48, "padding_x": 24, "font_size": 14},
    }
    size_config = size_map.get(size, size_map["medium"])
    
    # Corner radius
    radius = getattr(CORNERS, corner_radius, CORNERS.md)
    
    # Configure button
    button.config(
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        highlightthickness=0,
        height=size_config["height"] // 10,  # tkinter uses character units
        padx=size_config["padding_x"],
        font=get_font(size_config["font_size"], bold=True),
        cursor="hand2",
    )
    
    # Store original colors for hover effects
    button._ctk_bg = bg
    button._ctk_hover_bg = hover_bg
    button._ctk_active_bg = active_bg
    button._ctk_fg = fg
    
    # Bind hover events
    def on_enter(event):
        button.config(bg=hover_bg)
    
    def on_leave(event):
        button.config(bg=bg)
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)


def apply_ctk_card_style(frame: tk.Frame, shadow: str = "md", 
                       corner_radius: str = "md", border: bool = True) -> None:
    """Apply CustomTkinter-inspired card styling with shadow and rounded corners.
    
    Args:
        frame: The frame widget to style
        shadow: Shadow level - "none", "sm", "md", "lg", "xl"
        corner_radius: Corner radius - "none", "xs", "sm", "md", "lg", "xl", "full"
        border: Whether to show a border
    """
    colors = theme.colors
    
    # Background color
    bg = colors.bg_card
    
    # Corner radius (simulated in tkinter via border)
    radius = getattr(CORNERS, corner_radius, CORNERS.md)
    
    # Configure frame
    frame.config(bg=bg)
    
    if border:
        frame.config(
            highlightbackground=colors.border,
            highlightcolor=colors.border_focus,
            highlightthickness=1,
        )
    else:
        frame.config(highlightthickness=0)
    
    # Store shadow level for potential use
    frame._ctk_shadow = shadow
    frame._ctk_radius = radius


def apply_ctk_entry_style(entry: tk.Entry, corner_radius: str = "sm", 
                         show_focus: bool = True) -> None:
    """Apply CustomTkinter-inspired entry styling with focus ring.
    
    Args:
        entry: The entry widget to style
        corner_radius: Corner radius - "none", "xs", "sm", "md", "lg", "xl", "full"
        show_focus: Whether to show focus ring
    """
    colors = theme.colors
    
    # Background colors
    bg = colors.bg_input
    fg = colors.text_primary
    
    # Corner radius (simulated via border)
    radius = getattr(CORNERS, corner_radius, CORNERS.sm)
    
    # Configure entry
    entry.config(
        bg=bg,
        fg=fg,
        insertbackground=colors.primary,
        relief="solid",
        bd=1 if show_focus else 0,
        highlightthickness=2 if show_focus else 0,
        highlightbackground=colors.border,
        highlightcolor=colors.border_focus,
        font=get_font(theme.fonts.body_normal),
    )
    
    # Store original border color
    entry._ctk_border = colors.border
    entry._ctk_border_focus = colors.border_focus
    
    # Bind focus events
    def on_focus_in(event):
        if show_focus:
            entry.config(highlightcolor=colors.border_focus)
    
    def on_focus_out(event):
        if show_focus:
            entry.config(highlightcolor=colors.border)
    
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


def apply_ctk_frame_style(frame: tk.Frame, bg_variant: str = "card", 
                         corner_radius: str = "md") -> None:
    """Apply CustomTkinter-inspired frame styling.
    
    Args:
        frame: The frame widget to style
        bg_variant: Background variant - "card", "main", "sidebar", "input"
        corner_radius: Corner radius - "none", "xs", "sm", "md", "lg", "xl", "full"
    """
    colors = theme.colors
    
    # Background color based on variant
    bg_map = {
        "card": colors.bg_card,
        "main": colors.bg_main,
        "sidebar": colors.bg_sidebar,
        "input": colors.bg_input,
    }
    bg = bg_map.get(bg_variant, colors.bg_card)
    
    # Corner radius
    radius = getattr(CORNERS, corner_radius, CORNERS.md)
    
    # Configure frame
    frame.config(bg=bg)
    frame._ctk_bg_variant = bg_variant
    frame._ctk_radius = radius


def apply_ctk_label_style(label: tk.Label, variant: str = "body", 
                         tone: str = "primary") -> None:
    """Apply CustomTkinter-inspired label styling.
    
    Args:
        label: The label widget to style
        variant: Text variant - "title", "subtitle", "heading", "body", "caption", "muted"
        tone: Color tone - "primary", "secondary", "success", "warning", "danger", "muted"
    """
    colors = theme.colors
    fonts = theme.fonts
    
    # Font mapping
    font_map = {
        "title": (fonts.title_large, True),
        "subtitle": (fonts.title_medium, True),
        "heading": (fonts.title_small, True),
        "body": (fonts.body_normal, False),
        "caption": (fonts.caption, False),
        "muted": (fonts.body_small, False),
    }
    
    font_size, bold = font_map.get(variant, (fonts.body_normal, False))
    
    # Color mapping
    color_map = {
        "primary": colors.text_primary,
        "secondary": colors.secondary,
        "success": colors.success,
        "warning": colors.warning,
        "danger": colors.error,
        "muted": colors.text_secondary,
    }
    fg = color_map.get(tone, colors.text_primary)
    
    label.config(
        font=get_font(font_size, bold=bold),
        fg=fg,
    )


def apply_ctk_scrollbar_style(scrollbar: tk.Scrollbar, variant: str = "primary") -> None:
    """Apply CustomTkinter-inspired scrollbar styling.
    
    Args:
        scrollbar: The scrollbar widget to style
        variant: Color variant - "primary", "secondary"
    """
    colors = theme.colors
    
    # Color mapping
    color_map = {
        "primary": colors.primary,
        "secondary": colors.secondary,
    }
    bg = color_map.get(variant, colors.primary)
    
    scrollbar.config(
        troughcolor=colors.bg_input,
        bg=bg,
        activebackground=colors.primary_hover,
        orient="vertical",
    )


def apply_ctk_progressbar_style(progressbar: ttk.Progressbar, variant: str = "primary") -> None:
    """Apply CustomTkinter-inspired progressbar styling.
    
    Args:
        progressbar: The progressbar widget to style
        variant: Color variant - "primary", "secondary", "success", "warning", "danger"
    """
    colors = theme.colors
    
    # Color mapping
    color_map = {
        "primary": colors.primary,
        "secondary": colors.secondary,
        "success": colors.success,
        "warning": colors.warning,
        "danger": colors.error,
    }
    color = color_map.get(variant, colors.primary)
    
    style = ttk.Style()
    style.theme_use('default')
    style.configure(f"CTK.Horizontal.TProgressbar",
                   troughcolor=colors.bg_input,
                   background=color,
                   bordercolor=colors.border,
                   lightcolor=color,
                   darkcolor=color)
    
    progressbar.configure(style="CTK.Horizontal.TProgressbar")


def create_ctk_button(parent: tk.Text, text: str, command=None, 
                     variant: str = "primary", size: str = "medium",
                     corner_radius: str = "md") -> tk.Button:
    """Create a new button with CustomTkinter styling applied.
    
    Args:
        parent: Parent widget
        text: Button text
        command: Button command
        variant: Color variant
        size: Size variant
        corner_radius: Corner radius
    
    Returns:
        Styled button widget
    """
    button = tk.Button(parent, text=text, command=command)
    apply_ctk_button_style(button, variant, size, corner_radius)
    return button


def create_ctk_card(parent: tk.Widget, shadow: str = "md",
                    corner_radius: str = "md", border: bool = True) -> tk.Frame:
    """Create a new card frame with CustomTkinter styling applied.
    
    Args:
        parent: Parent widget
        shadow: Shadow level
        corner_radius: Corner radius
        border: Whether to show border
    
    Returns:
        Styled card frame
    """
    card = tk.Frame(parent)
    apply_ctk_card_style(card, shadow, corner_radius, border)
    return card


def create_ctk_entry(parent: tk.Widget, textvariable=None, 
                    corner_radius: str = "sm", show_focus: bool = True) -> tk.Entry:
    """Create a new entry with CustomTkinter styling applied.
    
    Args:
        parent: Parent widget
        textvariable: Text variable
        corner_radius: Corner radius
        show_focus: Whether to show focus ring
    
    Returns:
        Styled entry widget
    """
    entry = tk.Entry(parent, textvariable=textvariable)
    apply_ctk_entry_style(entry, corner_radius, show_focus)
    return entry
