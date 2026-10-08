# sidebar.py
import tkinter as tk
import dataclasses
import typing
import pathlib
from .theme import theme, get_font, load_icon

from ui.theme.engine import get_engine

# Project root (…/Real-Time-Site-Cost-Tracker-Managemnt-System)
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

# tk.PhotoImage cannot render SVG files, so icons fall back to glyphs.
ICON_GLYPHS: dict[str, str] = {
    "home.svg": "⌂", "square-dashed.svg": "▦", "clipboard-paste.svg": "🧾",
    "copy.svg": "📋", "settings.svg": "⚙", "user.svg": "⏻",
    "check.svg": "✓", "wifi.svg": "📶", "wifi-sync.svg": "⟳",
}


@dataclasses.dataclass
class Icon:
    """Icon configuration for sidebar buttons."""
    path: str  # path to the icon image relative to public/
    size: tuple[int, int] = (24, 24)  # size of the icon (width, height)

    def glyph(self) -> str:
        """Emoji fallback for icons (SVGs are not raster-loadable in tk)."""
        return ICON_GLYPHS.get(pathlib.Path(self.path).name.lower(), "•")


@dataclasses.dataclass
class NavigationItem:
    """Navigation item configuration."""
    text: str
    command: typing.Callable[[], None]
    icon: typing.Optional[Icon] = None


class Sidebar:
    """Modern sidebar component with theming support."""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.colors = theme.colors
        
        self.frame = tk.Frame(
            parent,
            bg=self.colors.bg_sidebar,
            width=theme.sidebar_width
        )
        self.frame.pack(side="left", fill="y")
        self.frame.pack_propagate(False)  # Prevent shrinking
        
        self.buttons: list[tk.Button] = []
        self.active_button: typing.Optional[tk.Button] = None
        self.icon_cache: dict[str, tk.PhotoImage] = {}
        self._labels: list[dict] = []  # {"container","button","text","icon"}

        # Add logo/header section
        self._add_header()

        # Restyle everything when the theme changes
        get_engine().add_listener(self.frame, self.restyle)

    def _add_header(self):
        """Add the application logo/header to the sidebar."""
        header_frame = tk.Frame(self.frame, bg=self.colors.bg_sidebar)
        header_frame.pack(fill="x", pady=(theme.spacing.lg, theme.spacing.md), padx=theme.spacing.md)
        self._header_frame = header_frame

        # Text logo (SVG assets can't be rasterized by tk.PhotoImage)
        logo_label = tk.Label(
            header_frame,
            text="🏗️",
            bg=self.colors.bg_sidebar,
            font=("Segoe UI", 32)
        )
        logo_label.pack()

        # App name
        app_label = tk.Label(
            header_frame,
            text="Cost Tracker",
            bg=self.colors.bg_sidebar,
            fg=self.colors.text_light,
            font=get_font(theme.fonts.body_normal, bold=True)
        )
        app_label.pack(pady=(theme.spacing.sm, 0))
        self._labels.append({"container": header_frame, "labels": [logo_label, app_label]})

    def add_button(self, text: str, command: typing.Callable[[], None], icon: typing.Optional[Icon] = None):
        """Add a navigation button to the sidebar."""
        colors = self.colors
        spacing = theme.spacing

        # Container for icon + text
        btn_container = tk.Frame(self.frame, bg=colors.bg_sidebar)
        btn_container.pack(fill="x", padx=spacing.sm, pady=spacing.xs)

        # Load icon if provided (falls back to an emoji glyph for SVGs)
        icon_image = None
        if icon:
            icon_key = icon.path
            if icon_key not in self.icon_cache:
                try:
                    full_path = PROJECT_ROOT / "public" / icon.path
                    if full_path.exists():
                        icon_image = load_icon(str(full_path), icon.size)
                        if icon_image:
                            self.icon_cache[icon_key] = icon_image
                except Exception:
                    pass
            icon_image = self.icon_cache.get(icon_key)

        label = text if icon_image else (
            f"{icon.glyph()}  {text}" if icon else text)

        # Create button
        btn = tk.Button(
            btn_container,
            text=label,
            command=lambda b=btn_container, c=command: self._on_button_click(b, c),
            bg=colors.bg_sidebar,
            fg=colors.text_light,
            activebackground=colors.active_button,
            activeforeground=colors.text_white,
            relief="flat",
            anchor="w",
            padx=spacing.md,
            pady=spacing.sm,
            font=get_font(theme.fonts.body_normal),
            cursor="hand2",
            compound="left" if icon_image else "none",
            image=icon_image
        )

        if icon_image:
            btn.config(image=icon_image)

        btn.pack(fill="x")

        # Bind hover events
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self._hover_color()))
        btn.bind("<Leave>", lambda e, b=btn: self._restore_button_color(b))

        # Store reference to the button container for active state
        btn_container.button = btn
        self.buttons.append(btn_container)
        self._labels.append({"container": btn_container, "button": btn,
                             "text": text, "icon": icon})

    def _on_button_click(self, button_container: tk.Frame, command: typing.Callable[[], None]):
        """Handle button click: set active button and call command."""
        # Reset previous active button
        if self.active_button:
            self._paint_active(self.active_button.button, active=False)

        # Set new active button
        self._paint_active(button_container.button, active=True)
        self.active_button = button_container

        # Execute command
        command()

    def _restore_button_color(self, button: tk.Button):
        """Restore button color based on active state."""
        # Check if this button is the active one
        for btn_container in self.buttons:
            if btn_container.button == button:
                self._paint_active(button, btn_container == self.active_button)
                break
    
    def add_separator(self):
        """Add a visual separator to the sidebar."""
        separator = tk.Frame(
            self.frame,
            bg=self.colors.hover,
            height=1
        )
        separator.pack(fill="x", padx=theme.spacing.md, pady=theme.spacing.md)
        self._labels.append({"container": separator, "separator": True})

    def add_spacer(self, height: int = None):
        """Add empty space that pushes everything below it to the bottom."""
        spacer = tk.Frame(self.frame, bg=self.colors.bg_sidebar)
        spacer.pack(fill="both", expand=True)
        self._labels.append({"container": spacer, "spacer": True})

    def _hover_color(self) -> str:
        """Hover color that stays visible on the dark sidebar panel."""
        from ui.theme import color as C
        t = get_engine().tokens
        return C.lighten(self.colors.bg_sidebar, 0.08) if C.is_dark(self.colors.bg_sidebar) \
            else t["surface_hover"]

    def _paint_active(self, btn: tk.Button, active: bool) -> None:
        colors = self.colors
        if active:
            btn.config(bg=colors.active_button, fg=colors.text_white)
        else:
            btn.config(bg=colors.bg_sidebar, fg=colors.text_light)

    def restyle(self):
        """Re-apply the current theme to every sidebar widget."""
        if not hasattr(self, "frame") or not self.frame.winfo_exists():
            return
        colors = self.colors
        try:
            self.frame.config(bg=colors.bg_sidebar)
        except tk.TclError:
            return
        for entry in self._labels:
            container = entry["container"]
            try:
                if entry.get("separator"):
                    container.config(bg=colors.hover)
                else:
                    container.config(bg=colors.bg_sidebar)
            except tk.TclError:
                continue
            for lbl in entry.get("labels", []):
                try:
                    lbl.config(bg=colors.bg_sidebar, fg=colors.text_light)
                except tk.TclError:
                    pass
            if "button" in entry:
                btn = entry["button"]
                icon = entry["icon"]
                has_image = bool(btn.cget("image"))
                label = entry["text"] if has_image else (
                    f"{icon.glyph()}  {entry['text']}" if icon else entry["text"])
                try:
                    btn.config(text=label)
                except tk.TclError:
                    continue
                self._paint_active(btn, container == self.active_button)
