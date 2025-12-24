"""配置和常量定义"""

# 颜色常量（向后兼容，将在初始化时更新）
COLOR_BG_MAIN = "#f0f2f5"
COLOR_BG_SIDEBAR = "#2c3e50"
COLOR_BG_CONFIG = "#34495e"
COLOR_BG_CHAT = "#ffffff"
COLOR_BG_PAIR = "#f8f9fa"
COLOR_BG_ERROR = "#ffe6e6"

COLOR_TEXT_WHITE = "white"
COLOR_TEXT_GRAY = "#bdc3c7"
COLOR_TEXT_DARK = "#2c3e50"
COLOR_TEXT_DARKER = "#34495e"
COLOR_TEXT_LIGHT_GRAY = "#95a5a6"
COLOR_TEXT_MEDIUM_GRAY = "#7f8c8d"
COLOR_TEXT_ERROR = "#c0392b"

COLOR_STATUS_RED = "#e74c3c"
COLOR_STATUS_GREEN = "#2ecc71"
COLOR_STATUS_ORANGE = "#f39c12"
COLOR_STATUS_BLUE = "#3498db"
COLOR_STATUS_PURPLE = "#9b59b6"
COLOR_STATUS_GRAY = "#95a5a6"

COLOR_BUTTON_BLUE = "#3498db"
COLOR_BUTTON_GREEN = "#2ecc71"
COLOR_BUTTON_RED = "#e74c3c"
COLOR_BUTTON_PURPLE = "#9b59b6"
COLOR_BUTTON_GRAY = "#95a5a6"
COLOR_BUTTON_HOVER = "#3498db"

COLOR_CODE_BG = "#f8f9fa"
COLOR_BG_INPUT = "#1a252f"  # 输入框深色背景

# 字体配置
FONT_TITLE = ("Segoe UI", 24, "bold")
FONT_TEXT = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_MEDIUM = ("Segoe UI", 12, "bold")
FONT_TINY = ("Segoe UI", 8)
FONT_CODE = ("Courier New", 10)
FONT_BOLD = ("Segoe UI", 11, "bold")
FONT_H1 = ("Segoe UI", 16, "bold")
FONT_H2 = ("Segoe UI", 14, "bold")
FONT_H3 = ("Segoe UI", 12, "bold")
FONT_ITALIC = ("Segoe UI", 10, "italic")

# UI尺寸常量
WINDOW_WIDTH = 1657  # 增加宽度以容纳左右边栏
WINDOW_HEIGHT = 1024
WINDOW_MIN_WIDTH = 1400  # 降低最小宽度，允许折叠边栏
WINDOW_MIN_HEIGHT = 900
SIDEBAR_WIDTH = 310
HISTORY_SIDEBAR_WIDTH = 310
SIDEBAR_COLLAPSED_WIDTH = 40  # 折叠后的宽度
TITLE_BAR_HEIGHT = 60
INPUT_HEIGHT = 4
CHECKBOX_FRAME_WIDTH = 30

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "max_tokens": 2000,
    "temperature": 0.7,
    "stream": True,
    "thinking_enabled": False,
    "dark_mode": False,
    "sidebar_collapsed": False,
    "history_sidebar_collapsed": False
}

# 模型配置
MODELS = ['deepseek-chat', 'deepseek-reasoner']
MODEL_MAX_TOKENS = {
    'deepseek-chat': 8000,
    'deepseek-reasoner': 64000
}

# 文件路径
CONFIG_FILE = "config/deepseek_config.json"
CHAT_HISTORY_DIR = "chat_history"
ICON_FILE = "icon/deepseek.ico"

# 其他常量
SEPARATOR_LENGTH = 50
TITLE_MAX_LENGTH = 9
MAX_TITLE_GEN_LENGTH = 3000
MAX_CONTENT_PREVIEW = 500
SCROLL_UPDATE_THRESHOLD = 10

# 主题配置
# 浅色主题（默认）
LIGHT_THEME = {
    "COLOR_BG_MAIN": "#f0f2f5",
    "COLOR_BG_SIDEBAR": "#2c3e50",
    "COLOR_BG_CONFIG": "#34495e",
    "COLOR_BG_CHAT": "#ffffff",
    "COLOR_BG_PAIR": "#f8f9fa",
    "COLOR_BG_ERROR": "#ffe6e6",
    "COLOR_BG_INPUT": "#1a252f",  # 输入框深色背景（比SIDEBAR更深）
    "COLOR_TEXT_WHITE": "white",
    "COLOR_TEXT_GRAY": "#bdc3c7",
    "COLOR_TEXT_DARK": "#2c3e50",
    "COLOR_TEXT_DARKER": "#34495e",
    "COLOR_TEXT_LIGHT_GRAY": "#95a5a6",
    "COLOR_TEXT_MEDIUM_GRAY": "#7f8c8d",
    "COLOR_TEXT_ERROR": "#c0392b",
    "COLOR_STATUS_RED": "#e74c3c",
    "COLOR_STATUS_GREEN": "#2ecc71",
    "COLOR_STATUS_ORANGE": "#f39c12",
    "COLOR_STATUS_BLUE": "#3498db",
    "COLOR_STATUS_PURPLE": "#9b59b6",
    "COLOR_STATUS_GRAY": "#95a5a6",
    "COLOR_BUTTON_BLUE": "#3498db",
    "COLOR_BUTTON_GREEN": "#2ecc71",
    "COLOR_BUTTON_RED": "#e74c3c",
    "COLOR_BUTTON_PURPLE": "#9b59b6",
    "COLOR_BUTTON_GRAY": "#95a5a6",
    "COLOR_BUTTON_HOVER": "#3498db",
    "COLOR_CODE_BG": "#f8f9fa",
}

# 深色主题（夜间模式）
DARK_THEME = {
    "COLOR_BG_MAIN": "#1a1a1a",
    "COLOR_BG_SIDEBAR": "#2d2d2d",
    "COLOR_BG_CONFIG": "#3d3d3d",
    "COLOR_BG_CHAT": "#252525",
    "COLOR_BG_PAIR": "#2d2d2d",
    "COLOR_BG_ERROR": "#4a2a2a",
    "COLOR_BG_INPUT": "#1f1f1f",  # 输入框深色背景（比SIDEBAR更深）
    "COLOR_TEXT_WHITE": "#e0e0e0",
    "COLOR_TEXT_GRAY": "#888888",
    "COLOR_TEXT_DARK": "#e0e0e0",
    "COLOR_TEXT_DARKER": "#d0d0d0",
    "COLOR_TEXT_LIGHT_GRAY": "#aaaaaa",
    "COLOR_TEXT_MEDIUM_GRAY": "#999999",
    "COLOR_TEXT_ERROR": "#ff6b6b",
    "COLOR_STATUS_RED": "#ff6b6b",
    "COLOR_STATUS_GREEN": "#51cf66",
    "COLOR_STATUS_ORANGE": "#ffa94d",
    "COLOR_STATUS_BLUE": "#4dabf7",
    "COLOR_STATUS_PURPLE": "#9775fa",
    "COLOR_STATUS_GRAY": "#868e96",
    "COLOR_BUTTON_BLUE": "#4dabf7",
    "COLOR_BUTTON_GREEN": "#51cf66",
    "COLOR_BUTTON_RED": "#ff6b6b",
    "COLOR_BUTTON_PURPLE": "#9775fa",
    "COLOR_BUTTON_GRAY": "#868e96",
    "COLOR_BUTTON_HOVER": "#5c7cfa",
    "COLOR_CODE_BG": "#1e1e1e",
}

# 当前主题（默认浅色）
_current_theme = LIGHT_THEME.copy()

def get_theme():
    """获取当前主题"""
    return _current_theme

def set_theme(dark_mode):
    """设置主题"""
    global _current_theme
    _current_theme = DARK_THEME.copy() if dark_mode else LIGHT_THEME.copy()
    # 更新全局变量以便向后兼容
    for key, value in _current_theme.items():
        globals()[key] = value

def get_color(color_name):
    """获取主题颜色"""
    return _current_theme.get(color_name, LIGHT_THEME.get(color_name))

