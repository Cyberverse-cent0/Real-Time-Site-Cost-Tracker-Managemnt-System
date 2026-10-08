# preferences.py
"""
Centralized UI Preferences System for Site Cost Tracker.

This module provides a comprehensive preference engine that controls:
- Appearance (theme, colors, contrast)
- Size & Density (UI scale, icon size, button size)
- Typography (font family, size, weight)
- Interaction (animations, hover effects, transitions)
- Layout (sidebar behavior, navigation)
- Notifications (position, duration, sounds)
- Accessibility (high contrast, reduce motion, screen reader)
"""
import dataclasses
import json
import pathlib
from typing import Optional, Literal
from enum import Enum
from copy import deepcopy


class ThemeMode(Enum):
    """Available theme modes."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
    AMOLED = "amoled"
    HIGH_CONTRAST = "high_contrast"


class ColorScheme(Enum):
    """Available color schemes."""
    BLUE = "blue"
    CYAN = "cyan"
    PURPLE = "purple"
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"
    CUSTOM = "custom"


class UIDensity(Enum):
    """UI density options."""
    COMPACT = "compact"
    NORMAL = "normal"
    SPACIOUS = "spacious"


class IconSize(Enum):
    """Icon size options."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ButtonSize(Enum):
    """Button size options."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class CornerRadius(Enum):
    """Corner radius options."""
    SHARP = "sharp"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    PILL = "pill"


class FontFamily(Enum):
    """Font family options."""
    INTER = "Inter"
    ROBOTO = "Roboto"
    NOTO_SANS = "Noto Sans"
    SYSTEM_UI = "System UI"
    IBM_PLEX = "IBM Plex Sans"


class MonospaceFont(Enum):
    """Monospace font options."""
    JETBRAINS = "JetBrains Mono"
    FIRA_CODE = "Fira Code"
    CONSOLAS = "Consolas"
    MONACO = "Monaco"


class SidebarBehavior(Enum):
    """Sidebar behavior options."""
    EXPANDED = "expanded"
    COLLAPSED = "collapsed"
    AUTO_HIDE = "auto_hide"


class NotificationPosition(Enum):
    """Notification position options."""
    BOTTOM_RIGHT = "bottom_right"
    TOP_RIGHT = "top_right"
    TOP_CENTER = "top_center"


@dataclasses.dataclass
class AppearancePreferences:
    """Appearance-related preferences."""
    theme: ThemeMode = ThemeMode.LIGHT
    color_scheme: ColorScheme = ColorScheme.BLUE
    accent_color: str = "#0ea5e9"
    background_color: str = "#f8fafc"
    surface_color: str = "#ffffff"
    text_color: str = "#0f172a"
    contrast_level: int = 100  # 0-200


@dataclasses.dataclass
class SizePreferences:
    """Size and density preferences."""
    ui_scale: int = 100  # 75-150
    density: UIDensity = UIDensity.NORMAL
    icon_size: IconSize = IconSize.MEDIUM
    button_size: ButtonSize = ButtonSize.MEDIUM
    text_size_multiplier: float = 1.0


@dataclasses.dataclass
class TypographyPreferences:
    """Typography preferences."""
    font_family: FontFamily = FontFamily.INTER
    font_size: int = 12  # Base font size
    font_weight: str = "normal"
    line_height: float = 1.5
    letter_spacing: float = 0.0
    monospace_font: MonospaceFont = MonospaceFont.JETBRAINS


@dataclasses.dataclass
class InteractionPreferences:
    """Interaction and animation preferences."""
    hover_effects: bool = True
    click_feedback: bool = True
    ripple_effect: bool = False
    page_transitions: bool = True
    tooltips: bool = True
    animated_icons: bool = True
    drag_feedback: bool = True
    loading_animations: bool = True
    animation_speed: float = 1.0  # 0.5-2.0


@dataclasses.dataclass
class LayoutPreferences:
    """Layout preferences."""
    sidebar_behavior: SidebarBehavior = SidebarBehavior.EXPANDED
    menu_trigger: Literal["click", "hover"] = "click"
    dialog_position: Literal["center", "side"] = "center"
    table_density: UIDensity = UIDensity.NORMAL
    content_width: Literal["narrow", "normal", "wide"] = "normal"


@dataclasses.dataclass
class NotificationPreferences:
    """Notification preferences."""
    show_notifications: bool = True
    sound_enabled: bool = False
    desktop_notifications: bool = False
    show_success: bool = True
    show_errors: bool = True
    show_warnings: bool = True
    show_info: bool = True
    background_notifications: bool = True
    position: NotificationPosition = NotificationPosition.BOTTOM_RIGHT
    duration: int = 4  # seconds


@dataclasses.dataclass
class InputPreferences:
    """Input field preferences."""
    focus_style: Literal["minimal", "standard", "strong"] = "standard"
    autocomplete: bool = True
    spell_checking: bool = True
    password_reveal: bool = True
    clear_buttons: bool = True
    enter_key_behavior: Literal["submit", "newline"] = "submit"
    tab_behavior: Literal["focus", "indent"] = "focus"


@dataclasses.dataclass
class AccessibilityPreferences:
    """Accessibility preferences."""
    high_contrast: bool = False
    larger_text: bool = False
    reduce_motion: bool = False
    always_show_focus: bool = False
    larger_click_targets: bool = False
    screen_reader_optimized: bool = False
    disable_transparency: bool = False
    color_blind_mode: Optional[Literal["protanopia", "deuteranopia", "tritanopia"]] = None


@dataclasses.dataclass
class ShapePreferences:
    """Shape and style preferences."""
    corner_radius: CornerRadius = CornerRadius.MEDIUM
    border_visible: bool = True
    shadow_enabled: bool = True
    elevation: int = 2  # 0-4
    card_style: Literal["flat", "elevated", "outlined"] = "elevated"
    input_style: Literal["filled", "outlined", "underlined"] = "outlined"


@dataclasses.dataclass
class UserPreferences:
    """Complete user preferences model."""
    appearance: AppearancePreferences = dataclasses.field(default_factory=AppearancePreferences)
    size: SizePreferences = dataclasses.field(default_factory=SizePreferences)
    typography: TypographyPreferences = dataclasses.field(default_factory=TypographyPreferences)
    interaction: InteractionPreferences = dataclasses.field(default_factory=InteractionPreferences)
    layout: LayoutPreferences = dataclasses.field(default_factory=LayoutPreferences)
    notifications: NotificationPreferences = dataclasses.field(default_factory=NotificationPreferences)
    input: InputPreferences = dataclasses.field(default_factory=InputPreferences)
    accessibility: AccessibilityPreferences = dataclasses.field(default_factory=AccessibilityPreferences)
    shape: ShapePreferences = dataclasses.field(default_factory=ShapePreferences)
    
    # Profile management
    current_profile: str = "default"
    custom_profiles: dict[str, dict] = dataclasses.field(default_factory=dict)


class PreferencesStorage:
    """Handles persistence of user preferences."""
    
    def __init__(self, username: str):
        self.username = username
        self.preferences_dir = pathlib.Path.home() / ".site_cost_tracker" / "preferences"
        self.preferences_file = self.preferences_dir / f"{username}.json"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create preferences directory if it doesn't exist."""
        self.preferences_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, preferences: UserPreferences, exclude_custom_profiles: bool = False) -> bool:
        """Save preferences to file."""
        try:
            # Convert to dict, handling Enums
            prefs_dict = self._preferences_to_dict(preferences, exclude_custom_profiles=exclude_custom_profiles)
            
            with open(self.preferences_file, "w") as f:
                json.dump(prefs_dict, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False
    
    def load(self) -> Optional[UserPreferences]:
        """Load preferences from file."""
        try:
            if not self.preferences_file.exists():
                return None
            
            with open(self.preferences_file, "r") as f:
                prefs_dict = json.load(f)
            
            # Convert None values to defaults for optional fields
            if 'color_blind_mode' in prefs_dict.get('accessibility', {}):
                if prefs_dict['accessibility']['color_blind_mode'] is None:
                    prefs_dict['accessibility']['color_blind_mode'] = None
            
            return self._dict_to_preferences(prefs_dict)
        except Exception as e:
            print(f"Error loading preferences: {e}")
            return None
    
    def _preferences_to_dict(self, prefs: UserPreferences, exclude_custom_profiles: bool = False) -> dict:
        """Convert UserPreferences to JSON-serializable dict."""
        def convert_value(value):
            """Recursively convert values to JSON-serializable types."""
            if isinstance(value, Enum):
                return value.value
            if dataclasses.is_dataclass(value):
                # Recursively convert dataclass fields
                return {k: convert_value(v) for k, v in dataclasses.asdict(value).items()}
            if isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [convert_value(v) for v in value]
            return value
        
        result = {}
        for field_name, field_value in dataclasses.asdict(prefs).items():
            # Skip custom_profiles if requested
            if exclude_custom_profiles and field_name == "custom_profiles":
                continue
            result[field_name] = convert_value(field_value)
        
        return result
    
    def _dict_to_preferences(self, prefs_dict: dict) -> UserPreferences:
        """Convert dict back to UserPreferences with proper Enums."""
        def convert_to_enum(field_name: str, value):
            # Map field names to Enum classes
            enum_map = {
                "theme": ThemeMode,
                "color_scheme": ColorScheme,
                "density": UIDensity,
                "icon_size": IconSize,
                "button_size": ButtonSize,
                "corner_radius": CornerRadius,
                "font_family": FontFamily,
                "monospace_font": MonospaceFont,
                "sidebar_behavior": SidebarBehavior,
                "position": NotificationPosition,
            }
            
            if field_name in enum_map and isinstance(value, str):
                try:
                    return enum_map[field_name](value)
                except ValueError:
                    # Fallback to default if value is invalid
                    return list(enum_map[field_name])[0]
            return value
        
        # Convert each section
        appearance_dict = prefs_dict.get("appearance", {})
        appearance = AppearancePreferences(
            theme=convert_to_enum("theme", appearance_dict.get("theme", ThemeMode.LIGHT.value)),
            color_scheme=convert_to_enum("color_scheme", appearance_dict.get("color_scheme", ColorScheme.BLUE.value)),
            accent_color=appearance_dict.get("accent_color", "#0ea5e9"),
            background_color=appearance_dict.get("background_color", "#f8fafc"),
            surface_color=appearance_dict.get("surface_color", "#ffffff"),
            text_color=appearance_dict.get("text_color", "#0f172a"),
            contrast_level=appearance_dict.get("contrast_level", 100),
        )
        
        size_dict = prefs_dict.get("size", {})
        size = SizePreferences(
            ui_scale=size_dict.get("ui_scale", 100),
            density=convert_to_enum("density", size_dict.get("density", UIDensity.NORMAL.value)),
            icon_size=convert_to_enum("icon_size", size_dict.get("icon_size", IconSize.MEDIUM.value)),
            button_size=convert_to_enum("button_size", size_dict.get("button_size", ButtonSize.MEDIUM.value)),
            text_size_multiplier=size_dict.get("text_size_multiplier", 1.0),
        )
        
        typography_dict = prefs_dict.get("typography", {})
        typography = TypographyPreferences(
            font_family=convert_to_enum("font_family", typography_dict.get("font_family", FontFamily.INTER.value)),
            font_size=typography_dict.get("font_size", 12),
            font_weight=typography_dict.get("font_weight", "normal"),
            line_height=typography_dict.get("line_height", 1.5),
            letter_spacing=typography_dict.get("letter_spacing", 0.0),
            monospace_font=convert_to_enum("monospace_font", typography_dict.get("monospace_font", MonospaceFont.JETBRAINS.value)),
        )
        
        interaction_dict = prefs_dict.get("interaction", {})
        interaction = InteractionPreferences(
            hover_effects=interaction_dict.get("hover_effects", True),
            click_feedback=interaction_dict.get("click_feedback", True),
            ripple_effect=interaction_dict.get("ripple_effect", False),
            page_transitions=interaction_dict.get("page_transitions", True),
            tooltips=interaction_dict.get("tooltips", True),
            animated_icons=interaction_dict.get("animated_icons", True),
            drag_feedback=interaction_dict.get("drag_feedback", True),
            loading_animations=interaction_dict.get("loading_animations", True),
            animation_speed=interaction_dict.get("animation_speed", 1.0),
        )
        
        layout_dict = prefs_dict.get("layout", {})
        layout = LayoutPreferences(
            sidebar_behavior=convert_to_enum("sidebar_behavior", layout_dict.get("sidebar_behavior", SidebarBehavior.EXPANDED.value)),
            menu_trigger=layout_dict.get("menu_trigger", "click"),
            dialog_position=layout_dict.get("dialog_position", "center"),
            table_density=convert_to_enum("table_density", layout_dict.get("table_density", UIDensity.NORMAL.value)),
            content_width=layout_dict.get("content_width", "normal"),
        )
        
        notifications_dict = prefs_dict.get("notifications", {})
        notifications = NotificationPreferences(
            show_notifications=notifications_dict.get("show_notifications", True),
            sound_enabled=notifications_dict.get("sound_enabled", False),
            desktop_notifications=notifications_dict.get("desktop_notifications", False),
            show_success=notifications_dict.get("show_success", True),
            show_errors=notifications_dict.get("show_errors", True),
            show_warnings=notifications_dict.get("show_warnings", True),
            show_info=notifications_dict.get("show_info", True),
            background_notifications=notifications_dict.get("background_notifications", True),
            position=convert_to_enum("position", notifications_dict.get("position", NotificationPosition.BOTTOM_RIGHT.value)),
            duration=notifications_dict.get("duration", 4),
        )
        
        input_dict = prefs_dict.get("input", {})
        input_prefs = InputPreferences(
            focus_style=input_dict.get("focus_style", "standard"),
            autocomplete=input_dict.get("autocomplete", True),
            spell_checking=input_dict.get("spell_checking", True),
            password_reveal=input_dict.get("password_reveal", True),
            clear_buttons=input_dict.get("clear_buttons", True),
            enter_key_behavior=input_dict.get("enter_key_behavior", "submit"),
            tab_behavior=input_dict.get("tab_behavior", "focus"),
        )
        
        accessibility_dict = prefs_dict.get("accessibility", {})
        accessibility = AccessibilityPreferences(
            high_contrast=accessibility_dict.get("high_contrast", False),
            larger_text=accessibility_dict.get("larger_text", False),
            reduce_motion=accessibility_dict.get("reduce_motion", False),
            always_show_focus=accessibility_dict.get("always_show_focus", False),
            larger_click_targets=accessibility_dict.get("larger_click_targets", False),
            screen_reader_optimized=accessibility_dict.get("screen_reader_optimized", False),
            disable_transparency=accessibility_dict.get("disable_transparency", False),
            color_blind_mode=accessibility_dict.get("color_blind_mode"),
        )
        
        shape_dict = prefs_dict.get("shape", {})
        shape = ShapePreferences(
            corner_radius=convert_to_enum("corner_radius", shape_dict.get("corner_radius", CornerRadius.MEDIUM.value)),
            border_visible=shape_dict.get("border_visible", True),
            shadow_enabled=shape_dict.get("shadow_enabled", True),
            elevation=shape_dict.get("elevation", 2),
            card_style=shape_dict.get("card_style", "elevated"),
            input_style=shape_dict.get("input_style", "outlined"),
        )
        
        return UserPreferences(
            appearance=appearance,
            size=size,
            typography=typography,
            interaction=interaction,
            layout=layout,
            notifications=notifications,
            input=input_prefs,
            accessibility=accessibility,
            shape=shape,
            current_profile=prefs_dict.get("current_profile", "default"),
            custom_profiles=prefs_dict.get("custom_profiles", {}),
        )


class PreferencesEngine:
    """Centralized preference engine that applies preferences globally."""
    
    def __init__(self, username: str):
        self.username = username
        self.storage = PreferencesStorage(username)
        self.preferences: UserPreferences = self._load_or_create_default()
        self._observers = []
    
    def _load_or_create_default(self) -> UserPreferences:
        """Load saved preferences or create default."""
        loaded = self.storage.load()
        if loaded:
            return loaded
        return UserPreferences()
    
    def save(self) -> bool:
        """Save current preferences."""
        return self.storage.save(self.preferences, exclude_custom_profiles=False)
    
    def apply_profile(self, profile_name: str) -> bool:
        """Apply a predefined preference profile."""
        # Preserve custom_profiles
        existing_custom_profiles = self.preferences.custom_profiles.copy()
        
        profiles = self._get_predefined_profiles()
        
        if profile_name in profiles:
            self.preferences = profiles[profile_name]
            self.preferences.custom_profiles = existing_custom_profiles
            self.preferences.current_profile = profile_name
            self.save()
            self._notify_observers()
            return True
        elif profile_name in self.preferences.custom_profiles:
            # Apply custom profile
            custom_prefs = self.preferences.custom_profiles[profile_name]
            self.preferences = self._dict_to_preferences(custom_prefs)
            self.preferences.custom_profiles = existing_custom_profiles
            self.preferences.current_profile = profile_name
            self.save()
            self._notify_observers()
            return True
        return False
    
    def save_as_profile(self, profile_name: str) -> bool:
        """Save current preferences as a custom profile."""
        # Reload to get existing custom_profiles
        loaded = self.storage.load()
        if loaded and loaded.custom_profiles:
            # Merge existing custom_profiles with current
            for key, value in loaded.custom_profiles.items():
                if key not in self.preferences.custom_profiles:
                    self.preferences.custom_profiles[key] = value
        
        # Save current preferences WITHOUT custom_profiles to avoid recursion
        prefs_dict = self.storage._preferences_to_dict(self.preferences, exclude_custom_profiles=True)
        
        # Add to custom_profiles
        self.preferences.custom_profiles[profile_name] = prefs_dict
        self.preferences.current_profile = profile_name
        # Save with custom_profiles included
        return self.storage.save(self.preferences, exclude_custom_profiles=False)
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a custom profile."""
        # Reload to get the latest custom_profiles from disk
        loaded = self.storage.load()
        if loaded:
            self.preferences.custom_profiles = loaded.custom_profiles
        
        if profile_name in self.preferences.custom_profiles:
            del self.preferences.custom_profiles[profile_name]
            if self.preferences.current_profile == profile_name:
                self.preferences.current_profile = "default"
            return self.save()
        print(f"Profile '{profile_name}' not found in custom_profiles: {list(self.preferences.custom_profiles.keys())}")
        return False
    
    def _get_predefined_profiles(self) -> dict[str, UserPreferences]:
        """Get predefined preference profiles."""
        return {
            "default": UserPreferences(),
            "compact": self._create_compact_profile(),
            "developer": self._create_developer_profile(),
            "accessibility": self._create_accessibility_profile(),
        }
    
    def _create_compact_profile(self) -> UserPreferences:
        """Create compact profile for space-efficient UI."""
        prefs = UserPreferences()
        prefs.size.density = UIDensity.COMPACT
        prefs.size.icon_size = IconSize.SMALL
        prefs.size.button_size = ButtonSize.SMALL
        prefs.size.ui_scale = 90
        prefs.layout.sidebar_behavior = SidebarBehavior.COLLAPSED
        prefs.shape.corner_radius = CornerRadius.SMALL
        prefs.interaction.animation_speed = 1.5
        return prefs
    
    def _create_developer_profile(self) -> UserPreferences:
        """Create developer profile optimized for technical users."""
        prefs = UserPreferences()
        prefs.typography.font_family = FontFamily.IBM_PLEX
        prefs.typography.monospace_font = MonospaceFont.JETBRAINS
        prefs.typography.font_size = 11
        prefs.size.density = UIDensity.COMPACT
        prefs.interaction.tooltips = True
        prefs.interaction.hover_effects = True
        prefs.shape.corner_radius = CornerRadius.SHARP
        prefs.layout.content_width = "wide"
        return prefs
    
    def _create_accessibility_profile(self) -> UserPreferences:
        """Create accessibility profile for users with disabilities."""
        prefs = UserPreferences()
        prefs.accessibility.high_contrast = True
        prefs.accessibility.larger_text = True
        prefs.accessibility.reduce_motion = True
        prefs.accessibility.always_show_focus = True
        prefs.accessibility.larger_click_targets = True
        prefs.size.text_size_multiplier = 1.25
        prefs.size.button_size = ButtonSize.LARGE
        prefs.size.icon_size = IconSize.LARGE
        prefs.interaction.animation_speed = 0.5
        prefs.shape.elevation = 0
        return prefs
    
    def register_observer(self, callback):
        """Register a callback to be called when preferences change."""
        self._observers.append(callback)
    
    def _notify_observers(self):
        """Notify all observers of preference changes."""
        for callback in self._observers:
            try:
                callback(self.preferences)
            except Exception as e:
                print(f"Error notifying observer: {e}")
    
    def _dict_to_preferences(self, prefs_dict: dict) -> UserPreferences:
        """Convert dict to UserPreferences (helper for custom profiles)."""
        return self.storage._dict_to_preferences(prefs_dict)
