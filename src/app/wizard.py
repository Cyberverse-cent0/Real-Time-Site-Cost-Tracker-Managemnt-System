# wizard.py
"""Multi-step wizard framework for guided workflows.

Provides a base Wizard class and WizardStep component for creating
step-by-step user interfaces with validation, progress tracking, and navigation.
"""
import tkinter as tk
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass

from .theme import theme, get_font, apply_button_style, apply_label_style, create_card_frame
from .widget_styles import apply_ctk_card_style, apply_ctk_button_style
from .animations import FadeTransition, SlideTransition, are_animations_enabled


@dataclass
class WizardStep:
    """Represents a single step in the wizard."""
    title: str
    description: str = ""
    can_skip: bool = False
    is_optional: bool = False


class Wizard:
    """Multi-step wizard component with navigation and validation."""
    
    def __init__(self, parent: tk.Widget, title: str = "Wizard",
                 on_complete: Callable = None, on_cancel: Callable = None):
        self.parent = parent
        self.title = title
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        
        self.steps: List[WizardStep] = []
        self.current_step_index = 0
        self.step_widgets: Dict[int, tk.Widget] = {}
        self.step_validators: Dict[int, Callable] = {}
        self.step_data: Dict[int, Dict[str, Any]] = {}
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Build the wizard UI."""
        colors = theme.colors
        spacing = theme.spacing
        
        # Main container
        self.container = create_card_frame(self.parent)
        self.container.pack(fill="both", expand=True, padx=spacing.xl, pady=spacing.xl)
        apply_ctk_card_style(self.container, shadow="md", corner_radius="lg")
        
        # Header
        self.header = tk.Frame(self.container, bg=colors.bg_card)
        self.header.pack(fill="x", padx=spacing.xl, pady=(spacing.lg, spacing.md))
        
        self.title_label = tk.Label(
            self.header,
            text=self.title,
            bg=colors.bg_card
        )
        apply_label_style(self.title_label, variant="title")
        self.title_label.pack(anchor="w")
        
        # Progress indicator
        self.progress_frame = tk.Frame(self.header, bg=colors.bg_card)
        self.progress_frame.pack(fill="x", pady=(spacing.sm, 0))
        
        # Step content area
        self.content_frame = tk.Frame(self.container, bg=colors.bg_card)
        self.content_frame.pack(fill="both", expand=True, padx=spacing.xl, pady=spacing.md)
        
        # Navigation buttons
        self.nav_frame = tk.Frame(self.container, bg=colors.bg_card)
        self.nav_frame.pack(fill="x", padx=spacing.xl, pady=(spacing.md, spacing.lg))
        
        # Navigation buttons
        self.back_btn = tk.Button(
            self.nav_frame,
            text="Back",
            command=self._on_back
        )
        apply_ctk_button_style(self.back_btn, variant="ghost", size="medium")
        self.back_btn.pack(side="left", padx=spacing.xs)
        
        self.next_btn = tk.Button(
            self.nav_frame,
            text="Next",
            command=self._on_next
        )
        apply_ctk_button_style(self.next_btn, variant="primary", size="medium")
        self.next_btn.pack(side="right", padx=spacing.xs)
        
        self.cancel_btn = tk.Button(
            self.nav_frame,
            text="Cancel",
            command=self._on_cancel
        )
        apply_ctk_button_style(self.cancel_btn, variant="ghost", size="medium")
        self.cancel_btn.pack(side="right", padx=spacing.xs)
        
        self.finish_btn = tk.Button(
            self.nav_frame,
            text="Finish",
            command=self._on_finish
        )
        apply_ctk_button_style(self.finish_btn, variant="success", size="medium")
        # Finish button hidden initially
        self.finish_btn.pack_forget()
    
    def add_step(self, step: WizardStep, content_widget: tk.Widget,
                validator: Callable = None) -> None:
        """Add a step to the wizard.
        
        Args:
            step: WizardStep object with title and description
            content_widget: Widget to display for this step
            validator: Optional validation function that returns (valid, error_message)
        """
        step_index = len(self.steps)
        self.steps.append(step)
        self.step_widgets[step_index] = content_widget
        self.step_validators[step_index] = validator
        self.step_data[step_index] = {}
        
        content_widget.pack_forget()  # Don't show yet
        
        # Update progress indicator
        self._update_progress()
    
    def _update_progress(self) -> None:
        """Update the progress indicator."""
        colors = theme.colors
        spacing = theme.spacing
        
        # Clear existing progress
        for widget in self.progress_frame.winfo_children():
            widget.destroy()
        
        # Create progress dots
        for i, step in enumerate(self.steps):
            dot = tk.Frame(
                self.progress_frame,
                width=12,
                height=12,
                bg=colors.primary if i == self.current_step_index else colors.border,
                highlightthickness=0
            )
            dot.pack(side="left", padx=spacing.xs)
            
            if i < len(self.steps) - 1:
                line = tk.Frame(
                    self.progress_frame,
                    width=20,
                    height=2,
                    bg=colors.primary if i < self.current_step_index else colors.border
                )
                line.pack(side="left", padx=spacing.xs)
        
        # Update step title
        if self.steps:
            current_step = self.steps[self.current_step_index]
            self.title_label.config(text=f"{self.title} - {current_step.title}")
    
    def show_step(self, step_index: int) -> None:
        """Show a specific step."""
        if step_index < 0 or step_index >= len(self.steps):
            return
        
        # Hide current step
        if self.current_step_index in self.step_widgets:
            self.step_widgets[self.current_step_index].pack_forget()
        
        # Show new step
        self.current_step_index = step_index
        self.step_widgets[step_index].pack(fill="both", expand=True)
        
        # Update progress
        self._update_progress()
        
        # Update navigation buttons
        self._update_nav_buttons()
        
        # Animate if enabled
        if are_animations_enabled():
            fade = FadeTransition(self.step_widgets[step_index])
            fade.fade_in(duration=200)
    
    def _update_nav_buttons(self) -> None:
        """Update navigation button states."""
        # Hide/show back button
        if self.current_step_index == 0:
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(side="left", padx=spacing.xs)
        
        # Show next or finish button
        if self.current_step_index == len(self.steps) - 1:
            self.next_btn.pack_forget()
            self.finish_btn.pack(side="right", padx=spacing.xs)
        else:
            self.finish_btn.pack_forget()
            self.next_btn.pack(side="right", padx=spacing.xs)
    
    def _on_back(self) -> None:
        """Handle back button click."""
        if self.current_step_index > 0:
            if are_animations_enabled():
                fade = FadeTransition(self.step_widgets[self.current_step_index])
                fade.fade_out(duration=150, callback=lambda: self.show_step(self.current_step_index - 1))
            else:
                self.show_step(self.current_step_index - 1)
    
    def _on_next(self) -> None:
        """Handle next button click."""
        # Validate current step
        if self.current_step_index in self.step_validators:
            validator = self.step_validators[self.current_step_index]
            if validator:
                valid, error_message = validator(self.step_data[self.current_step_index])
                if not valid:
                    self._show_error(error_message)
                    return
        
        # Move to next step
        if self.current_step_index < len(self.steps) - 1:
            if are_animations_enabled():
                fade = FadeTransition(self.step_widgets[self.current_step_index])
                fade.fade_out(duration=150, callback=lambda: self.show_step(self.current_step_index + 1))
            else:
                self.show_step(self.current_step_index + 1)
    
    def _on_finish(self) -> None:
        """Handle finish button click."""
        # Validate final step
        if self.current_step_index in self.step_validators:
            validator = self.step_validators[self.current_step_index]
            if validator:
                valid, error_message = validator(self.step_data[self.current_step_index])
                if not valid:
                    self._show_error(error_message)
                    return
        
        # Call completion callback
        if self.on_complete:
            self.on_complete(self.step_data)
    
    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if self.on_cancel:
            self.on_cancel()
        else:
            # Default: destroy wizard
            self.container.destroy()
    
    def _show_error(self, message: str) -> None:
        """Show an error message."""
        colors = theme.colors
        spacing = theme.spacing
        
        # Remove existing error label
        for widget in self.nav_frame.winfo_children():
            if hasattr(widget, '_is_error_label'):
                widget.destroy()
        
        # Add error label
        error_label = tk.Label(
            self.nav_frame,
            text=message,
            bg=colors.bg_card,
            fg=colors.error
        )
        apply_label_style(error_label, variant="caption")
        error_label.pack(side="top", pady=(0, spacing.sm))
        error_label._is_error_label = True
    
    def get_step_data(self, step_index: int = None) -> Dict[str, Any]:
        """Get data for a specific step (or current step if not specified)."""
        if step_index is None:
            step_index = self.current_step_index
        return self.step_data.get(step_index, {})
    
    def set_step_data(self, data: Dict[str, Any], step_index: int = None) -> None:
        """Set data for a specific step (or current step if not specified)."""
        if step_index is None:
            step_index = self.current_step_index
        self.step_data[step_index] = data
    
    def start(self) -> None:
        """Start the wizard by showing the first step."""
        if self.steps:
            self.show_step(0)
