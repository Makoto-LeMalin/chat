"""配置和常量定义"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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

# Canvas 在 Windows 上存在 y 坐标约 32767 像素的渲染上限，超出部分会显示为空白（Tk 限制）
CANVAS_MAX_Y = 32767

# UI尺寸常量
WINDOW_WIDTH = 1200  # 增加宽度以容纳左右边栏
WINDOW_HEIGHT = 750
WINDOW_MIN_WIDTH = 1000  # 降低最小宽度，允许折叠边栏
WINDOW_MIN_HEIGHT = 600
SIDEBAR_WIDTH = 310
HISTORY_SIDEBAR_WIDTH = 310
SIDEBAR_COLLAPSED_WIDTH = 40  # 折叠后的宽度
TITLE_BAR_HEIGHT = 60
INPUT_HEIGHT = 4
CHECKBOX_FRAME_WIDTH = 30

# 文件路径
CONFIG_FILE = "config/deepseek_config.json"

# 默认单端点配置（用于迁移旧配置）
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

# 兼容：默认模型列表与 token 上限（无 providers 时使用）
MODELS = ["deepseek-chat", "deepseek-reasoner"]
MODEL_MAX_TOKENS = {
    "deepseek-chat": 8000,
    "deepseek-reasoner": 64000
}
DEFAULT_MODEL_MAX_TOKENS = 8000


@dataclass
class Provider:
    """单个厂商/端点配置"""
    id: str
    name: str
    endpoint: str
    api_key: str
    models: List[str] = field(default_factory=list)
    model_max_tokens: Dict[str, int] = field(default_factory=dict)
    models_url: str = ""  # 获取模型列表的 URL，留空则自动尝试 /v1/models 或 /models

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "endpoint": self.endpoint.strip().rstrip("/"),
            "api_key": self.api_key,
            "models": list(self.models),
            "model_max_tokens": dict(self.model_max_tokens),
            "models_url": self.models_url.strip(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Provider":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            endpoint=str(d.get("endpoint", "")).strip().rstrip("/"),
            api_key=str(d.get("api_key", "")),
            models=list(d.get("models") or []),
            model_max_tokens=dict(d.get("model_max_tokens") or {}),
            models_url=str(d.get("models_url", "")).strip(),
        )


def _config_path() -> str:
    """与 main 一致：使用相对路径，依赖进程 cwd 为项目根。"""
    return CONFIG_FILE


def _ensure_config_dir():
    p = _config_path()
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)


def migrate_old_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """将旧格式（无 providers）转为新格式。不写文件，只返回新 dict。"""
    if "providers" in data and isinstance(data["providers"], list) and len(data["providers"]) > 0:
        return data
    base_url = (data.get("base_url") or DEFAULT_CONFIG["base_url"]).strip().rstrip("/")
    model = data.get("model") or DEFAULT_CONFIG["model"]
    api_key = data.get("api_key") or ""
    provider_id = "default"
    name = "Default"
    if "deepseek" in base_url.lower():
        provider_id = "deepseek"
        name = "DeepSeek"
    models = list(MODELS)
    model_max_tokens = dict(MODEL_MAX_TOKENS)
    if model and model not in models:
        models = [model] + [m for m in models if m != model]
    providers = [
        {
            "id": provider_id,
            "name": name,
            "endpoint": base_url,
            "api_key": api_key,
            "models": models,
            "model_max_tokens": model_max_tokens,
        }
    ]
    out = dict(data)
    out["providers"] = providers
    out["current_provider_id"] = provider_id
    out["current_model"] = model
    return out


def load_config() -> Dict[str, Any]:
    """加载完整配置；若为旧格式则自动迁移为新格式（仅内存，不自动保存）。"""
    path = _config_path()
    if not os.path.exists(path):
        return migrate_old_config(dict(DEFAULT_CONFIG))
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = dict(DEFAULT_CONFIG)
    return migrate_old_config(data)


def save_config(data: Dict[str, Any]) -> None:
    """保存完整配置。"""
    _ensure_config_dir()
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_providers() -> List[Provider]:
    """加载 providers 列表（已迁移格式）。"""
    data = load_config()
    raw = data.get("providers") or []
    return [Provider.from_dict(p) for p in raw]


def save_providers(providers: List[Provider], full_config: Optional[Dict[str, Any]] = None) -> None:
    """保存 providers；若提供 full_config 则在此基础上更新 providers 后整体保存。"""
    data = full_config if full_config is not None else load_config()
    data["providers"] = [p.to_dict() for p in providers]
    save_config(data)


def get_provider_by_id(provider_id: str) -> Optional[Provider]:
    """按 id 获取 provider。"""
    for p in load_providers():
        if p.id == provider_id:
            return p
    return None


def get_models_for_provider(provider: Optional[Provider]) -> List[str]:
    """获取某 provider 的模型列表；无则返回默认 MODELS。"""
    if provider and provider.models:
        return list(provider.models)
    return list(MODELS)


def get_model_max_tokens(provider_id: Optional[str], model: str) -> int:
    """获取某厂商下某模型的最大 token 数。"""
    if provider_id:
        p = get_provider_by_id(provider_id)
        if p and p.model_max_tokens and model in p.model_max_tokens:
            return p.model_max_tokens[model]
    return MODEL_MAX_TOKENS.get(model, DEFAULT_MODEL_MAX_TOKENS)
CHAT_HISTORY_DIR = "chat_history"
ICON_FILE = "icon/deepseek.ico"

# 其他常量
SEPARATOR_LENGTH = 50
TITLE_MAX_LENGTH = 10
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
    "COLOR_BG_PAIR_SELECTED": "#d0e8f7",  # 对话对选中时背景（更明显的青蓝）
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
    "COLOR_BG_PAIR_SELECTED": "#404050",  # 对话对选中时背景（更明显的亮色）
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

