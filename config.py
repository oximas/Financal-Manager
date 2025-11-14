"""Configitation constants for the Finance Manager"""
"""WAS WRITTEN BY Claude.ai check there for complete code after studying the appropriate material
search for "Financial Manager Design" in your claude acount
"""
class UIConfig:
    """UI-related configuration"""
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 300
    WINDOW_MARGIN = 20

    # Colors
    COLOR_BACKGROUND = "#000000"
    COLOR_PRIMARY = "#98FB98"
    COLOR_SECONDARY = "#444"
    COLOR_SUCCESS = "#00FFC6"
    COLOR_TEXT_PRIMARY = "white"
    COLOR_TEXT_SECONDARY = "#BBBBBB"
    COLOR_TEXT_DARK = "#111"
    COLOR_FRAME_LIGHT = "#222"
    COLOR_FRAME_DARK = "#333"

    # Spacing
    PADDING_SMALL = 2
    PADDING_MEDIUM = 5
    PADDING_LARGE = 10
    PADDING_XLARGE = 20

    # Sizes
    BUTTON_WIDTH = 200
    ENTRY_WIDTH = 250

    # Fonts
    FONT_TITLE = ("Arial", 24, "bold")
    FONT_HEADING = ("Helvetica", 18, "bold")
    FONT_SUBHEADING = ("Helvetica", 16, "bold")
    FONT_NORMAL = ("Helvetica", 14)
    FONT_BUTTON = ("Helvetica", 14, "bold")

class AppConfig:
    DB_NAME = "personal_financial_manager.db"
    APPEARANCE_MODE = "System"
    COLOR_THEME = "blue"
    DEFAULT_VAULT_NAME = "Main"
