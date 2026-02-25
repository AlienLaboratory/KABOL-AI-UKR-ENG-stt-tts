"""Dark theme constants for the KA-BOL-AI GUI."""

# ---- Colors ----
BG_DARK = "#1a1a2e"        # Main background
BG_PANEL = "#16213e"       # Panel/card background
BG_INPUT = "#0f3460"       # Input field background
TEXT_PRIMARY = "#e0e0e0"   # Primary text
TEXT_SECONDARY = "#8899aa" # Secondary/muted text
TEXT_ACCENT = "#00d2ff"    # Accent text (cyan)
BORDER = "#2a2a4a"         # Border color

# Status colors
GREEN = "#00e676"          # Ready / active
RED = "#ff1744"            # Recording / listening
BLUE = "#2979ff"           # Processing / thinking
PURPLE = "#aa00ff"         # Speaking
YELLOW = "#ffd600"         # Warning
ORANGE = "#ff9100"         # Error / attention
GREY = "#616161"           # Inactive / disabled

# Mic button states
MIC_READY = GREEN
MIC_LISTENING = RED
MIC_PROCESSING = BLUE
MIC_SPEAKING = PURPLE
MIC_INACTIVE = GREY

# ---- Fonts ----
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 16, "bold")
FONT_HEADING = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_SMALL = (FONT_FAMILY, 10)
FONT_MONO = ("Consolas", 11)
FONT_TRANSCRIPT = ("Consolas", 11)
FONT_MIC_HINT = (FONT_FAMILY, 10)

# ---- Sizing ----
WINDOW_WIDTH = 520
WINDOW_HEIGHT = 720
MIC_BUTTON_SIZE = 120      # Diameter in pixels
PADDING = 12
CORNER_RADIUS = 10

# ---- Status text ----
STATUS_TEXT = {
    "ready":      {"en": "Ready", "uk": "Готовий"},
    "listening":  {"en": "Listening...", "uk": "Слухаю..."},
    "processing": {"en": "Thinking...", "uk": "Думаю..."},
    "speaking":   {"en": "Speaking...", "uk": "Говорю..."},
    "inactive":   {"en": "Inactive", "uk": "Неактивний"},
    "error":      {"en": "Error", "uk": "Помилка"},
}
