"""Qt 侧边栏：API 配置 + 历史记录列表，支持折叠/展开"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QSlider, QScrollArea, QFrame, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QFontMetrics
import config


class _HistoryItemRow(QWidget):
    """单条历史：按宽度省略标题，resize 时更新。"""
    def __init__(self, filepath, filename, theme, load_requested, delete_requested, parent=None):
        super().__init__(parent)
        self._filename = filename
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(4)
        self._load_btn = QPushButton()
        self._load_btn.setCursor(Qt.PointingHandCursor)
        self._load_btn.setToolTip(filename)
        self._load_btn.setStyleSheet(f"""
            QPushButton {{ text-align: left; padding: 6px 6px; background: transparent; color: {theme['COLOR_TEXT_WHITE']}; border: none; font-size: 9pt; }}
            QPushButton:hover {{ background: {theme['COLOR_TEXT_GRAY']}; color: {theme['COLOR_TEXT_WHITE']}; }}
        """)
        self._load_btn.clicked.connect(lambda: load_requested.emit(filepath))
        row_layout.addWidget(self._load_btn, 1)
        self._del_btn = QPushButton("🗑")
        self._del_btn.setObjectName("historyDeleteBtn")
        self._del_btn.setFixedSize(28, 28)
        self._del_btn.setCursor(Qt.PointingHandCursor)
        self._del_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {theme['COLOR_TEXT_MEDIUM_GRAY']}; border: none; font-size: 12pt; padding: 0; }}
            QPushButton:hover {{ background-color: {theme['COLOR_BUTTON_RED']}; }}
        """)
        self._del_btn.clicked.connect(lambda: delete_requested.emit(filepath, filename))
        row_layout.addWidget(self._del_btn, 0)
        self._update_elided_text()

    def _update_elided_text(self):
        w = self._load_btn.width()
        if w <= 0:
            w = 200
        fm = QFontMetrics(self._load_btn.font())
        self._load_btn.setText(fm.elidedText(self._filename, Qt.TextElideMode.ElideMiddle, w))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided_text()


def _theme():
    return config.get_theme()


class CollapsibleSidebar(QWidget):
    """可折叠侧栏：展开时显示 content_widget，折叠时仅显示窄条与切换按钮。"""
    toggled = Signal(bool)  # True = 当前为折叠状态

    def __init__(self, content_widget, collapsed_width=config.SIDEBAR_COLLAPSED_WIDTH,
                 expanded_width=config.SIDEBAR_WIDTH, toggle_arrow_left="◀", toggle_arrow_right="▶",
                 initial_collapsed=False, object_name="sidebar", parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._collapsed = initial_collapsed
        self._expanded_width = expanded_width
        self._collapsed_width = collapsed_width
        self._toggle_arrow_left = toggle_arrow_left
        self._toggle_arrow_right = toggle_arrow_right
        self.setMinimumWidth(collapsed_width)
        self.setMaximumWidth(expanded_width)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.toggle_btn = QPushButton(toggle_arrow_right if initial_collapsed else toggle_arrow_left)
        self.toggle_btn.setObjectName("sidebarToggleBtn")
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle)
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(content_widget)
        layout.addWidget(self.content_stack, 1)
        layout.addWidget(self.toggle_btn, 0, Qt.AlignTop | Qt.AlignRight)
        self._content_widget = content_widget
        self._apply_state()

    def _apply_state(self):
        if self._collapsed:
            self.setFixedWidth(self._collapsed_width)
            self.content_stack.hide()
            self.toggle_btn.setText(self._toggle_arrow_right)
        else:
            self.setFixedWidth(self._expanded_width)
            self.content_stack.show()
            self.toggle_btn.setText(self._toggle_arrow_left)

    def toggle(self):
        self._collapsed = not self._collapsed
        self._apply_state()
        self.toggled.emit(self._collapsed)

    def is_collapsed(self):
        return self._collapsed

    def set_collapsed(self, collapsed):
        self._collapsed = collapsed
        self._apply_state()


class ConfigPanel(QWidget):
    """左侧 API 与参数配置"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("configPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(200)
        self.setMaximumWidth(320)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # API 配置
        layout.addWidget(QLabel("API配置"))
        layout.addWidget(QLabel("API密钥:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("sk-...")
        layout.addWidget(self.api_key_edit)
        layout.addWidget(QLabel("API端点:"))
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.deepseek.com")
        layout.addWidget(self.base_url_edit)
        layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(config.MODELS)
        self.model_combo.setCurrentText(config.DEFAULT_CONFIG["model"])
        layout.addWidget(self.model_combo)
        btn_row = QHBoxLayout()
        self.init_btn = QPushButton("🔗 连接")
        self.test_btn = QPushButton("🔄 测试")
        btn_row.addWidget(self.init_btn)
        btn_row.addWidget(self.test_btn)
        layout.addLayout(btn_row)

        # 参数
        layout.addWidget(QLabel("生成参数"))
        self.thinking_check = QCheckBox("思考模式")
        layout.addWidget(self.thinking_check)
        layout.addWidget(QLabel("最大长度:"))
        self.max_tokens_slider = QSlider(Qt.Horizontal)
        self.max_tokens_slider.setRange(100, config.MODEL_MAX_TOKENS.get(self.model_combo.currentText(), 8000))
        self.max_tokens_slider.setValue(config.DEFAULT_CONFIG["max_tokens"])
        self.max_tokens_label = QLabel(str(self.max_tokens_slider.value()))
        self.max_tokens_slider.valueChanged.connect(lambda v: self.max_tokens_label.setText(str(v)))
        layout.addWidget(self.max_tokens_slider)
        layout.addWidget(self.max_tokens_label)
        layout.addWidget(QLabel("随机性:"))
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 20)
        self.temp_slider.setValue(int(config.DEFAULT_CONFIG["temperature"] * 10))
        layout.addWidget(self.temp_slider)
        self.stream_check = QCheckBox("流式响应")
        self.stream_check.setChecked(True)
        layout.addWidget(self.stream_check)
        self.dark_check = QCheckBox("🌙 夜间模式")
        layout.addWidget(self.dark_check)
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.setProperty("colorRole", "purple")
        layout.addWidget(self.save_btn)

        layout.addStretch()

    def set_init_connected(self, connected):
        theme = config.get_theme()
        if connected:
            self.init_btn.setText("✅ 已连接")
            self.init_btn.setStyleSheet(f"background-color: {theme['COLOR_STATUS_GREEN']}; color: {theme['COLOR_TEXT_WHITE']};")
        else:
            self.init_btn.setText("🔗 连接")
            self.init_btn.setStyleSheet("")

    def get_api_key(self):
        return self.api_key_edit.text().strip()

    def get_base_url(self):
        return self.base_url_edit.text().strip()

    def get_model(self):
        return self.model_combo.currentText()

    def get_max_tokens(self):
        return self.max_tokens_slider.value()

    def get_temperature(self):
        return self.temp_slider.value() / 10.0

    def get_stream(self):
        return self.stream_check.isChecked()

    def get_thinking_enabled(self):
        return self.thinking_check.isChecked()

    def get_dark_mode(self):
        return self.dark_check.isChecked()

    def set_config(self, cfg):
        self.api_key_edit.setText(cfg.get("api_key", ""))
        self.base_url_edit.setText(cfg.get("base_url", config.DEFAULT_CONFIG["base_url"]))
        self.model_combo.setCurrentText(cfg.get("model", config.DEFAULT_CONFIG["model"]))
        self.max_tokens_slider.setValue(cfg.get("max_tokens", config.DEFAULT_CONFIG["max_tokens"]))
        self.temp_slider.setValue(int((cfg.get("temperature", 0.7) * 10)))
        self.stream_check.setChecked(cfg.get("stream", True))
        self.thinking_check.setChecked(cfg.get("thinking_enabled", False))
        self.dark_check.setChecked(cfg.get("dark_mode", False))
        m = self.model_combo.currentText()
        self.max_tokens_slider.setMaximum(config.MODEL_MAX_TOKENS.get(m, 8000))

    def update_max_tokens_range(self):
        m = self.model_combo.currentText()
        self.max_tokens_slider.setMaximum(config.MODEL_MAX_TOKENS.get(m, 8000))


class HistoryPanel(QWidget):
    """右侧历史记录列表"""
    load_requested = Signal(str)
    delete_requested = Signal(str, str)  # filepath, filename

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("historyPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(200)
        self.setMaximumWidth(320)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📚 对话历史"))
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setProperty("colorRole", "blue")
        layout.addWidget(self.refresh_btn)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("")
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.list_widget)
        layout.addWidget(self.scroll)
        self.row_widgets = []

    def set_items(self, items):
        """items: list of (mtime, filepath, filename)"""
        for w in self.row_widgets:
            w.deleteLater()
        self.row_widgets.clear()
        theme = _theme()
        for _mtime, filepath, filename in items:
            row = _HistoryItemRow(
                filepath, filename, theme,
                self.load_requested, self.delete_requested,
                parent=self.list_widget,
            )
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)
            self.row_widgets.append(row)
