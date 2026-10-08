# main_windows.py
import tkinter as tk
from dataclasses import dataclass


@dataclass
class WindowGeometry:
    width: int
    height: int
    x: int
    y: int


# ---- Defaults for the app ----
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800


# ---- Single root for the whole app ----
root = tk.Tk()
root.title("Site Cost Tracker - Login")
root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
root.minsize(900, 600)


def get_geometry() -> WindowGeometry:
    """
    Detect the *current* geometry of the root window.

    IMPORTANT: requires update_idletasks() so Tk has actually laid
    out the window. Otherwise returns 1x1+0+0.
    """
    root.update_idletasks()
    geom = root.winfo_geometry()           # e.g. "800x600+120+80"
    size, x_str, y_str = geom.split("+", 2)  # split only first two '+'
    width, height = map(int, size.split("x"))
    x = int(x_str)
    y = int(y_str)
    return WindowGeometry(width=width, height=height, x=x, y=y)


def get_screen_size() -> tuple[int, int]:
    """Return the monitor's resolution."""
    return root.winfo_screenwidth(), root.winfo_screenheight()


def set_window_geometry(width: int, height: int) -> None:
    """Resize the window to the given dimensions (keeps position)."""
    current = get_geometry()
    root.geometry(f"{width}x{height}+{current.x}+{current.y}")
    root.update_idletasks()


def center_window(width: int, height: int) -> None:
    """Center the window on the screen with the given size."""
    screen_w, screen_h = get_screen_size()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.update_idletasks()


def center_on_screen() -> None:
    """Center the *existing* window (keeps current size)."""
    g = get_geometry()
    center_window(g.width, g.height)


# ---- Helpers used by other modules ----
def set_window_title(title: str) -> None:
    root.title(title)


def get_root() -> tk.Tk:
    return root


def clear_root() -> None:
    for widget in root.winfo_children():
        widget.destroy()


def run() -> None:
    root.mainloop()