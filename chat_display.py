"""对话显示模块"""

import tkinter as tk

import config
from message_components import (
    UserMessageFrame, ThinkingFrame, AIMainTitleFrame, AIAnswerFrame,
    update_scroll_region, create_mousewheel_binding
)


class ConversationPair:
    """对话对类，封装对话对的创建和显示逻辑"""

    def __init__(self, parent_frame, pair_index, user_msg_index,
                 checkbox_toggle_callback, text_font, canvas=None, delete_callback=None):
        """初始化对话对"""
        self.parent_frame = parent_frame
        self.pair_index = pair_index
        self.user_msg_index = user_msg_index
        self.checkbox_toggle_callback = checkbox_toggle_callback
        self.text_font = text_font
        self.canvas = canvas
        self.delete_callback = delete_callback

        # 获取当前主题
        theme = config.get_theme()

        # 创建对话对的Frame容器
        self.pair_frame = tk.Frame(parent_frame, bg=theme["COLOR_BG_PAIR"],
                                   relief=tk.SOLID, borderwidth=1)
        self.pair_frame.pack(fill=tk.X, padx=10, pady=5)

        # 左侧：选择框和删除按钮
        self._create_control_panel(theme)

        # 右侧：对话内容区域
        self.content_frame = tk.Frame(self.pair_frame, bg=theme["COLOR_BG_CHAT"])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 初始化消息组件
        self.user_frame = None
        self.main_title_frame = None  # AI主标题
        self.thinking_frame = None
        self.answer_frame = None      # AI回答（最终回答）

        # AI消息索引（将在AI消息显示时更新）
        self.ai_msg_index = None
        
        # 思考模式状态（用于流式响应）
        self.thinking_enabled = False

        # 如果提供了canvas，绑定滚轮事件到整个对话对
        if self.canvas:
            # 为整个pair_frame绑定
            create_mousewheel_binding(self.pair_frame, self.canvas)
            # 为content_frame绑定
            create_mousewheel_binding(self.content_frame, self.canvas)

    def _create_control_panel(self, theme):
        """创建控制面板（复选框和删除按钮）"""
        checkbox_frame = tk.Frame(self.pair_frame, bg=theme["COLOR_BG_PAIR"],
                                 width=config.CHECKBOX_FRAME_WIDTH)
        checkbox_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        checkbox_frame.pack_propagate(False)

        # 创建Checkbutton
        self.checkbox_var = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(checkbox_frame, variable=self.checkbox_var,
                                       bg=theme["COLOR_BG_PAIR"],
                                       activebackground=theme["COLOR_BG_PAIR"],
                                       command=lambda: self.checkbox_toggle_callback(
                                           self.pair_index, self.checkbox_var))
        self.checkbox.pack(anchor=tk.NW, pady=5)

        # 创建删除按钮（悬停时显示，放在复选框下面）
        if self.delete_callback:
            self.delete_button = tk.Button(
                checkbox_frame,
                text="🗑️",
                font=("Segoe UI", 10),
                fg=theme["COLOR_TEXT_MEDIUM_GRAY"],
                bg=theme["COLOR_BG_PAIR"],
                activebackground=theme["COLOR_BUTTON_RED"],
                activeforeground="white",
                relief=tk.FLAT,
                cursor="hand2",
                width=3,
                command=lambda: self.delete_callback(self.pair_index),
                anchor="nw"
            )
            # 初始隐藏
            self.delete_button.pack_forget()

            # 绑定悬停事件
            def on_enter(e):
                self.delete_button.pack(anchor=tk.NW, pady=(0, 5))

            def on_leave(e):
                self.pair_frame.after(100, self._check_and_hide_delete_button)

            def on_button_enter(e):
                theme = config.get_theme()
                self.delete_button.config(fg=theme["COLOR_BUTTON_RED"])

            def on_button_leave(e):
                theme = config.get_theme()
                self.delete_button.config(fg=theme["COLOR_TEXT_MEDIUM_GRAY"])
                self.pair_frame.after(100, self._check_and_hide_delete_button)

            self.pair_frame.bind("<Enter>", on_enter)
            self.pair_frame.bind("<Leave>", on_leave)
            self.delete_button.bind("<Enter>", on_button_enter)
            self.delete_button.bind("<Leave>", on_button_leave)

    def display_user_message(self, message):
        """显示用户消息"""
        # 创建或重用用户消息Frame
        if self.user_frame is None:
            self.user_frame = UserMessageFrame(self.content_frame, self.text_font, self.canvas)
            self.user_frame.pack(fill=tk.X, pady=(0, 5))
        else:
            self.user_frame.clear()

        # 设置用户消息
        self.user_frame.set_message(message, self.canvas)

        # 更新滚动区域
        if self.canvas:
            update_scroll_region(self.canvas, self.content_frame)

    def display_ai_message(self, ai_reply, reasoning_content, thinking_enabled, ai_msg_index):
        """显示AI消息（非流式）"""
        self.ai_msg_index = ai_msg_index

        # 显示主标题
        if self.main_title_frame is None:
            self.main_title_frame = AIMainTitleFrame(self.content_frame, self.text_font, self.canvas)
            self.main_title_frame.pack(fill=tk.X, pady=(0, 5))
        else:
            self.main_title_frame.clear()

        self.main_title_frame.set_title(thinking_enabled, self.canvas)

        # 显示思考过程（如果有）
        if reasoning_content and thinking_enabled:
            if self.thinking_frame is None:
                self.thinking_frame = ThinkingFrame(self.content_frame, self.text_font, self.canvas)
                self.thinking_frame.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))  # 添加缩进
            else:
                self.thinking_frame.clear()

            self.thinking_frame.set_thinking(reasoning_content, self.canvas)

        # 显示AI回答
        if self.answer_frame is None:
            self.answer_frame = AIAnswerFrame(self.content_frame, self.text_font, self.canvas)
            # 根据是否有思考过程决定缩进
            if thinking_enabled and reasoning_content:
                self.answer_frame.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))
            else:
                self.answer_frame.pack(fill=tk.X, pady=(0, 5))
        else:
            self.answer_frame.clear()

        self.answer_frame.set_message(ai_reply, thinking_enabled, self.canvas)

        # 更新滚动区域
        if self.canvas:
            update_scroll_region(self.canvas, self.content_frame)

    def start_ai_stream(self, thinking_enabled):
        """开始流式显示AI响应"""
        # 保存thinking_enabled状态
        self.thinking_enabled = thinking_enabled
        
        # 准备主标题
        if self.main_title_frame is None:
            self.main_title_frame = AIMainTitleFrame(self.content_frame, self.text_font, self.canvas)
            self.main_title_frame.pack(fill=tk.X, pady=(0, 5))
        else:
            self.main_title_frame.clear()

        self.main_title_frame.set_title(thinking_enabled, self.canvas)

        # 准备思考过程Frame（如果需要）
        if thinking_enabled:
            if self.thinking_frame is None:
                self.thinking_frame = ThinkingFrame(self.content_frame, self.text_font, self.canvas)
                self.thinking_frame.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))
            else:
                self.thinking_frame.clear()

        # 准备AI回答Frame
        if self.answer_frame is None:
            self.answer_frame = AIAnswerFrame(self.content_frame, self.text_font, self.canvas)
            # 初始位置先不确定，在finish_ai_stream中确定
        else:
            self.answer_frame.clear()

    def insert_thinking_chunk(self, chunk, content_frame):
        """插入思考内容块（流式显示时使用）"""
        if self.thinking_frame:
            self.thinking_frame.insert_thinking(chunk, self.canvas)
            update_scroll_region(self.canvas, content_frame)

    def insert_answer_chunk(self, chunk, content_frame, char_count):
        """插入回答内容块（流式显示时使用）"""
        if self.answer_frame:
            # 如果是第一个chunk，确定位置并显示标题（如果有思考过程）
            if not hasattr(self.answer_frame, 'packed'):
                if self.thinking_enabled:
                    self.answer_frame.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))
                    # 显示"💡 最终回答"标题
                    self.answer_frame.show_header("💡 最终回答")
                else:
                    self.answer_frame.pack(fill=tk.X, pady=(0, 5))
                self.answer_frame.packed = True

            self.answer_frame.insert_message(chunk, self.canvas)

            # 每10个字符或每行更新一次
            if char_count % config.SCROLL_UPDATE_THRESHOLD == 0 or '\n' in chunk:
                update_scroll_region(self.canvas, content_frame)

    def finish_ai_stream(self, full_response, reasoning_content, thinking_enabled,
                         ai_msg_index, content_frame):
        """完成流式显示，重新渲染Markdown"""
        self.ai_msg_index = ai_msg_index

        # 思考过程部分已经在流式响应中使用了正确的格式，不需要重新渲染

        # 重新渲染AI回答（完整Markdown）
        if self.answer_frame is None:
            self.answer_frame = AIAnswerFrame(self.content_frame, self.text_font, self.canvas)
            if thinking_enabled and reasoning_content and self.thinking_frame is not None:
                self.answer_frame.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))
            else:
                self.answer_frame.pack(fill=tk.X, pady=(0, 5))

        self.answer_frame.set_message(full_response, thinking_enabled, self.canvas)

        # 更新滚动区域
        update_scroll_region(self.canvas, content_frame)

    def set_selected(self, selected):
        """设置选择状态"""
        theme = config.get_theme()
        if selected:
            is_dark = theme["COLOR_BG_MAIN"] == config.DARK_THEME["COLOR_BG_MAIN"]
            if is_dark:
                selected_bg = "#3d3d3d"
            else:
                selected_bg = "#e8f4f8"
            self.pair_frame.config(bg=selected_bg)
            self.checkbox.config(bg=selected_bg, activebackground=selected_bg)
        else:
            self.pair_frame.config(bg=theme["COLOR_BG_PAIR"])
            self.checkbox.config(bg=theme["COLOR_BG_PAIR"],
                               activebackground=theme["COLOR_BG_PAIR"])

    def get_pair_info(self):
        """获取对话对信息字典"""
        return {
            'selected': self.checkbox_var.get(),
            'user_msg_index': self.user_msg_index,
            'ai_msg_index': self.ai_msg_index,
            'pair_frame': self.pair_frame,
            'checkbox_var': self.checkbox_var,
            'checkbox': self.checkbox
        }

    def destroy(self):
        """销毁对话对"""
        if self.user_frame:
            self.user_frame.destroy()
        if self.main_title_frame:
            self.main_title_frame.destroy()
        if self.thinking_frame:
            self.thinking_frame.destroy()
        if self.answer_frame:
            self.answer_frame.destroy()
        self.pair_frame.destroy()

    def _check_and_hide_delete_button(self):
        """检查鼠标是否仍在frame或按钮上，如果不是则隐藏删除按钮"""
        try:
            if not hasattr(self, 'delete_button') or not hasattr(self, 'pair_frame'):
                return

            x, y = self.pair_frame.winfo_pointerxy()
            widget_x = self.pair_frame.winfo_rootx()
            widget_y = self.pair_frame.winfo_rooty()
            widget_width = self.pair_frame.winfo_width()
            widget_height = self.pair_frame.winfo_height()

            # 检查鼠标是否在frame内
            if widget_x <= x <= widget_x + widget_width and widget_y <= y <= widget_y + widget_height:
                return

            # 检查鼠标是否在按钮上
            try:
                btn_x = self.delete_button.winfo_rootx()
                btn_y = self.delete_button.winfo_rooty()
                btn_width = self.delete_button.winfo_width()
                btn_height = self.delete_button.winfo_height()
                if btn_x <= x <= btn_x + btn_width and btn_y <= y <= btn_y + btn_height:
                    return
            except:
                pass

            # 如果都不在，隐藏按钮
            self.delete_button.pack_forget()
        except:
            pass