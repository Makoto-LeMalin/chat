"""Qt 对话区域：无坐标限制的 QScrollArea + 对话对组件"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTextEdit,
    QCheckBox, QPushButton, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtGui import QFont
import config


def _md_to_html(text):
    """简单将 Markdown 转为 HTML 供 QTextEdit 显示（可后续接 markdown 库）"""
    import markdown
    try:
        html = markdown.markdown(text, extensions=['extra', 'nl2br'])
        return html if html else text.replace('\n', '<br>')
    except Exception:
        return text.replace('\n', '<br>').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class ConversationPairWidget(QFrame):
    """单个对话对：用户消息 + AI 标题/思考/回答。无高度限制。"""
    checkbox_toggled = Signal(int, bool)
    delete_requested = Signal(int)

    def __init__(self, parent, pair_index, user_msg_index, checkbox_callback, delete_callback):
        super().__init__(parent)
        self.setObjectName("pairFrame")
        self.pair_index = pair_index
        self.user_msg_index = user_msg_index
        self.ai_msg_index = None
        self.checkbox_callback = checkbox_callback
        self.delete_callback = delete_callback
        self.thinking_enabled = False

        theme = config.get_theme()
        self.setStyleSheet(f"""
            QFrame#pairFrame {{
                background-color: {theme["COLOR_BG_PAIR"]};
                border: 1px solid {theme["COLOR_TEXT_GRAY"]};
                border-radius: 4px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        # 左侧：复选框 + 删除
        left = QWidget()
        left.setStyleSheet(f"background-color: {theme['COLOR_BG_PAIR']};")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left.setFixedWidth(config.CHECKBOX_FRAME_WIDTH + 10)
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._on_check)
        left_layout.addWidget(self.checkbox)
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setObjectName("pairDeleteBtn")
        self.delete_btn.setFixedSize(32, 32)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {theme['COLOR_TEXT_MEDIUM_GRAY']}; border: none; font-size: 14pt; padding: 0px; }}
            QPushButton:hover {{ background-color: {theme['COLOR_BUTTON_RED']}; }}
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.pair_index))
        self.delete_btn.installEventFilter(self)
        left_layout.addWidget(self.delete_btn)
        left_layout.addStretch()
        layout.addWidget(left)

        # 右侧：对话内容（与原版一致：用户消息、AI 标题、思考/回答可有 20px 左缩进）
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(5, 0, 0, 0)
        content_layout.setSpacing(5)

        self.user_header = QLabel()
        self.user_header.setStyleSheet(f"color: {theme['COLOR_STATUS_BLUE']}; font-weight: bold; font-size: 10pt; background: transparent;")
        self.user_content = QTextEdit()
        self.user_content.setReadOnly(True)
        self.user_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.user_content.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._style_text_edit(self.user_content)
        content_layout.addWidget(self.user_header)
        content_layout.addWidget(self.user_content)

        self.ai_title = QLabel()
        self.ai_title.setStyleSheet(f"color: {theme['COLOR_STATUS_RED']}; font-weight: bold; font-size: 10pt; background: transparent;")
        content_layout.addWidget(self.ai_title)

        self.thinking_wrap = QWidget()
        thinking_layout = QVBoxLayout(self.thinking_wrap)
        thinking_layout.setContentsMargins(20, 0, 0, 0)
        thinking_layout.setSpacing(2)
        self.thinking_header = QLabel()
        self.thinking_header.setStyleSheet(f"color: {theme['COLOR_STATUS_PURPLE']}; font-weight: bold; font-size: 10pt; background: transparent;")
        self.thinking_content = QTextEdit()
        self.thinking_content.setReadOnly(True)
        self.thinking_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.thinking_content.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._style_text_edit(self.thinking_content)
        thinking_layout.addWidget(self.thinking_header)
        thinking_layout.addWidget(self.thinking_content)
        content_layout.addWidget(self.thinking_wrap)

        self.answer_wrap = QWidget()
        self.answer_layout = QVBoxLayout(self.answer_wrap)
        self.answer_layout.setContentsMargins(0, 0, 0, 0)
        self.answer_layout.setSpacing(2)
        self.answer_header = QLabel()
        self.answer_header.setStyleSheet(f"color: {theme['COLOR_STATUS_GREEN']}; font-weight: bold; font-size: 10pt; background: transparent;")
        self.answer_content = QTextEdit()
        self.answer_content.setReadOnly(True)
        self.answer_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.answer_content.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._style_text_edit(self.answer_content)
        self.answer_layout.addWidget(self.answer_header)
        self.answer_layout.addWidget(self.answer_content)
        content_layout.addWidget(self.answer_wrap)

        self._hide_ai_parts()
        layout.addWidget(self.content, 1)

        for te in (self.user_content, self.thinking_content, self.answer_content):
            te.installEventFilter(self)
        self.content.installEventFilter(self)
        self.installEventFilter(self)

    def _style_text_edit(self, w):
        theme = config.get_theme()
        w.setStyleSheet(f"""
            QTextEdit {{ background-color: {theme["COLOR_BG_CHAT"]}; color: {theme["COLOR_TEXT_DARK"]}; border: none; }}
        """)
        # 固定像素换行，由 _fit_text_height 设置 setLineWrapColumnOrWidth，使渲染宽度始终等于气泡宽度
        w.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)

    def _content_width_for(self, text_edit):
        """获取用于文档排版的可用宽度；优先用气泡实际宽度(width-2*frame)，避免用错别框的 viewport。"""
        te_w = text_edit.width() - text_edit.frameWidth() * 2
        if te_w > 0:
            return te_w
        w = text_edit.viewport().width()
        if w > 0:
            return w
        p = text_edit.parentWidget()
        while p and w <= 0:
            w = p.size().width()
            if w > 0 and getattr(p, "layout", None) and p.layout():
                m = p.layout().contentsMargins()
                w = w - m.left() - m.right()
            p = p.parentWidget()
        return max(w, 200)

    def _fit_text_height(self, text_edit):
        """根据文档内容高度设置 QTextEdit 高度；渲染宽度与气泡一致（FixedPixelWidth + setLineWrapColumnOrWidth）。"""
        doc = text_edit.document()
        content_w = self._content_width_for(text_edit)
        text_edit.setLineWrapColumnOrWidth(content_w)
        doc.setTextWidth(content_w)
        doc.adjustSize()
        # adjustSize() 会令文档采用“理想宽度”，需再次设回以保证渲染与气泡一致
        doc.setTextWidth(content_w)
        h = doc.size().height()
        margin = doc.documentMargin() * 2
        frame = text_edit.frameWidth() * 2
        total = int(h + margin + frame + 4)
        total = max(24, min(total, 50000))
        text_edit.setMinimumHeight(total)
        text_edit.setMaximumHeight(total)

    def refresh_theme(self):
        """切换主题后重新应用颜色"""
        theme = config.get_theme()
        self.setStyleSheet(f"""
            QFrame#pairFrame {{
                background-color: {theme["COLOR_BG_PAIR"]};
                border: 1px solid {theme["COLOR_TEXT_GRAY"]};
                border-radius: 4px;
            }}
        """)
        self.user_header.setStyleSheet(f"color: {theme['COLOR_STATUS_BLUE']}; font-weight: bold; background: transparent;")
        self.ai_title.setStyleSheet(f"color: {theme['COLOR_STATUS_RED']}; font-weight: bold; background: transparent;")
        self.thinking_header.setStyleSheet(f"color: {theme['COLOR_STATUS_PURPLE']}; font-weight: bold; background: transparent;")
        self.answer_header.setStyleSheet(f"color: {theme['COLOR_STATUS_GREEN']}; font-weight: bold; background: transparent;")
        left = self.layout().itemAt(0).widget()
        if left:
            left.setStyleSheet(f"background-color: {theme['COLOR_BG_PAIR']};")
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {theme['COLOR_TEXT_MEDIUM_GRAY']}; border: none; font-size: 14pt; padding: 0px; }}
            QPushButton:hover {{ background-color: {theme['COLOR_BUTTON_RED']}; }}
        """)
        for te in (self.user_content, self.thinking_content, self.answer_content):
            self._style_text_edit(te)

    def _hide_ai_parts(self):
        self.ai_title.hide()
        self.thinking_wrap.hide()
        self.answer_wrap.hide()

    def _on_check(self, state):
        self.checkbox_toggled.emit(self.pair_index, state == Qt.Checked)

    def eventFilter(self, obj, event):
        if not hasattr(self, "user_content"):
            return super().eventFilter(obj, event)
        if obj in (self.user_content, self.thinking_content, self.answer_content):
            if event.type() == QEvent.Resize and hasattr(event, "oldSize") and event.oldSize().width() != event.size().width():
                QTimer.singleShot(0, lambda t=obj: self._fit_text_height(t))
        elif obj == self.content:
            if event.type() == QEvent.Resize and hasattr(event, "oldSize") and event.oldSize().width() != event.size().width():
                for te in (self.user_content, self.thinking_content, self.answer_content):
                    if te.isVisible():
                        QTimer.singleShot(0, lambda t=te: self._fit_text_height(t))
        return super().eventFilter(obj, event)

    def _schedule_fit(self, text_edit):
        QTimer.singleShot(0, lambda: self._fit_text_height(text_edit))

    def display_user_message(self, message):
        self.user_header.setText(f"👤 我 ({datetime.now().strftime('%H:%M:%S')})")
        self.user_content.setHtml(_md_to_html(message))
        self._schedule_fit(self.user_content)
        self.user_header.show()
        self.user_content.show()

    def display_ai_message(self, ai_reply, reasoning_content, thinking_enabled, ai_msg_index):
        self.ai_msg_index = ai_msg_index
        self.thinking_enabled = thinking_enabled
        theme = config.get_theme()
        self.ai_title.setText(f"🤖 DeepSeek ({datetime.now().strftime('%H:%M:%S')})")
        self.ai_title.show()
        if reasoning_content and thinking_enabled:
            self.thinking_header.setText("🧠 思考过程")
            self.thinking_content.setHtml(_md_to_html(reasoning_content))
            self._schedule_fit(self.thinking_content)
            self.thinking_wrap.show()
            self.answer_header.setText("💡 最终回答")
            self.answer_header.show()
            self.answer_layout.setContentsMargins(20, 0, 0, 0)
        else:
            self.answer_header.hide()
            self.answer_layout.setContentsMargins(0, 0, 0, 0)
        self.answer_content.setHtml(_md_to_html(ai_reply))
        self._schedule_fit(self.answer_content)
        self.answer_wrap.show()

    def start_ai_stream(self, thinking_enabled):
        self.thinking_enabled = thinking_enabled
        self.ai_title.setText(f"🤖 DeepSeek ({datetime.now().strftime('%H:%M:%S')})")
        self.ai_title.show()
        self.thinking_header.setText("🧠 思考过程")
        self.thinking_content.clear()
        self.answer_content.clear()
        self._fit_text_height(self.thinking_content)
        self._fit_text_height(self.answer_content)
        if thinking_enabled:
            self.thinking_wrap.show()
            self.answer_layout.setContentsMargins(20, 0, 0, 0)
        else:
            self.thinking_wrap.hide()
            self.answer_layout.setContentsMargins(0, 0, 0, 0)
        self.answer_header.hide()
        self.answer_wrap.show()

    def insert_thinking_chunk(self, chunk):
        self.thinking_content.setPlainText(self.thinking_content.toPlainText() + chunk)
        self._schedule_fit(self.thinking_content)
        self._scroll_chat_to_bottom()

    def insert_answer_chunk(self, chunk, char_count):
        if char_count == 0 and self.thinking_enabled:
            self.answer_header.setText("💡 最终回答")
            self.answer_header.show()
            self.answer_layout.setContentsMargins(20, 0, 0, 0)
        self.answer_wrap.show()
        self.answer_content.setPlainText(self.answer_content.toPlainText() + chunk)
        self._schedule_fit(self.answer_content)
        self._scroll_chat_to_bottom()

    def finish_ai_stream(self, full_response, reasoning_content, thinking_enabled, ai_msg_index):
        self.ai_msg_index = ai_msg_index
        if reasoning_content and thinking_enabled:
            self.thinking_content.setHtml(_md_to_html(reasoning_content))
            self.answer_header.setText("💡 最终回答")
            self.answer_header.show()
            self.answer_layout.setContentsMargins(20, 0, 0, 0)
        else:
            self.answer_layout.setContentsMargins(0, 0, 0, 0)
        self.answer_wrap.show()
        self.answer_content.setHtml(_md_to_html(full_response))
        self._schedule_fit(self.answer_content)
        if reasoning_content and thinking_enabled:
            self._schedule_fit(self.thinking_content)
        self._scroll_chat_to_bottom()

    def _scroll_chat_to_bottom(self):
        sa = self._find_scroll_area()
        if sa:
            sa.verticalScrollBar().setValue(sa.verticalScrollBar().maximum())

    def _find_scroll_area(self):
        p = self.parentWidget()
        while p:
            if isinstance(p, QScrollArea):
                return p
            p = p.parentWidget()
        return None

    def get_pair_info(self):
        return {
            'selected': self.checkbox.isChecked(),
            'user_msg_index': self.user_msg_index,
            'ai_msg_index': self.ai_msg_index,
            'pair_frame': self,
            'checkbox_var': None,
            'checkbox': self.checkbox
        }

    def set_selected(self, selected):
        self.checkbox.setChecked(selected)
        theme = config.get_theme()
        bg = theme.get("COLOR_BG_PAIR_SELECTED", theme["COLOR_BG_PAIR"]) if selected else theme["COLOR_BG_PAIR"]
        border_left = f"3px solid {theme['COLOR_BUTTON_BLUE']}" if selected else "3px solid transparent"
        self.setStyleSheet(f"""
            QFrame#pairFrame {{
                background-color: {bg};
                border: 1px solid {theme["COLOR_TEXT_GRAY"]};
                border-left: {border_left};
                border-radius: 4px;
            }}
        """)


class ChatAreaWidget(QWidget):
    """聊天主区域：欢迎语 + QScrollArea（内为对话对列表）。无坐标限制。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chatArea")
        self.setAttribute(Qt.WA_StyledBackground, True)
        theme = config.get_theme()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("")

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(8)
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

        self.welcome = QLabel()
        self.welcome.setWordWrap(True)
        self.welcome.setText("""🤖 欢迎使用 DeepSeek AI Assistant!

请在左侧配置您的 API 密钥，然后点击"连接"按钮开始使用。

功能特点：
• 支持流式响应，实时查看生成过程
• 可调整生成参数（长度、随机性）
• 保存和加载配置
• 导出对话记录

开始对话吧！""")
        self._update_welcome_style()
        self.show_welcome()

    def _update_welcome_style(self):
        theme = config.get_theme()
        self.welcome.setStyleSheet(f"color: {theme['COLOR_TEXT_DARK']}; padding: 20px; font-size: 11pt;")

    def show_welcome(self):
        if self.content_layout.indexOf(self.welcome) >= 0:
            return
        self.content_layout.insertStretch(0)
        self.content_layout.insertWidget(1, self.welcome)
        self.content_layout.addStretch()

    def hide_welcome(self):
        idx = self.content_layout.indexOf(self.welcome)
        if idx >= 0:
            self.content_layout.removeWidget(self.welcome)
            self.welcome.setParent(None)
            if self.content_layout.count() > 0:
                self.content_layout.takeAt(0)

    def add_pair_widget(self, pair_widget):
        self.hide_welcome()
        self.content_layout.insertWidget(self.content_layout.count() - 1, pair_widget)
        self._scroll_to_bottom()

    def remove_pair_widget(self, pair_widget, scroll_after=False):
        self.content_layout.removeWidget(pair_widget)
        pair_widget.deleteLater()
        if self.content_layout.count() <= 1:
            self.show_welcome()
        if scroll_after:
            self._scroll_to_bottom()

    def clear_pairs(self):
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.show_welcome()

    def _scroll_to_bottom(self):
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def scroll_to_bottom(self):
        """公开方法：滚动到底部（如加载对话后调用）。"""
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
