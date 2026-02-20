"""Qt 侧边栏：API 配置 + 历史记录列表，支持折叠/展开"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QSlider, QScrollArea, QFrame, QSizePolicy, QStackedWidget,
    QTabWidget, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, QMessageBox,
    QFormLayout, QGroupBox, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QFontMetrics
import threading
import config
from config import Provider, load_providers, save_providers, load_config, save_config
import model_discovery


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


class ProviderEditDialog(QDialog):
    """添加/编辑端点对话框"""
    def __init__(self, parent=None, provider: Provider = None):
        super().__init__(parent)
        self.setWindowTitle("编辑端点" if provider else "添加端点")
        self.setMinimumSize(480, 320)
        self._provider = provider
        layout = QFormLayout(self)
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("如: deepseek, openai")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("显示名称")
        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText("https://api.example.com")
        self.models_url_edit = QLineEdit()
        self.models_url_edit.setPlaceholderText("/v1/models（留空则自动尝试）")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("sk-...")
        layout.addRow("ID:", self.id_edit)
        layout.addRow("名称:", self.name_edit)
        layout.addRow("端点:", self.endpoint_edit)
        layout.addRow("获取模型 URL:", self.models_url_edit)
        layout.addRow("API 密钥:", self.api_key_edit)
        if provider:
            self.id_edit.setText(provider.id)
            self.name_edit.setText(provider.name)
            self.endpoint_edit.setText(provider.endpoint)
            self.models_url_edit.setText(provider.models_url)
            self.api_key_edit.setText(provider.api_key)
            self.id_edit.setEnabled(False)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_provider(self) -> Provider:
        return Provider(
            id=self.id_edit.text().strip() or "default",
            name=self.name_edit.text().strip() or "Default",
            endpoint=self.endpoint_edit.text().strip().rstrip("/") or "https://api.deepseek.com",
            api_key=self.api_key_edit.text().strip(),
            models=self._provider.models if self._provider else [],
            model_max_tokens=dict(self._provider.model_max_tokens) if self._provider else {},
            models_url=self.models_url_edit.text().strip(),
        )


class ProviderManageDialog(QDialog):
    """API 端点与密钥管理对话框"""
    providers_updated = Signal()
    refresh_done = Signal(int, object, object, str)  # row, provider, models, error_str (empty if ok)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑API及密钥")
        self.setMinimumSize(640, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("端点与密钥"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.list_widget)
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.setProperty("colorRole", "green")
        self.edit_btn = QPushButton("✏️ 编辑")
        self.delete_btn = QPushButton("🗑 删除")
        self.delete_btn.setProperty("colorRole", "red")
        self.refresh_models_btn = QPushButton("🔄 刷新模型")
        self.refresh_models_btn.setProperty("colorRole", "blue")
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addWidget(self.refresh_models_btn)
        layout.addLayout(btn_row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)
        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.delete_btn.clicked.connect(self._on_delete)
        self.refresh_models_btn.clicked.connect(self._on_refresh_models)
        self.refresh_done.connect(self._apply_refresh_result)
        self.list_widget.itemDoubleClicked.connect(lambda: self._on_edit())
        self._providers = []
        self.load_providers_list()

    def _refresh_list(self):
        self.list_widget.clear()
        for p in self._providers:
            item = QListWidgetItem(f"{p.name} — {p.endpoint}")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self.list_widget.addItem(item)

    def load_providers_list(self):
        self._providers = load_providers()
        self._refresh_list()

    def _save(self):
        full = load_config()
        save_providers(self._providers, full)
        self.providers_updated.emit()

    def _on_add(self):
        dlg = ProviderEditDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        p = dlg.get_provider()
        existing_ids = {x.id for x in self._providers}
        if p.id in existing_ids:
            base = p.id
            for i in range(1, 100):
                p.id = f"{base}_{i}"
                if p.id not in existing_ids:
                    break
        self._providers.append(p)
        self._save()
        self._refresh_list()

    def _on_edit(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._providers):
            return
        p = self._providers[row]
        dlg = ProviderEditDialog(self, p)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._providers[row] = dlg.get_provider()
        self._save()
        self._refresh_list()

    def _on_delete(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._providers):
            return
        p = self._providers[row]
        if QMessageBox.question(
            self, "确认删除",
            f"确定要删除端点「{p.name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        self._providers.pop(row)
        self._save()
        self._refresh_list()

    def _on_refresh_models(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._providers):
            QMessageBox.information(self, "提示", "请先选择要刷新模型的端点。")
            return
        p = self._providers[row]
        self.refresh_models_btn.setEnabled(False)
        self.refresh_models_btn.setText("获取中…")

        def work():
            try:
                models = model_discovery.get_models_sync(
                    p.endpoint, p.api_key, use_cache=False, models_url=p.models_url
                )
                self.refresh_done.emit(row, p, models, "")
            except Exception as e:
                self.refresh_done.emit(row, p, None, str(e))

        threading.Thread(target=work, daemon=True).start()

    def _apply_refresh_result(self, row, p, models, error_str):
        error = error_str if error_str else None
        try:
            if error:
                QMessageBox.warning(self, "错误", error)
            elif models:
                self._providers[row] = Provider(
                    id=p.id, name=p.name, endpoint=p.endpoint, api_key=p.api_key,
                    models=models, model_max_tokens=dict(p.model_max_tokens),
                    models_url=p.models_url,
                )
                self._save()
                self._refresh_list()
                self.providers_updated.emit()
                QMessageBox.information(self, "成功", f"已获取 {len(models)} 个模型。")
            else:
                QMessageBox.warning(self, "提示", "未获取到模型列表，请检查端点和密钥。")
        finally:
            self.refresh_models_btn.setEnabled(True)
            self.refresh_models_btn.setText("🔄 刷新模型")

    def get_providers(self):
        return list(self._providers)


class ParamsTab(QWidget):
    """参数配置：厂商/模型选择、生成参数、连接与测试"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._providers = []
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("厂商与模型"))
        self.edit_api_btn = QPushButton("⚙️ 编辑API及密钥")
        self.edit_api_btn.setProperty("colorRole", "blue")
        layout.addWidget(self.edit_api_btn)
        layout.addWidget(QLabel("厂商:"))
        self.provider_combo = QComboBox()
        layout.addWidget(self.provider_combo)
        layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        layout.addWidget(self.model_combo)
        btn_row = QHBoxLayout()
        self.init_btn = QPushButton("🔗 连接")
        self.test_btn = QPushButton("🔄 测试")
        btn_row.addWidget(self.init_btn)
        btn_row.addWidget(self.test_btn)
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("生成参数"))
        self.thinking_check = QCheckBox("思考模式")
        layout.addWidget(self.thinking_check)
        layout.addWidget(QLabel("最大长度:"))
        self.max_tokens_slider = QSlider(Qt.Horizontal)
        self.max_tokens_slider.setRange(100, config.DEFAULT_MODEL_MAX_TOKENS)
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

        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        self.edit_api_btn.clicked.connect(self._on_edit_api)
        layout.addStretch()

    def _on_edit_api(self):
        dlg = ProviderManageDialog(self)
        dlg.providers_updated.connect(self._on_providers_updated)
        dlg.exec()

    def _on_providers_updated(self):
        self.set_providers(load_providers())

    def set_providers(self, providers):
        self._providers = list(providers)
        self.provider_combo.clear()
        for p in self._providers:
            self.provider_combo.addItem(f"{p.name} ({p.id})", p.id)
        self._fill_models_for_current_provider()

    def _current_provider(self):
        i = self.provider_combo.currentIndex()
        if 0 <= i < len(self._providers):
            return self._providers[i]
        return None

    def _fill_models_for_current_provider(self):
        p = self._current_provider()
        models = config.get_models_for_provider(p)
        prev = self.model_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItems(models)
        if prev and prev in models:
            self.model_combo.setCurrentText(prev)
        elif models:
            self.model_combo.setCurrentIndex(0)
        self._update_max_tokens_max()

    def _on_provider_changed(self):
        self._fill_models_for_current_provider()

    def _on_model_changed(self):
        self._update_max_tokens_max()

    def _update_max_tokens_max(self):
        pid = self.get_current_provider_id()
        m = self.model_combo.currentText()
        max_tok = config.get_model_max_tokens(pid, m)
        current_value = self.max_tokens_slider.value()
        # 先设置最大值为模型的 max_tokens
        self.max_tokens_slider.setMaximum(max_tok)
        # 如果当前值超过新的最大值，则调整为新的最大值
        if current_value > max_tok:
            self.max_tokens_slider.setValue(max_tok)

    def get_current_provider_id(self):
        p = self._current_provider()
        return p.id if p else None

    def get_current_provider(self):
        return self._current_provider()

    def set_init_connected(self, connected):
        theme = config.get_theme()
        if connected:
            self.init_btn.setText("✅ 已连接")
            self.init_btn.setStyleSheet(f"background-color: {theme['COLOR_STATUS_GREEN']}; color: {theme['COLOR_TEXT_WHITE']};")
        else:
            self.init_btn.setText("🔗 连接")
            self.init_btn.setStyleSheet("")

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
        self.max_tokens_slider.setValue(cfg.get("max_tokens", config.DEFAULT_CONFIG["max_tokens"]))
        self.temp_slider.setValue(int((cfg.get("temperature", 0.7) * 10)))
        self.stream_check.setChecked(cfg.get("stream", True))
        self.thinking_check.setChecked(cfg.get("thinking_enabled", False))
        self.dark_check.setChecked(cfg.get("dark_mode", False))
        pid = cfg.get("current_provider_id")
        model = cfg.get("current_model") or cfg.get("model", config.DEFAULT_CONFIG["model"])
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == pid:
                self.provider_combo.setCurrentIndex(i)
                break
        self._fill_models_for_current_provider()
        self.model_combo.setCurrentText(model)
        self._update_max_tokens_max()

    def update_max_tokens_range(self):
        self._update_max_tokens_max()


class ConfigPanel(QWidget):
    """左侧配置：参数配置面板"""
    startup_discovery_done = Signal(list)  # list of Provider

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("configPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(200)
        self.setMaximumWidth(320)
        layout = QVBoxLayout(self)
        self.params_tab = ParamsTab()
        self.params_tab.set_providers(load_providers())
        layout.addWidget(self.params_tab)

        cfg = load_config()
        self.params_tab.set_config(cfg)
        self.startup_discovery_done.connect(self._apply_startup_discovery_result)
        self._run_startup_discovery()

    def _run_startup_discovery(self):
        """启动时在后台为每个端点获取模型列表"""
        providers = load_providers()
        if not providers:
            return

        def work():
            updated = False
            updated_providers = []
            for i, p in enumerate(providers):
                if not p.endpoint or not p.api_key:
                    updated_providers.append(p)
                    continue
                try:
                    models = model_discovery.get_models_sync(
                        p.endpoint, p.api_key, use_cache=True, models_url=p.models_url
                    )
                    if models:
                        updated_providers.append(Provider(
                            id=p.id, name=p.name, endpoint=p.endpoint, api_key=p.api_key,
                            models=models, model_max_tokens=dict(p.model_max_tokens),
                            models_url=p.models_url,
                        ))
                        updated = True
                    else:
                        updated_providers.append(p)
                except Exception:
                    updated_providers.append(p)
            if updated:
                self.startup_discovery_done.emit(updated_providers)

        threading.Thread(target=work, daemon=True).start()

    def _apply_startup_discovery_result(self, providers):
        full = load_config()
        save_providers(providers, full)
        self.params_tab.set_providers(providers)

    def set_init_connected(self, connected):
        self.params_tab.set_init_connected(connected)

    def get_api_key(self):
        p = self.params_tab.get_current_provider()
        return p.api_key if p else ""

    def get_base_url(self):
        p = self.params_tab.get_current_provider()
        return p.endpoint if p else config.DEFAULT_CONFIG["base_url"]

    def get_model(self):
        return self.params_tab.get_model()

    def get_current_provider_id(self):
        return self.params_tab.get_current_provider_id()

    def get_max_tokens(self):
        return self.params_tab.get_max_tokens()

    def get_temperature(self):
        return self.params_tab.get_temperature()

    def get_stream(self):
        return self.params_tab.get_stream()

    def get_thinking_enabled(self):
        return self.params_tab.get_thinking_enabled()

    def get_dark_mode(self):
        return self.params_tab.get_dark_mode()

    def set_config(self, cfg):
        self.params_tab.set_providers(load_providers())
        self.params_tab.set_config(cfg)

    def update_max_tokens_range(self):
        self.params_tab.update_max_tokens_range()

    @property
    def model_combo(self):
        return self.params_tab.model_combo

    @property
    def init_btn(self):
        return self.params_tab.init_btn

    @property
    def test_btn(self):
        return self.params_tab.test_btn

    @property
    def save_btn(self):
        return self.params_tab.save_btn

    @property
    def dark_check(self):
        return self.params_tab.dark_check


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
