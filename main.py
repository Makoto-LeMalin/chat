"""DeepSeek AI Assistant - 主程序（Qt / PySide6，无坐标限制）"""

import os
import json
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QMessageBox, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QShortcut, QKeySequence

import config
import api_client
import history_manager
from qt_ui import get_stylesheet, apply_theme_to_app
from qt_chat import ChatAreaWidget, ConversationPairWidget
from qt_sidebar import ConfigPanel, HistoryPanel, CollapsibleSidebar


class WorkerSignals(QObject):
    """后台线程与主线程通信"""
    stream_thinking = Signal(str)
    stream_answer = Signal(str)
    stream_done = Signal(str, str, bool, int)
    response_done = Signal(object)
    error = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek AI Assistant")
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        self.config_file = config.CONFIG_FILE
        self.config = self._load_config()
        config.set_theme(self.config.get("dark_mode", False))

        self.api_client = None
        self.history_manager = history_manager.HistoryManager()
        self.conversation_history = []
        self.conversation_pairs = {}
        self.current_pair_index = -1
        self.signals = WorkerSignals()

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)

        # 左侧：可折叠配置栏（与原版顺序一致）
        self.config_panel = ConfigPanel(self)
        self.config_panel.set_config(self.config)
        self.config_panel.model_combo.currentTextChanged.connect(self._on_model_changed)
        self.config_panel.save_btn.clicked.connect(self._save_config)
        self.config_panel.dark_check.stateChanged.connect(self._on_theme_toggle)
        self.config_sidebar = CollapsibleSidebar(
            self.config_panel,
            expanded_width=config.SIDEBAR_WIDTH,
            initial_collapsed=self.config.get("sidebar_collapsed", False),
            object_name="sidebar",
        )
        self.config_sidebar.toggled.connect(self._save_sidebar_state)
        layout.addWidget(self.config_sidebar)

        # 中间偏左：可折叠历史栏（与原版顺序一致：配置 | 历史 | 聊天）
        self.history_panel = HistoryPanel(self)
        self.history_panel.refresh_btn.clicked.connect(self._refresh_history)
        self.history_panel.load_requested.connect(self._load_history_from_file)
        self.history_panel.delete_requested.connect(self._delete_history_file)
        self.history_sidebar = CollapsibleSidebar(
            self.history_panel,
            expanded_width=config.HISTORY_SIDEBAR_WIDTH,
            initial_collapsed=self.config.get("history_sidebar_collapsed", False),
            object_name="historySidebar",
        )
        self.history_sidebar.toggled.connect(self._save_sidebar_state)
        layout.addWidget(self.history_sidebar)

        # 中间：标题 + 聊天区 + 输入
        center = QWidget()
        center.setObjectName("centerPanel")
        center.setAttribute(Qt.WA_StyledBackground, True)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.addWidget(QLabel("DeepSeek AI Assistant"))
        self.status_label = QLabel("未连接")
        self.status_indicator = QLabel("●")
        self._last_status_theme_key = "COLOR_STATUS_RED"
        self._set_status("未连接", config.get_theme()[self._last_status_theme_key])
        title_layout.addStretch()
        title_layout.addWidget(self.status_indicator)
        title_layout.addWidget(self.status_label)
        center_layout.addWidget(title_bar)

        self.chat_area = ChatAreaWidget(self)
        center_layout.addWidget(self.chat_area, 1)

        input_row = QWidget()
        input_layout = QVBoxLayout(input_row)
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入消息...")
        self.input_text.setMaximumHeight(120)
        input_layout.addWidget(self.input_text)
        btn_row = QHBoxLayout()
        clear_chat_btn = QPushButton("🗑️ 清空对话")
        clear_chat_btn.setProperty("colorRole", "red")
        clear_chat_btn.clicked.connect(self._clear_chat)
        btn_row.addWidget(clear_chat_btn)
        export_btn = QPushButton("📤 导出对话")
        export_btn.setProperty("colorRole", "blue")
        export_btn.clicked.connect(self._export_chat)
        btn_row.addWidget(export_btn)
        clear_input_btn = QPushButton("📋 清空输入")
        clear_input_btn.clicked.connect(self.input_text.clear)
        btn_row.addWidget(clear_input_btn)
        self.send_btn = QPushButton("🚀 发送消息")
        self.send_btn.setEnabled(False)
        self.send_btn.setProperty("colorRole", "green")
        self.send_btn.clicked.connect(self._send_message)
        btn_row.addWidget(self.send_btn)
        input_layout.addLayout(btn_row)
        center_layout.addWidget(input_row)

        layout.addWidget(center, 1)

        self.config_panel.init_btn.clicked.connect(self._init_client_sync)
        self.config_panel.test_btn.clicked.connect(self._test_connection)
        self._connect_stream_signals()
        self._refresh_history()
        self._apply_styles()
        QShortcut(QKeySequence("Ctrl+Return"), self.input_text, self._send_message)

        if self.config.get("api_key") and self.config.get("base_url"):
            self._init_client_sync()

    def _load_config(self):
        out = config.DEFAULT_CONFIG.copy()
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k in out:
                        if k in data:
                            out[k] = data[k]
            except Exception as e:
                print(f"加载配置失败: {e}")
        return out

    def _save_config(self):
        self.config = self._build_config_dict()
        try:
            d = os.path.dirname(self.config_file)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def _build_config_dict(self):
        return {
            "api_key": self.config_panel.get_api_key(),
            "base_url": self.config_panel.get_base_url(),
            "model": self.config_panel.get_model(),
            "max_tokens": self.config_panel.get_max_tokens(),
            "temperature": self.config_panel.get_temperature(),
            "stream": self.config_panel.get_stream(),
            "thinking_enabled": self.config_panel.get_thinking_enabled(),
            "dark_mode": self.config_panel.get_dark_mode(),
        }

    def _apply_styles(self):
        self.setStyleSheet(get_stylesheet())

    def _save_sidebar_state(self, _collapsed=None):
        """保存左右侧栏折叠状态到配置"""
        try:
            current = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    current = json.load(f)
            current["sidebar_collapsed"] = self.config_sidebar.is_collapsed()
            current["history_sidebar_collapsed"] = self.history_sidebar.is_collapsed()
            current["dark_mode"] = self.config_panel.get_dark_mode()
            d = os.path.dirname(self.config_file)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _on_theme_toggle(self, _state=None):
        config.set_theme(self.config_panel.get_dark_mode())
        self._apply_styles()
        theme = config.get_theme()
        if getattr(self, "_last_status_theme_key", None):
            self.status_indicator.setStyleSheet(f"color: {theme[self._last_status_theme_key]};")
        for pair in self.conversation_pairs.values():
            if hasattr(pair, "refresh_theme"):
                pair.refresh_theme()
        if hasattr(self.chat_area, "_update_welcome_style"):
            self.chat_area._update_welcome_style()
        self._refresh_history()
        self.config_panel.set_init_connected(self.api_client is not None)

    def _on_model_changed(self):
        self.config_panel.update_max_tokens_range()

    def _init_client_sync(self):
        api_key = self.config_panel.get_api_key()
        base_url = self.config_panel.get_base_url()
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入 API 密钥")
            return
        try:
            self.api_client = api_client.DeepSeekAPIClient(api_key, base_url)
            self.config = self._build_config_dict()
            self.config["api_key"] = api_key
            self.config["base_url"] = base_url
            try:
                d = os.path.dirname(self.config_file)
                if d:
                    os.makedirs(d, exist_ok=True)
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            self._set_status("已连接", config.get_theme()["COLOR_STATUS_GREEN"], "COLOR_STATUS_GREEN")
            self.send_btn.setEnabled(True)
            self.config_panel.set_init_connected(True)
        except Exception as e:
            self._set_status("连接失败", config.get_theme()["COLOR_STATUS_RED"], "COLOR_STATUS_RED")
            self.api_client = None
            QMessageBox.critical(self, "错误", f"初始化失败: {e}")

    def _test_connection(self):
        if not self.api_client:
            QMessageBox.warning(self, "警告", "请先连接")
            return
        try:
            self._set_status("测试中...", config.get_theme()["COLOR_STATUS_ORANGE"], "COLOR_STATUS_ORANGE")
            self.api_client.test_connection(self.config_panel.get_model())
            self._set_status("连接成功", config.get_theme()["COLOR_STATUS_GREEN"], "COLOR_STATUS_GREEN")
            QMessageBox.information(self, "成功", "API 连接测试成功！")
        except Exception as e:
            self._set_status("测试失败", config.get_theme()["COLOR_STATUS_RED"], "COLOR_STATUS_RED")
            QMessageBox.critical(self, "错误", f"连接测试失败: {e}")

    def _set_status(self, text, color, theme_key=None):
        self.status_label.setText(text)
        if theme_key:
            self._last_status_theme_key = theme_key
        self.status_indicator.setStyleSheet(f"color: {color};")

    def _send_message(self):
        if not self.api_client:
            QMessageBox.warning(self, "警告", "请先连接")
            return
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        self.input_text.clear()
        self._display_user_message(text)
        self.conversation_history.append({"role": "user", "content": text})
        self._set_status("正在生成...", config.get_theme()["COLOR_STATUS_ORANGE"], "COLOR_STATUS_ORANGE")

        params = self.api_client.build_params(
            model=self.config_panel.get_model(),
            messages=[{"role": m["role"], "content": m["content"]} for m in self.conversation_history],
            max_tokens=self.config_panel.get_max_tokens(),
            temperature=self.config_panel.get_temperature(),
            stream=self.config_panel.get_stream(),
            is_reasoner_model=self._is_reasoner_model(),
            thinking_enabled=self.config_panel.get_thinking_enabled(),
        )
        if self.config_panel.get_stream():
            pair = self.conversation_pairs.get(self.current_pair_index)
            if pair is not None:
                pair.start_ai_stream(self.config_panel.get_thinking_enabled())
            threading.Thread(target=self._stream_worker, args=(params,), daemon=True).start()
        else:
            threading.Thread(target=self._response_worker, args=(params,), daemon=True).start()

    def _is_reasoner_model(self):
        return self.config_panel.get_model() == "deepseek-reasoner"

    def _display_user_message(self, message):
        self.current_pair_index = len(self.conversation_pairs)
        user_msg_index = len(self.conversation_history) - 1
        pair = ConversationPairWidget(
            self.chat_area.content,
            self.current_pair_index,
            user_msg_index,
            self._on_checkbox_toggle,
            self._delete_pair,
        )
        pair.display_user_message(message)
        pair.checkbox_toggled.connect(self._on_checkbox_toggle)
        pair.delete_requested.connect(self._delete_pair)
        self.conversation_pairs[self.current_pair_index] = pair
        self.chat_area.add_pair_widget(pair)

    def _on_checkbox_toggle(self, pair_index, checked):
        pass

    def _delete_pair(self, pair_index):
        if pair_index not in self.conversation_pairs:
            return
        r = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条对话对吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return
        pair = self.conversation_pairs.pop(pair_index)
        self.chat_area.remove_pair_widget(pair)
        for idx in sorted(self.conversation_pairs.keys(), reverse=True):
            if idx > pair_index:
                w = self.conversation_pairs.pop(idx)
                w.pair_index = idx - 1
                self.conversation_pairs[idx - 1] = w
        if self.current_pair_index == pair_index:
            self.current_pair_index = -1
        elif self.current_pair_index > pair_index:
            self.current_pair_index -= 1

    def _connect_stream_signals(self):
        self.signals.stream_thinking.connect(self._on_stream_thinking)
        self.signals.stream_answer.connect(self._on_stream_answer)
        self.signals.stream_done.connect(self._on_stream_done)
        self.signals.response_done.connect(self._on_response_done)
        self.signals.error.connect(self._on_error)

    def _on_stream_thinking(self, chunk):
        if self.current_pair_index in self.conversation_pairs:
            self.conversation_pairs[self.current_pair_index].insert_thinking_chunk(chunk)
        QApplication.processEvents()

    def _on_stream_answer(self, chunk):
        if self.current_pair_index in self.conversation_pairs:
            c = chunk
            pair = self.conversation_pairs[self.current_pair_index]
            n = len(pair.answer_content.toPlainText())
            pair.insert_answer_chunk(c, n)
        QApplication.processEvents()

    def _on_stream_done(self, full_response, reasoning_content, thinking_enabled, ai_msg_index):
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response,
            **({"reasoning_content": reasoning_content} if reasoning_content else {}),
        })
        final_ai_idx = len(self.conversation_history) - 1
        if self.current_pair_index in self.conversation_pairs:
            pair = self.conversation_pairs[self.current_pair_index]
            pair.finish_ai_stream(full_response, reasoning_content, thinking_enabled, final_ai_idx)
            pair.ai_msg_index = final_ai_idx
        self._set_status("流式响应完成", config.get_theme()["COLOR_STATUS_GREEN"], "COLOR_STATUS_GREEN")

    def _on_response_done(self, response):
        ai_reply = response.choices[0].message.content
        reasoning = getattr(response.choices[0].message, "reasoning_content", "") or ""
        self.conversation_history.append({
            "role": "assistant",
            "content": ai_reply,
            **({"reasoning_content": reasoning} if reasoning else {}),
        })
        if self.current_pair_index in self.conversation_pairs:
            pair = self.conversation_pairs[self.current_pair_index]
            pair.display_ai_message(
                ai_reply, reasoning, self.config_panel.get_thinking_enabled(),
                len(self.conversation_history) - 1,
            )
            pair.ai_msg_index = len(self.conversation_history) - 1
        self._set_status("已完成", config.get_theme()["COLOR_STATUS_GREEN"], "COLOR_STATUS_GREEN")

    def _on_error(self, msg):
        self._set_status("错误", config.get_theme()["COLOR_STATUS_RED"], "COLOR_STATUS_RED")
        QMessageBox.critical(self, "错误", f"API 请求失败:\n{msg}")

    def _stream_worker(self, params):
        try:
            full_response = ""
            reasoning_content = ""
            stream = self.api_client.create_completion_stream(**params)
            in_thinking = True
            for chunk in stream:
                delta = chunk.choices[0].delta
                if getattr(delta, "reasoning_content", None):
                    reasoning_content += delta.reasoning_content
                    self.signals.stream_thinking.emit(delta.reasoning_content)
                if getattr(delta, "content", None):
                    if in_thinking and reasoning_content:
                        in_thinking = False
                    full_response += delta.content
                    self.signals.stream_answer.emit(delta.content)
            self.signals.stream_done.emit(
                full_response, reasoning_content,
                self.config_panel.get_thinking_enabled(),
                len(self.conversation_history),
            )
        except Exception as e:
            self.signals.error.emit(str(e))

    def _response_worker(self, params):
        try:
            response = self.api_client.create_completion(**params)
            self.signals.response_done.emit(response)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _clear_chat(self):
        if QMessageBox.question(
            self, "确认", "确定要清空对话历史吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return
        for pair in list(self.conversation_pairs.values()):
            self.chat_area.remove_pair_widget(pair)
        self.conversation_pairs.clear()
        self.conversation_history.clear()
        self.current_pair_index = -1
        self.chat_area.clear_pairs()
        theme = config.get_theme()
        key = "COLOR_STATUS_GREEN" if self.api_client else "COLOR_STATUS_RED"
        self._set_status("已连接" if self.api_client else "未连接", theme[key], key)

    def _export_chat(self):
        if not self.conversation_history:
            QMessageBox.warning(self, "警告", "没有对话内容可导出")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出对话",
            self.history_manager.chat_history_dir,
            "Markdown (*.md);;All (*)",
            f"deepseek_chat_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        )
        if not path:
            return
        def gen_title(indices):
            return self._generate_chat_title(indices)
        result, err = self.history_manager.export_chat_to_path(
            path, self.conversation_history,
            {i: p.get_pair_info() for i, p in self.conversation_pairs.items()},
            self.config_panel.get_model(), gen_title,
        )
        if err:
            QMessageBox.critical(self, "错误", err)
        else:
            QMessageBox.information(self, "成功", f"对话已导出到:\n{path}")
            self._refresh_history()

    def _generate_chat_title(self, message_indices=None):
        if not self.api_client or not self.conversation_history:
            return None
        try:
            content = self.history_manager.generate_title_content(
                self.conversation_history, message_indices
            )
            if not content:
                return None
            use_chat = self._is_reasoner_model()
            resp = self.api_client.generate_title(
                [{"role": "user", "content": content}],
                self.config_panel.get_model(), use_chat,
            )
            return self.history_manager.parse_title_from_response(resp)
        except Exception:
            return None

    def _refresh_history(self):
        files = self.history_manager.get_history_files()
        self.history_panel.set_items(files)

    def _delete_history_file(self, filepath, filename):
        """删除历史对话文件"""
        r = QMessageBox.question(
            self, "确认删除",
            f"确定要删除历史对话文件吗？\n\n{filename}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                QMessageBox.information(self, "成功", "历史对话文件已删除")
                self._refresh_history()
            else:
                QMessageBox.warning(self, "警告", "文件不存在")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")

    def _load_history_from_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            imported = self.history_manager.parse_chat_history(content)
            if not imported:
                QMessageBox.warning(self, "警告", "未能解析出对话内容")
                return
            if self.conversation_history:
                r = QMessageBox.question(
                    self, "加载选项",
                    "当前已有对话。\n是 = 追加 | 否 = 替换 | 取消 = 取消",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Cancel,
                )
                if r == QMessageBox.Cancel:
                    return
                if r == QMessageBox.No:
                    self.chat_area.clear_pairs()
                    self.conversation_pairs.clear()
                    self.conversation_history = imported
                    self.current_pair_index = -1
                else:
                    self.conversation_history.extend(imported)
            else:
                self.conversation_history = imported
            base = len(self.conversation_history) - len(imported)
            idx = len(self.conversation_pairs)
            i = 0
            while i < len(imported):
                msg = imported[i]
                if msg["role"] == "user":
                    user_idx = base + i
                    pair = ConversationPairWidget(
                        self.chat_area.content, idx, user_idx,
                        self._on_checkbox_toggle, self._delete_pair,
                    )
                    pair.checkbox_toggled.connect(self._on_checkbox_toggle)
                    pair.delete_requested.connect(self._delete_pair)
                    pair.display_user_message(msg["content"])
                    ai_idx = None
                    if i + 1 < len(imported) and imported[i + 1]["role"] == "assistant":
                        i += 1
                        ai_msg = imported[i]
                        ai_idx = base + i
                        reasoning = ai_msg.get("reasoning_content")
                        pair.display_ai_message(
                            ai_msg["content"], reasoning, bool(reasoning), ai_idx,
                        )
                    self.conversation_pairs[idx] = pair
                    self.chat_area.add_pair_widget(pair)
                    idx += 1
                i += 1
            self.chat_area.scroll_to_bottom()
            QMessageBox.information(self, "成功", f"已加载 {len(imported)} 条对话记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self._send_message()
            return
        super().keyPressEvent(event)


def main():
    # Qt 6 已默认使用 PER_MONITOR_AWARE_V2，无需再调 Windows DPI API，否则易报“拒绝访问”
    app = QApplication([])
    apply_theme_to_app(app)
    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
