"""Qt 界面样式与主题（基于 config 主题，无坐标限制）"""

from PySide6.QtWidgets import QWidget, QFrame, QLabel, QPushButton, QTextEdit, QScrollArea
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
import config


def get_stylesheet():
    """根据当前主题返回完整样式表，按区域区分颜色避免全局 QWidget 覆盖。"""
    t = config.get_theme()
    return f"""
        QMainWindow {{
            background-color: {t["COLOR_BG_MAIN"]};
        }}
        QWidget#centralWidget {{
            background-color: {t["COLOR_BG_MAIN"]};
        }}
        /* 左侧配置栏：外层 CONFIG，内容区 SIDEBAR（与原版一致） */
        QWidget#sidebar {{
            background-color: {t["COLOR_BG_CONFIG"]};
        }}
        QWidget#sidebar QStackedWidget {{
            background-color: {t["COLOR_BG_CONFIG"]};
        }}
        QWidget#sidebar QPushButton#sidebarToggleBtn {{
            background: transparent;
            color: {t["COLOR_TEXT_WHITE"]};
            font-weight: bold;
            font-size: 12pt;
            border: none;
        }}
        QWidget#sidebar QPushButton#sidebarToggleBtn:hover {{
            background: {t["COLOR_TEXT_GRAY"]};
        }}
        QWidget#configPanel {{
            background-color: {t["COLOR_BG_SIDEBAR"]};
        }}
        QWidget#sidebar QLabel, QWidget#configPanel QLabel {{
            color: {t["COLOR_TEXT_WHITE"]};
            background: transparent;
        }}
        QWidget#configPanel QLineEdit {{
            background-color: {t["COLOR_BG_INPUT"]};
            color: {t["COLOR_TEXT_WHITE"]};
            border: 1px solid {t["COLOR_TEXT_GRAY"]};
            border-radius: 3px;
            padding: 4px;
        }}
        QWidget#configPanel QComboBox {{
            background-color: {t["COLOR_BG_INPUT"]};
            color: {t["COLOR_TEXT_WHITE"]};
            border: 1px solid {t["COLOR_TEXT_GRAY"]};
            border-radius: 3px;
            padding: 4px;
        }}
        QWidget#configPanel QComboBox::drop-down {{
            border: none;
            background: transparent;
        }}
        QWidget#configPanel QPushButton {{
            background-color: {t["COLOR_BUTTON_BLUE"]};
            color: {t["COLOR_TEXT_WHITE"]};
            border: none;
            border-radius: 3px;
            padding: 6px 12px;
            font-size: 9pt;
        }}
        QWidget#configPanel QPushButton:hover {{
            background-color: {t["COLOR_BUTTON_HOVER"]};
        }}
        QWidget#configPanel QPushButton:disabled {{
            background-color: {t["COLOR_TEXT_GRAY"]};
        }}
        QWidget#configPanel QPushButton[colorRole="purple"] {{
            background-color: {t["COLOR_BUTTON_PURPLE"]};
        }}
        QWidget#configPanel QCheckBox {{
            color: {t["COLOR_TEXT_WHITE"]};
            background: transparent;
        }}
        QWidget#configPanel QSlider::groove:horizontal {{
            background: {t["COLOR_TEXT_GRAY"]};
            height: 6px;
            border-radius: 3px;
        }}
        QWidget#configPanel QSlider::handle:horizontal {{
            background: {t["COLOR_TEXT_WHITE"]};
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}
        /* 右侧历史栏：外层 CONFIG，列表区 SIDEBAR（与原版一致） */
        QWidget#historySidebar {{
            background-color: {t["COLOR_BG_CONFIG"]};
        }}
        QWidget#historySidebar QStackedWidget {{
            background-color: {t["COLOR_BG_CONFIG"]};
        }}
        QWidget#historySidebar QPushButton#sidebarToggleBtn {{
            background: transparent;
            color: {t["COLOR_TEXT_WHITE"]};
            font-weight: bold;
            font-size: 12pt;
            border: none;
        }}
        QWidget#historySidebar QPushButton#sidebarToggleBtn:hover {{
            background: {t["COLOR_TEXT_GRAY"]};
        }}
        QWidget#historyPanel {{
            background-color: {t["COLOR_BG_SIDEBAR"]};
        }}
        QWidget#historyPanel QScrollArea {{
            background-color: {t["COLOR_BG_SIDEBAR"]};
            border: none;
        }}
        QWidget#historyPanel QScrollArea QWidget {{
            background-color: {t["COLOR_BG_SIDEBAR"]};
        }}
        QWidget#historyPanel QLabel {{
            color: {t["COLOR_TEXT_WHITE"]};
            background: transparent;
        }}
        QWidget#historyPanel QPushButton {{
            background-color: {t["COLOR_BG_SIDEBAR"]};
            color: {t["COLOR_TEXT_WHITE"]};
            border: none;
            text-align: left;
            padding: 8px 10px;
        }}
        QWidget#historyPanel QPushButton:hover {{
            background-color: {t["COLOR_BUTTON_HOVER"]};
        }}
        QWidget#historyPanel QPushButton#historyDeleteBtn {{
            background: transparent;
            min-width: 28px;
            max-width: 28px;
        }}
        QWidget#historyPanel QPushButton#historyDeleteBtn:hover {{
            background-color: {t["COLOR_BUTTON_RED"]};
        }}
        QWidget#historyPanel QPushButton[colorRole="blue"] {{
            background-color: {t["COLOR_BUTTON_BLUE"]};
        }}
        /* 中间区域：容器 BG_MAIN，标题/聊天/输入块 BG_CHAT（与原版一致） */
        QWidget#centerPanel {{
            background-color: {t["COLOR_BG_MAIN"]};
        }}
        QWidget#centerPanel > QWidget {{
            background-color: {t["COLOR_BG_CHAT"]};
        }}
        QWidget#centerPanel QLabel {{
            color: {t["COLOR_TEXT_DARK"]};
            background: transparent;
        }}
        QWidget#centerPanel QTextEdit {{
            background-color: {t["COLOR_BG_CHAT"]};
            color: {t["COLOR_TEXT_DARK"]};
            border: 1px solid {t["COLOR_TEXT_GRAY"]};
            border-radius: 3px;
            padding: 8px;
            font-size: 11pt;
        }}
        QWidget#centerPanel QPushButton {{
            background-color: {t["COLOR_BUTTON_GRAY"]};
            color: {t["COLOR_TEXT_WHITE"]};
            border: none;
            border-radius: 3px;
            padding: 6px 12px;
        }}
        QWidget#centerPanel QPushButton:hover {{
            background-color: {t["COLOR_BUTTON_HOVER"]};
        }}
        QWidget#centerPanel QPushButton:disabled {{
            background-color: {t["COLOR_TEXT_GRAY"]};
        }}
        QWidget#centerPanel QPushButton[colorRole="green"] {{
            background-color: {t["COLOR_BUTTON_GREEN"]};
        }}
        QWidget#centerPanel QPushButton[colorRole="red"] {{
            background-color: {t["COLOR_BUTTON_RED"]};
        }}
        QWidget#centerPanel QPushButton[colorRole="blue"] {{
            background-color: {t["COLOR_BUTTON_BLUE"]};
        }}
        /* 聊天区域：日间为白，夜间为深灰 */
        QWidget#chatArea {{
            background-color: {t["COLOR_BG_CHAT"]};
        }}
        QWidget#chatArea QScrollArea {{
            border: none;
            background-color: {t["COLOR_BG_CHAT"]};
        }}
        QWidget#chatArea QScrollArea::viewport {{
            background-color: {t["COLOR_BG_CHAT"]};
        }}
        QWidget#chatArea QScrollArea QWidget {{
            background-color: {t["COLOR_BG_CHAT"]};
        }}
        QFrame#pairFrame {{
            background-color: {t["COLOR_BG_PAIR"]};
            border: 1px solid {t["COLOR_TEXT_GRAY"]};
            border-radius: 4px;
        }}
        QFrame#pairFrame QCheckBox {{
            spacing: 6px;
        }}
        QFrame#pairFrame QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {t["COLOR_TEXT_GRAY"]};
            border-radius: 3px;
            background: {t["COLOR_BG_CHAT"]};
        }}
        QFrame#pairFrame QCheckBox::indicator:checked {{
            background: {t["COLOR_BUTTON_BLUE"]};
            border-color: {t["COLOR_BUTTON_BLUE"]};
        }}
        QFrame#pairFrame QCheckBox::indicator:hover {{
            border-color: {t["COLOR_BUTTON_BLUE"]};
        }}
        QFrame#pairFrame QTextEdit {{
            background-color: {t["COLOR_BG_CHAT"]};
            color: {t["COLOR_TEXT_DARK"]};
            border: none;
            font-size: 11pt;
        }}
        QFrame#pairFrame QLabel {{
            background: transparent;
        }}
        QFrame#pairFrame QPushButton#pairDeleteBtn {{
            background: transparent;
            color: {t["COLOR_TEXT_MEDIUM_GRAY"]};
            border: none;
            padding: 0;
        }}
        QFrame#pairFrame QPushButton#pairDeleteBtn:hover {{
            background-color: {t["COLOR_BUTTON_RED"]};
        }}
        /* 滚动条 */
        QScrollBar:vertical {{
            background: {t["COLOR_BG_PAIR"]};
            width: 10px;
            border-radius: 5px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {t["COLOR_TEXT_GRAY"]};
            border-radius: 5px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t["COLOR_TEXT_MEDIUM_GRAY"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
    """


def apply_theme_to_app(app):
    """为 QApplication 设置全局样式"""
    app.setStyleSheet(get_stylesheet())


def font_text():
    """正文字体"""
    return QFont("Segoe UI", 11)


def font_small():
    """小号字体"""
    return QFont("Segoe UI", 9)


def font_medium():
    """中号加粗"""
    f = QFont("Segoe UI", 12)
    f.setBold(True)
    return f
