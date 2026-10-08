# preferences_ui.py
"""
UI for the comprehensive preferences system.
Provides a settings page with all preference categories.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from .theme import theme, get_font, apply_button_style, apply_label_style, create_card_frame, refresh_theme
from ui.context_menu import attach_entry_menu
from .preferences import (
    PreferencesEngine,
    ThemeMode,
    ColorScheme,
    UIDensity,
    IconSize,
    ButtonSize,
    CornerRadius,
    FontFamily,
    MonospaceFont,
    SidebarBehavior,
    NotificationPosition,
)


class PreferencesPage:
    """Main preferences/settings page."""
    
    def __init__(self, parent: tk.Widget, preferences_engine: PreferencesEngine):
        self.parent = parent
        self.prefs_engine = preferences_engine
        self.colors = theme.colors
        self.spacing = theme.spacing
        
        # Main container
        self.main_container = tk.Frame(parent, bg=self.colors.bg_main)
        self.main_container.pack(fill="both", expand=True)
        
        # Split into sidebar (navigation) and content
        self._create_layout()
    
    def _create_layout(self):
        """Create the preferences page layout."""
        # Navigation sidebar
        nav_frame = tk.Frame(self.main_container, bg=self.colors.bg_sidebar, width=200)
        nav_frame.pack(side="left", fill="y")
        nav_frame.pack_propagate(False)
        
        # Content area
        self.content_frame = tk.Frame(self.main_container, bg=self.colors.bg_main)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Navigation items
        nav_items = [
            ("Appearance", self._show_appearance),
            ("Size & Density", self._show_size_density),
            ("Typography", self._show_typography),
            ("Interaction", self._show_interaction),
            ("Layout", self._show_layout),
            ("Notifications", self._show_notifications),
            ("Input", self._show_input),
            ("Accessibility", self._show_accessibility),
            ("Shape & Style", self._show_shape),
            ("Profiles", self._show_profiles),
        ]
        
        for text, callback in nav_items:
            btn = tk.Button(
                nav_frame,
                text=text,
                command=callback,
                bg=self.colors.bg_sidebar,
                fg=self.colors.text_light,
                activebackground=self.colors.primary,
                activeforeground=self.colors.text_white,
                relief="flat",
                anchor="w",
                padx=self.spacing.md,
                pady=self.spacing.sm,
                font=get_font(theme.fonts.body_normal),
                cursor="hand2"
            )
            btn.pack(fill="x", padx=self.spacing.sm, pady=self.spacing.xs)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors.hover))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors.bg_sidebar))
        
        # Show default section
        self._show_appearance()
    
    def _clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _show_appearance(self):
        """Show appearance settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.appearance
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        # Title
        title = tk.Label(card, text="Appearance", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Theme selection
        self._create_section(card, "Theme Mode", [
            ("Light", ThemeMode.LIGHT),
            ("Dark", ThemeMode.DARK),
            ("System", ThemeMode.SYSTEM),
            ("AMOLED", ThemeMode.AMOLED),
            ("High Contrast", ThemeMode.HIGH_CONTRAST),
        ], prefs.theme, self._update_theme_mode)
        
        # Color scheme
        self._create_section(card, "Color Scheme", [
            ("Blue", ColorScheme.BLUE),
            ("Cyan", ColorScheme.CYAN),
            ("Purple", ColorScheme.PURPLE),
            ("Green", ColorScheme.GREEN),
            ("Orange", ColorScheme.ORANGE),
            ("Red", ColorScheme.RED),
        ], prefs.color_scheme, self._update_color_scheme)
        
        # Accent color
        self._create_color_picker(card, "Accent Color", prefs.accent_color, self._update_accent_color)
        
        # Contrast slider
        self._create_slider(card, "Contrast Level", 50, 200, prefs.contrast_level, self._update_contrast)
        
        # Apply button
        self._create_apply_button(card)
    
    def _show_size_density(self):
        """Show size and density settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.size
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Size & Density", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # UI Scale
        self._create_slider(card, "UI Scale (%)", 75, 150, prefs.ui_scale, self._update_ui_scale)
        
        # Density
        self._create_section(card, "UI Density", [
            ("Compact", UIDensity.COMPACT),
            ("Normal", UIDensity.NORMAL),
            ("Spacious", UIDensity.SPACIOUS),
        ], prefs.density, self._update_density)
        
        # Icon size
        self._create_section(card, "Icon Size", [
            ("Small", IconSize.SMALL),
            ("Medium", IconSize.MEDIUM),
            ("Large", IconSize.LARGE),
        ], prefs.icon_size, self._update_icon_size)
        
        # Button size
        self._create_section(card, "Button Size", [
            ("Small", ButtonSize.SMALL),
            ("Medium", ButtonSize.MEDIUM),
            ("Large", ButtonSize.LARGE),
        ], prefs.button_size, self._update_button_size)
        
        # Text size multiplier
        self._create_slider(card, "Text Size Multiplier", 0.5, 2.0, prefs.text_size_multiplier, self._update_text_size, step=0.1)
        
        self._create_apply_button(card)
    
    def _show_typography(self):
        """Show typography settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.typography
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Typography", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Font family
        self._create_section(card, "Font Family", [
            ("Inter", FontFamily.INTER),
            ("Roboto", FontFamily.ROBOTO),
            ("Noto Sans", FontFamily.NOTO_SANS),
            ("System UI", FontFamily.SYSTEM_UI),
            ("IBM Plex Sans", FontFamily.IBM_PLEX),
        ], prefs.font_family, self._update_font_family)
        
        # Font size
        self._create_slider(card, "Base Font Size", 8, 24, prefs.font_size, self._update_font_size)
        
        # Font weight
        self._create_section(card, "Font Weight", [
            ("Normal", "normal"),
            ("Bold", "bold"),
        ], prefs.font_weight, self._update_font_weight)
        
        # Line height
        self._create_slider(card, "Line Height", 1.0, 2.5, prefs.line_height, self._update_line_height, step=0.1)
        
        # Letter spacing
        self._create_slider(card, "Letter Spacing", -0.5, 1.0, prefs.letter_spacing, self._update_letter_spacing, step=0.05)
        
        # Monospace font
        self._create_section(card, "Monospace Font", [
            ("JetBrains Mono", MonospaceFont.JETBRAINS),
            ("Fira Code", MonospaceFont.FIRA_CODE),
            ("Consolas", MonospaceFont.CONSOLAS),
            ("Monaco", MonospaceFont.MONACO),
        ], prefs.monospace_font, self._update_monospace_font)
        
        self._create_apply_button(card)
    
    def _show_interaction(self):
        """Show interaction settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.interaction
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Interaction & Animation", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Toggles
        toggles = [
            ("Hover Effects", prefs.hover_effects, self._update_hover_effects),
            ("Click Feedback", prefs.click_feedback, self._update_click_feedback),
            ("Ripple Effect", prefs.ripple_effect, self._update_ripple_effect),
            ("Page Transitions", prefs.page_transitions, self._update_page_transitions),
            ("Tooltips", prefs.tooltips, self._update_tooltips),
            ("Animated Icons", prefs.animated_icons, self._update_animated_icons),
            ("Drag Feedback", prefs.drag_feedback, self._update_drag_feedback),
            ("Loading Animations", prefs.loading_animations, self._update_loading_animations),
        ]
        
        for label_text, current_value, callback in toggles:
            self._create_toggle(card, label_text, current_value, callback)
        
        # Animation speed
        self._create_slider(card, "Animation Speed", 0.5, 2.0, prefs.animation_speed, self._update_animation_speed, step=0.1)
        
        self._create_apply_button(card)
    
    def _show_layout(self):
        """Show layout settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.layout
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Layout", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Sidebar behavior
        self._create_section(card, "Sidebar Behavior", [
            ("Expanded", SidebarBehavior.EXPANDED),
            ("Collapsed", SidebarBehavior.COLLAPSED),
            ("Auto-hide", SidebarBehavior.AUTO_HIDE),
        ], prefs.sidebar_behavior, self._update_sidebar_behavior)
        
        # Menu trigger
        self._create_section(card, "Menu Trigger", [
            ("Click", "click"),
            ("Hover", "hover"),
        ], prefs.menu_trigger, self._update_menu_trigger)
        
        # Dialog position
        self._create_section(card, "Dialog Position", [
            ("Center", "center"),
            ("Side Panel", "side"),
        ], prefs.dialog_position, self._update_dialog_position)
        
        # Table density
        self._create_section(card, "Table Density", [
            ("Compact", UIDensity.COMPACT),
            ("Normal", UIDensity.NORMAL),
            ("Spacious", UIDensity.SPACIOUS),
        ], prefs.table_density, self._update_table_density)
        
        # Content width
        self._create_section(card, "Content Width", [
            ("Narrow", "narrow"),
            ("Normal", "normal"),
            ("Wide", "wide"),
        ], prefs.content_width, self._update_content_width)
        
        self._create_apply_button(card)
    
    def _show_notifications(self):
        """Show notification settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.notifications
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Notifications", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Toggles
        toggles = [
            ("Show Notifications", prefs.show_notifications, self._update_show_notifications),
            ("Sound Enabled", prefs.sound_enabled, self._update_sound_enabled),
            ("Desktop Notifications", prefs.desktop_notifications, self._update_desktop_notifications),
            ("Show Success", prefs.show_success, self._update_show_success),
            ("Show Errors", prefs.show_errors, self._update_show_errors),
            ("Show Warnings", prefs.show_warnings, self._update_show_warnings),
            ("Show Info", prefs.show_info, self._update_show_info),
            ("Background Notifications", prefs.background_notifications, self._update_background_notifications),
        ]
        
        for label_text, current_value, callback in toggles:
            self._create_toggle(card, label_text, current_value, callback)
        
        # Position
        self._create_section(card, "Notification Position", [
            ("Bottom Right", NotificationPosition.BOTTOM_RIGHT),
            ("Top Right", NotificationPosition.TOP_RIGHT),
            ("Top Center", NotificationPosition.TOP_CENTER),
        ], prefs.position, self._update_notification_position)
        
        # Duration
        self._create_slider(card, "Duration (seconds)", 1, 10, prefs.duration, self._update_notification_duration)
        
        self._create_apply_button(card)
    
    def _show_input(self):
        """Show input settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.input
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Input Preferences", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Focus style
        self._create_section(card, "Focus Style", [
            ("Minimal", "minimal"),
            ("Standard", "standard"),
            ("Strong", "strong"),
        ], prefs.focus_style, self._update_focus_style)
        
        # Toggles
        toggles = [
            ("Autocomplete", prefs.autocomplete, self._update_autocomplete),
            ("Spell Checking", prefs.spell_checking, self._update_spell_checking),
            ("Password Reveal", prefs.password_reveal, self._update_password_reveal),
            ("Clear Buttons", prefs.clear_buttons, self._update_clear_buttons),
        ]
        
        for label_text, current_value, callback in toggles:
            self._create_toggle(card, label_text, current_value, callback)
        
        # Enter key behavior
        self._create_section(card, "Enter Key Behavior", [
            ("Submit", "submit"),
            ("New Line", "newline"),
        ], prefs.enter_key_behavior, self._update_enter_key_behavior)
        
        # Tab behavior
        self._create_section(card, "Tab Behavior", [
            ("Focus Fields", "focus"),
            ("Indent Text", "indent"),
        ], prefs.tab_behavior, self._update_tab_behavior)
        
        self._create_apply_button(card)
    
    def _show_accessibility(self):
        """Show accessibility settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.accessibility
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Accessibility", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Toggles
        toggles = [
            ("High Contrast", prefs.high_contrast, self._update_high_contrast),
            ("Larger Text", prefs.larger_text, self._update_larger_text),
            ("Reduce Motion", prefs.reduce_motion, self._update_reduce_motion),
            ("Always Show Focus", prefs.always_show_focus, self._update_always_show_focus),
            ("Larger Click Targets", prefs.larger_click_targets, self._update_larger_click_targets),
            ("Screen Reader Optimized", prefs.screen_reader_optimized, self._update_screen_reader_optimized),
            ("Disable Transparency", prefs.disable_transparency, self._update_disable_transparency),
        ]
        
        for label_text, current_value, callback in toggles:
            self._create_toggle(card, label_text, current_value, callback)
        
        # Color blind mode
        self._create_section(card, "Color Blind Mode", [
            ("None", None),
            ("Protanopia", "protanopia"),
            ("Deuteranopia", "deuteranopia"),
            ("Tritanopia", "tritanopia"),
        ], prefs.color_blind_mode, self._update_color_blind_mode)
        
        self._create_apply_button(card)
    
    def _show_shape(self):
        """Show shape and style settings."""
        self._clear_content()
        prefs = self.prefs_engine.preferences.shape
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Shape & Style", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Corner radius
        self._create_section(card, "Corner Radius", [
            ("Sharp", CornerRadius.SHARP),
            ("Small", CornerRadius.SMALL),
            ("Medium", CornerRadius.MEDIUM),
            ("Large", CornerRadius.LARGE),
            ("Pill", CornerRadius.PILL),
        ], prefs.corner_radius, self._update_corner_radius)
        
        # Toggles
        toggles = [
            ("Border Visible", prefs.border_visible, self._update_border_visible),
            ("Shadow Enabled", prefs.shadow_enabled, self._update_shadow_enabled),
        ]
        
        for label_text, current_value, callback in toggles:
            self._create_toggle(card, label_text, current_value, callback)
        
        # Elevation
        self._create_slider(card, "Elevation", 0, 4, prefs.elevation, self._update_elevation)
        
        # Card style
        self._create_section(card, "Card Style", [
            ("Flat", "flat"),
            ("Elevated", "elevated"),
            ("Outlined", "outlined"),
        ], prefs.card_style, self._update_card_style)
        
        # Input style
        self._create_section(card, "Input Style", [
            ("Filled", "filled"),
            ("Outlined", "outlined"),
            ("Underlined", "underlined"),
        ], prefs.input_style, self._update_input_style)
        
        self._create_apply_button(card)
    
    def _show_profiles(self):
        """Show profile management."""
        self._clear_content()
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=self.spacing.lg, pady=self.spacing.lg)
        
        title = tk.Label(card, text="Preference Profiles", bg=self.colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(pady=self.spacing.lg, padx=self.spacing.lg)
        
        # Predefined profiles
        predefined_frame = tk.Frame(card, bg=self.colors.bg_card)
        predefined_frame.pack(fill="x", padx=self.spacing.lg, pady=self.spacing.md)
        
        tk.Label(predefined_frame, text="Predefined Profiles", bg=self.colors.bg_card).pack(anchor="w")
        
        profiles = [
            ("Default", "default"),
            ("Compact", "compact"),
            ("Developer", "developer"),
            ("Accessibility", "accessibility"),
        ]
        
        for name, profile_id in profiles:
            btn = tk.Button(
                predefined_frame,
                text=f"Apply {name}",
                command=lambda p=profile_id: self._apply_profile(p),
            )
            apply_button_style(btn, variant="outline")
            btn.pack(fill="x", pady=self.spacing.xs)
        
        # Custom profiles
        custom_frame = tk.Frame(card, bg=self.colors.bg_card)
        custom_frame.pack(fill="x", padx=self.spacing.lg, pady=self.spacing.lg)
        
        tk.Label(custom_frame, text="Custom Profiles", bg=self.colors.bg_card).pack(anchor="w")
        
        # Save current as profile
        save_frame = tk.Frame(custom_frame, bg=self.colors.bg_card)
        save_frame.pack(fill="x", pady=self.spacing.sm)
        
        profile_name_var = tk.StringVar()
        profile_name_entry = tk.Entry(save_frame, textvariable=profile_name_var)
        profile_name_entry.pack(side="left", fill="x", expand=True, padx=(0, self.spacing.xs))
        attach_entry_menu(profile_name_entry)
        
        save_btn = tk.Button(save_frame, text="Save as Profile", command=lambda: self._save_as_profile(profile_name_var.get()))
        apply_button_style(save_btn, variant="primary")
        save_btn.pack(side="left")
        
        # List custom profiles
        for profile_name in self.prefs_engine.preferences.custom_profiles.keys():
            profile_frame = tk.Frame(custom_frame, bg=self.colors.bg_card)
            profile_frame.pack(fill="x", pady=self.spacing.xs)
            
            tk.Label(profile_frame, text=profile_name, bg=self.colors.bg_card).pack(side="left")
            
            apply_btn = tk.Button(profile_frame, text="Apply", command=lambda p=profile_name: self._apply_profile(p))
            apply_button_style(apply_btn, variant="outline", size="small")
            apply_btn.pack(side="right", padx=self.spacing.xs)
            
            delete_btn = tk.Button(profile_frame, text="Delete", command=lambda p=profile_name: self._delete_profile(p))
            apply_button_style(delete_btn, variant="danger", size="small")
            delete_btn.pack(side="right")
    
    # Helper methods for creating UI components
    
    def _create_section(self, parent: tk.Frame, title: str, options: list[tuple[str, any]], current_value, callback):
        """Create a radio button section."""
        section = tk.Frame(parent, bg=self.colors.bg_card)
        section.pack(fill="x", padx=self.spacing.lg, pady=self.spacing.md)
        
        tk.Label(section, text=title, bg=self.colors.bg_card).pack(anchor="w")
        
        var = tk.StringVar(value=current_value.value if hasattr(current_value, 'value') else str(current_value))
        
        for label, value in options:
            rb = tk.Radiobutton(
                section,
                text=label,
                variable=var,
                value=value.value if hasattr(value, 'value') else str(value),
                bg=self.colors.bg_card,
                fg=self.colors.text_primary,
                selectcolor=self.colors.bg_main,
                activebackground=self.colors.bg_card,
                activeforeground=self.colors.text_primary,
                command=lambda v=value: callback(v)
            )
            rb.pack(anchor="w", padx=self.spacing.md)
    
    def _create_toggle(self, parent: tk.Frame, label: str, current_value: bool, callback):
        """Create a toggle switch."""
        frame = tk.Frame(parent, bg=self.colors.bg_card)
        frame.pack(fill="x", padx=self.spacing.lg, pady=self.spacing.sm)
        
        var = tk.BooleanVar(value=current_value)
        
        cb = tk.Checkbutton(
            frame,
            text=label,
            variable=var,
            bg=self.colors.bg_card,
            fg=self.colors.text_primary,
            selectcolor=self.colors.bg_main,
            activebackground=self.colors.bg_card,
            activeforeground=self.colors.text_primary,
            command=lambda: callback(var.get())
        )
        cb.pack(anchor="w")
    
    def _create_slider(self, parent: tk.Frame, label: str, min_val: float, max_val: float, current_value: float, callback, step: float = 1):
        """Create a slider."""
        frame = tk.Frame(parent, bg=self.colors.bg_card)
        frame.pack(fill="x", padx=self.spacing.lg, pady=self.spacing.md)
        
        tk.Label(frame, text=label, bg=self.colors.bg_card).pack(anchor="w")
        
        var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            orient="horizontal",
            variable=var,
            bg=self.colors.bg_card,
            fg=self.colors.text_primary,
            resolution=step,
            command=lambda v: callback(float(v))
        )
        slider.pack(fill="x")
    
    def _create_color_picker(self, parent: tk.Frame, label: str, current_color: str, callback):
        """Create a color picker (simplified)."""
        frame = tk.Frame(parent, bg=self.colors.bg_card)
        frame.pack(fill="x", padx=self.spacing.lg, pady=self.spacing.md)
        
        tk.Label(frame, text=label, bg=self.colors.bg_card).pack(anchor="w")
        
        var = tk.StringVar(value=current_color)
        
        entry = tk.Entry(frame, textvariable=var)
        entry.pack(fill="x", padx=self.spacing.md)
        attach_entry_menu(entry)
        
        btn = tk.Button(frame, text="Apply", command=lambda: callback(var.get()))
        apply_button_style(btn, variant="primary", size="small")
        btn.pack(pady=self.spacing.xs)
    
    def _create_apply_button(self, parent: tk.Frame):
        """Create an apply button at the bottom."""
        btn_frame = tk.Frame(parent, bg=self.colors.bg_card)
        btn_frame.pack(fill="x", padx=self.spacing.lg, pady=self.spacing.lg)
        
        apply_btn = tk.Button(btn_frame, text="Apply Changes", command=self._apply_changes)
        apply_button_style(apply_btn, variant="primary", size="large")
        apply_btn.pack(side="right")
        
        reset_btn = tk.Button(btn_frame, text="Reset to Default", command=self._reset_to_default)
        apply_button_style(reset_btn, variant="outline", size="large")
        reset_btn.pack(side="right", padx=self.spacing.xs)
    
    # Callback methods for preference updates
    
    def _update_theme_mode(self, value):
        self.prefs_engine.preferences.appearance.theme = value
    
    def _update_color_scheme(self, value):
        self.prefs_engine.preferences.appearance.color_scheme = value
    
    def _update_accent_color(self, value):
        self.prefs_engine.preferences.appearance.accent_color = value
    
    def _update_contrast(self, value):
        self.prefs_engine.preferences.appearance.contrast_level = int(value)
    
    def _update_ui_scale(self, value):
        self.prefs_engine.preferences.size.ui_scale = int(value)
    
    def _update_density(self, value):
        self.prefs_engine.preferences.size.density = value
    
    def _update_icon_size(self, value):
        self.prefs_engine.preferences.size.icon_size = value
    
    def _update_button_size(self, value):
        self.prefs_engine.preferences.size.button_size = value
    
    def _update_text_size(self, value):
        self.prefs_engine.preferences.size.text_size_multiplier = value
    
    def _update_font_family(self, value):
        self.prefs_engine.preferences.typography.font_family = value
    
    def _update_font_size(self, value):
        self.prefs_engine.preferences.typography.font_size = int(value)
    
    def _update_font_weight(self, value):
        self.prefs_engine.preferences.typography.font_weight = value
    
    def _update_line_height(self, value):
        self.prefs_engine.preferences.typography.line_height = value
    
    def _update_letter_spacing(self, value):
        self.prefs_engine.preferences.typography.letter_spacing = value
    
    def _update_monospace_font(self, value):
        self.prefs_engine.preferences.typography.monospace_font = value
    
    def _update_hover_effects(self, value):
        self.prefs_engine.preferences.interaction.hover_effects = value
    
    def _update_click_feedback(self, value):
        self.prefs_engine.preferences.interaction.click_feedback = value
    
    def _update_ripple_effect(self, value):
        self.prefs_engine.preferences.interaction.ripple_effect = value
    
    def _update_page_transitions(self, value):
        self.prefs_engine.preferences.interaction.page_transitions = value
    
    def _update_tooltips(self, value):
        self.prefs_engine.preferences.interaction.tooltips = value
    
    def _update_animated_icons(self, value):
        self.prefs_engine.preferences.interaction.animated_icons = value
    
    def _update_drag_feedback(self, value):
        self.prefs_engine.preferences.interaction.drag_feedback = value
    
    def _update_loading_animations(self, value):
        self.prefs_engine.preferences.interaction.loading_animations = value
    
    def _update_animation_speed(self, value):
        self.prefs_engine.preferences.interaction.animation_speed = value
    
    def _update_sidebar_behavior(self, value):
        self.prefs_engine.preferences.layout.sidebar_behavior = value
    
    def _update_menu_trigger(self, value):
        self.prefs_engine.preferences.layout.menu_trigger = value
    
    def _update_dialog_position(self, value):
        self.prefs_engine.preferences.layout.dialog_position = value
    
    def _update_table_density(self, value):
        self.prefs_engine.preferences.layout.table_density = value
    
    def _update_content_width(self, value):
        self.prefs_engine.preferences.layout.content_width = value
    
    def _update_show_notifications(self, value):
        self.prefs_engine.preferences.notifications.show_notifications = value
    
    def _update_sound_enabled(self, value):
        self.prefs_engine.preferences.notifications.sound_enabled = value
    
    def _update_desktop_notifications(self, value):
        self.prefs_engine.preferences.notifications.desktop_notifications = value
    
    def _update_show_success(self, value):
        self.prefs_engine.preferences.notifications.show_success = value
    
    def _update_show_errors(self, value):
        self.prefs_engine.preferences.notifications.show_errors = value
    
    def _update_show_warnings(self, value):
        self.prefs_engine.preferences.notifications.show_warnings = value
    
    def _update_show_info(self, value):
        self.prefs_engine.preferences.notifications.show_info = value
    
    def _update_background_notifications(self, value):
        self.prefs_engine.preferences.notifications.background_notifications = value
    
    def _update_notification_position(self, value):
        self.prefs_engine.preferences.notifications.position = value
    
    def _update_notification_duration(self, value):
        self.prefs_engine.preferences.notifications.duration = int(value)
    
    def _update_focus_style(self, value):
        self.prefs_engine.preferences.input.focus_style = value
    
    def _update_autocomplete(self, value):
        self.prefs_engine.preferences.input.autocomplete = value
    
    def _update_spell_checking(self, value):
        self.prefs_engine.preferences.input.spell_checking = value
    
    def _update_password_reveal(self, value):
        self.prefs_engine.preferences.input.password_reveal = value
    
    def _update_clear_buttons(self, value):
        self.prefs_engine.preferences.input.clear_buttons = value
    
    def _update_enter_key_behavior(self, value):
        self.prefs_engine.preferences.input.enter_key_behavior = value
    
    def _update_tab_behavior(self, value):
        self.prefs_engine.preferences.input.tab_behavior = value
    
    def _update_high_contrast(self, value):
        self.prefs_engine.preferences.accessibility.high_contrast = value
    
    def _update_larger_text(self, value):
        self.prefs_engine.preferences.accessibility.larger_text = value
    
    def _update_reduce_motion(self, value):
        self.prefs_engine.preferences.accessibility.reduce_motion = value
    
    def _update_always_show_focus(self, value):
        self.prefs_engine.preferences.accessibility.always_show_focus = value
    
    def _update_larger_click_targets(self, value):
        self.prefs_engine.preferences.accessibility.larger_click_targets = value
    
    def _update_screen_reader_optimized(self, value):
        self.prefs_engine.preferences.accessibility.screen_reader_optimized = value
    
    def _update_disable_transparency(self, value):
        self.prefs_engine.preferences.accessibility.disable_transparency = value
    
    def _update_color_blind_mode(self, value):
        self.prefs_engine.preferences.accessibility.color_blind_mode = value
    
    def _update_corner_radius(self, value):
        self.prefs_engine.preferences.shape.corner_radius = value
    
    def _update_border_visible(self, value):
        self.prefs_engine.preferences.shape.border_visible = value
    
    def _update_shadow_enabled(self, value):
        self.prefs_engine.preferences.shape.shadow_enabled = value
    
    def _update_elevation(self, value):
        self.prefs_engine.preferences.shape.elevation = int(value)
    
    def _update_card_style(self, value):
        self.prefs_engine.preferences.shape.card_style = value
    
    def _update_input_style(self, value):
        self.prefs_engine.preferences.shape.input_style = value
    
    # Profile management
    
    def _apply_profile(self, profile_name: str):
        """Apply a preference profile."""
        if self.prefs_engine.apply_profile(profile_name):
            messagebox.showinfo("Success", f"Applied profile: {profile_name}")
            self._show_profiles()  # Refresh
        else:
            messagebox.showerror("Error", f"Failed to apply profile: {profile_name}")
    
    def _save_as_profile(self, profile_name: str):
        """Save current preferences as a custom profile."""
        if not profile_name:
            messagebox.showwarning("Warning", "Please enter a profile name.")
            return
        
        if self.prefs_engine.save_as_profile(profile_name):
            messagebox.showinfo("Success", f"Saved profile: {profile_name}")
            self._show_profiles()  # Refresh
        else:
            messagebox.showerror("Error", f"Failed to save profile: {profile_name}")
    
    def _delete_profile(self, profile_name: str):
        """Delete a custom profile."""
        if messagebox.askyesno("Confirm", f"Delete profile '{profile_name}'?"):
            if self.prefs_engine.delete_profile(profile_name):
                messagebox.showinfo("Success", f"Deleted profile: {profile_name}")
                self._show_profiles()  # Refresh
            else:
                messagebox.showerror("Error", f"Failed to delete profile: {profile_name}")
    
    def _apply_changes(self):
        """Apply all preference changes."""
        self.prefs_engine.save()
        refresh_theme()
        messagebox.showinfo("Success", "Preferences saved and applied!")
    
    def _reset_to_default(self):
        """Reset preferences to default."""
        if messagebox.askyesno("Confirm", "Reset all preferences to default?"):
            self.prefs_engine.apply_profile("default")
            self._show_appearance()  # Refresh to current section
            messagebox.showinfo("Success", "Preferences reset to default!")
