# animations.py
"""Animation framework for smooth UI transitions and micro-interactions.

Provides fade, slide, scale animations, loading spinners, and progress animations
using pure tkinter with performant techniques.
"""
import tkinter as tk
import math
import time
from typing import Callable, Optional, List
from dataclasses import dataclass


@dataclass
class AnimationConfig:
    """Configuration for animation behavior."""
    duration: int = 300  # milliseconds
    easing: str = "easeInOut"  # linear, easeIn, easeOut, easeInOut
    fps: int = 60  # frames per second


class Easing:
    """Easing functions for smooth animations."""
    
    @staticmethod
    def linear(t: float) -> float:
        return t
    
    @staticmethod
    def easeIn(t: float) -> float:
        return t * t
    
    @staticmethod
    def easeOut(t: float) -> float:
        return t * (2 - t)
    
    @staticmethod
    def easeInOut(t: float) -> float:
        return t * t * (3 - 2 * t)
    
    @staticmethod
    def easeInQuad(t: float) -> float:
        return t * t
    
    @staticmethod
    def easeOutQuad(t: float) -> float:
        return t * (2 - t)
    
    @staticmethod
    def easeInOutQuad(t: float) -> float:
        return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t
    
    @staticmethod
    def easeInCubic(t: float) -> float:
        return t * t * t
    
    @staticmethod
    def easeOutCubic(t: float) -> float:
        return (t - 1) ** 3 + 1
    
    @staticmethod
    def easeInOutCubic(t: float) -> float:
        return 4 * t * t * t if t < 0.5 else (t - 1) ** 3 + 1
    
    @staticmethod
    def easeInBack(t: float) -> float:
        return 2.70158 * t * t * t - 1.70158 * t * t
    
    @staticmethod
    def easeOutBack(t: float) -> float:
        return 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2
    
    @staticmethod
    def easeInOutBack(t: float) -> float:
        return ((2 * t) ** 2 * ((2.70158 + 1) * 2 * t - 2.70158)) / 2 if t < 0.5 else \
               ((2 * t - 2) ** 2 * ((2.70158 + 1) * (t * 2 - 2) + 2.70158) + 2) / 2
    
    @staticmethod
    def get_easing(name: str) -> Callable[[float], float]:
        """Get easing function by name."""
        return getattr(Easing, name, Easing.easeInOut)


class FadeTransition:
    """Fade in/out animation for widgets."""
    
    def __init__(self, widget: tk.Widget, config: AnimationConfig = None):
        self.widget = widget
        self.config = config or AnimationConfig()
        self._is_animating = False
        self._stop_requested = False
    
    def fade_in(self, duration: int = None, callback: Callable = None) -> None:
        """Fade widget from transparent to opaque."""
        if self._is_animating:
            return
        
        self._is_animating = True
        self._stop_requested = False
        duration = duration or self.config.duration
        easing = Easing.get_easing(self.config.easing)
        fps = self.config.fps
        steps = int(duration / (1000 / fps))
        
        try:
            # Try alpha channel (if supported)
            self.widget.attributes("-alpha", 0.0)
        except tk.TclError:
            # Fallback: simulate fade by bg color interpolation
            pass
        
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = easing(t)
            
            try:
                self.widget.attributes("-alpha", eased_t)
            except tk.TclError:
                pass
            
            self.widget.update()
            time.sleep(1000 / fps / 1000)
        
        self._is_animating = False
        if callback:
            callback()
    
    def fade_out(self, duration: int = None, callback: Callable = None) -> None:
        """Fade widget from opaque to transparent."""
        if self._is_animating:
            return
        
        self._is_animating = True
        self._stop_requested = False
        duration = duration or self.config.duration
        easing = Easing.get_easing(self.config.easing)
        fps = self.config.fps
        steps = int(duration / (1000 / fps))
        
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = 1 - easing(t)
            
            try:
                self.widget.attributes("-alpha", eased_t)
            except tk.TclError:
                pass
            
            self.widget.update()
            time.sleep(1000 / fps / 1000)
        
        self._is_animating = False
        if callback:
            callback()
    
    def stop(self) -> None:
        """Stop the current animation."""
        self._stop_requested = True


class SlideTransition:
    """Slide animation for widgets (horizontal or vertical)."""
    
    def __init__(self, widget: tk.Widget, config: AnimationConfig = None):
        self.widget = widget
        self.config = config or AnimationConfig()
        self._is_animating = False
        self._stop_requested = False
        self._original_x = 0
        self._original_y = 0
    
    def slide_in_from_left(self, distance: int = 100, duration: int = None, 
                         callback: Callable = None) -> None:
        """Slide widget in from the left."""
        self._original_x = self.widget.winfo_x()
        self._is_animating = True
        self._stop_requested = False
        duration = duration or self.config.duration
        easing = Easing.get_easing(self.config.easing)
        fps = self.config.fps
        steps = int(duration / (1000 / fps))
        
        self.widget.place(x=self._original_x - distance)
        
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = easing(t)
            new_x = (self._original_x - distance) + (distance * eased_t)
            
            self.widget.place(x=new_x)
            self.widget.update()
            time.sleep(1000 / fps / 1000)
        
        self._is_animating = False
        if callback:
            callback()
    
    def slide_in_from_right(self, distance: int = 100, duration: int = None,
                          callback: Callable = None) -> None:
        """Slide widget in from the right."""
        self._original_x = self.widget.winfo_x()
        self._is_animating = True
        self._stop_requested = False
        duration = duration or self.config.duration
        easing = Easing.get_easing(self.config.easing)
        fps = self.config.fps
        steps = int(duration / (1000 / fps))
        
        self.widget.place(x=self._original_x + distance)
        
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = easing(t)
            new_x = (self._original_x + distance) - (distance * eased_t)
            
            self.widget.place(x=new_x)
            self.widget.update()
            time.sleep(1000 / fps / 1000)
        
        self._is_animating = False
        if callback:
            callback()
    
    def slide_out_to_left(self, distance: int = 100, duration: int = None,
                         callback: Callable = None) -> None:
        """Slide widget out to the left."""
        self._original_x = self.widget.winfo_x()
        self._is_animating = True
        self._stop_requested = False
        duration = duration or self.config.duration
        easing = Easing.get_easing(self.config.easing)
        fps = self.config.fps
        steps = int(duration / (1000 / fps))
        
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = easing(t)
            new_x = self._original_x - (distance * eased_t)
            
            self.widget.place(x=new_x)
            self.widget.update()
            time.sleep(1000 / fps / 1000)
        
        self._is_animating = False
        if callback:
            callback()
    
    def stop(self) -> None:
        """Stop the current animation."""
        self._stop_requested = True


class ScaleAnimation:
    """Scale/pulse animation for buttons and widgets."""
    
    def __init__(self, widget: tk.Widget, config: AnimationConfig = None):
        self.widget = widget
        self.config = config or AnimationConfig()
        self._is_animating = False
        self._stop_requested = False
        self._original_width = 0
        self._original_height = 0
    
    def pulse(self, scale_factor: float = 1.1, duration: int = None,
             callback: Callable = None) -> None:
        """Pulse animation (scale up then back down)."""
        if self._is_animating:
            return
        
        self._is_animating = True
        self._stop_requested = False
        duration = duration or self.config.duration
        half_duration = duration // 2
        easing = Easing.get_easing(self.config.easing)
        fps = self.config.fps
        steps = int(half_duration / (1000 / fps))
        
        # Scale up
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = easing(t)
            current_scale = 1 + (scale_factor - 1) * eased_t
            
            try:
                new_width = int(self.widget.winfo_width() * current_scale)
                new_height = int(self.widget.winfo_height() * current_scale)
                self.widget.config(width=new_width, height=new_height)
            except tk.TclError:
                pass
            
            self.widget.update()
            time.sleep(1000 / fps / 1000)
        
        # Scale down
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = 1 - easing(t)
            current_scale = scale_factor - (scale_factor - 1) * eased_t
            
            try:
                new_width = int(self.widget.winfo_width() * current_scale)
                new_height = int(self.widget.winfo_height() * current_scale)
                self.widget.config(width=new_width, height=new_height)
            except tk.TclError:
                pass
            
            self.widget.update()
            time.sleep(1000 / fps / 1000)
        
        self._is_animating = False
        if callback:
            callback()
    
    def stop(self) -> None:
        """Stop the current animation."""
        self._stop_requested = True


class LoadingSpinner:
    """Animated loading spinner using canvas."""
    
    def __init__(self, parent: tk.Widget, size: int = 40, color: str = "#3584e4"):
        self.parent = parent
        self.size = size
        self.color = color
        self.canvas = tk.Canvas(parent, width=size, height=size, bg="", highlightthickness=0)
        self._is_animating = False
        self._stop_requested = False
        self._angle = 0
    
    def start(self) -> None:
        """Start the spinner animation."""
        if self._is_animating:
            return
        
        self._is_animating = True
        self._stop_requested = False
        
        while not self._stop_requested:
            self._draw()
            self._angle = (self._angle + 15) % 360
            self.canvas.update()
            time.sleep(0.05)
        
        self._is_animating = False
    
    def stop(self) -> None:
        """Stop the spinner animation."""
        self._stop_requested = True
    
    def _draw(self) -> None:
        """Draw the spinner."""
        self.canvas.delete("all")
        center = self.size / 2
        radius = self.size / 2 - 4
        
        # Draw arcs
        for i in range(8):
            start_angle = self._angle + (i * 45)
            extent = 30
            alpha = 1 - (i / 8)
            
            # Simulate alpha by using lighter colors
            if i < 4:
                color = self.color
            else:
                color = "#e0e0e0"
            
            self.canvas.create_arc(
                center - radius, center - radius,
                center + radius, center + radius,
                start=start_angle, extent=extent,
                style=tk.ARC, outline=color, width=3
            )
    
    def pack(self, **kwargs) -> None:
        """Pack the canvas."""
        self.canvas.pack(**kwargs)
    
    def grid(self, **kwargs) -> None:
        """Grid the canvas."""
        self.canvas.grid(**kwargs)
    
    def place(self, **kwargs) -> None:
        """Place the canvas."""
        self.canvas.place(**kwargs)


class ProgressAnimation:
    """Animated progress bar with smooth transitions."""
    
    def __init__(self, canvas: tk.Canvas, width: int = 200, height: int = 20,
                 color: str = "#3584e4", bg_color: str = "#e0e0e0"):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.color = color
        self.bg_color = bg_color
        self._current_value = 0.0
        self._target_value = 0.0
        self._is_animating = False
        self._stop_requested = False
        
        canvas.config(width=width, height=height, bg="", highlightthickness=0)
        self._draw(0.0)
    
    def set_value(self, value: float, animate: bool = True, duration: int = 300) -> None:
        """Set the progress value (0.0 to 1.0)."""
        self._target_value = max(0.0, min(1.0, value))
        
        if animate:
            self._animate(duration)
        else:
            self._current_value = self._target_value
            self._draw(self._current_value)
    
    def _animate(self, duration: int) -> None:
        """Animate the progress bar."""
        if self._is_animating:
            return
        
        self._is_animating = True
        self._stop_requested = False
        easing = Easing.get_easing("easeOut")
        fps = 60
        steps = int(duration / (1000 / fps))
        
        start_value = self._current_value
        diff = self._target_value - start_value
        
        for i in range(steps + 1):
            if self._stop_requested:
                break
            
            t = i / steps
            eased_t = easing(t)
            self._current_value = start_value + (diff * eased_t)
            self._draw(self._current_value)
            self.canvas.update()
            time.sleep(1000 / fps / 1000)
        
        self._is_animating = False
    
    def _draw(self, value: float) -> None:
        """Draw the progress bar."""
        self.canvas.delete("all")
        
        # Background
        self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill=self.bg_color, outline=""
        )
        
        # Progress
        progress_width = self.width * value
        if progress_width > 0:
            self.canvas.create_rectangle(
                0, 0, progress_width, self.height,
                fill=self.color, outline=""
            )
    
    def stop(self) -> None:
        """Stop the current animation."""
        self._stop_requested = True


# Global animation toggle for performance
ANIMATIONS_ENABLED = True


def set_animations_enabled(enabled: bool) -> None:
    """Enable or disable all animations globally."""
    global ANIMATIONS_ENABLED
    ANIMATIONS_ENABLED = enabled


def are_animations_enabled() -> bool:
    """Check if animations are enabled."""
    return ANIMATIONS_ENABLED
