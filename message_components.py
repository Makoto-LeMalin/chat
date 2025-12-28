"""对话消息组件模块"""

import tkinter as tk
from datetime import datetime
import config
import markdown_renderer


def update_scroll_region(canvas, content_frame):
    """更新Canvas滚动区域并滚动到底部"""
    content_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.yview_moveto(1.0)


def bind_mousewheel_to_canvas(widget, canvas):
    """为widget及其所有子widget绑定滚轮事件到Canvas"""
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    # 为当前widget绑定
    widget.bind("<MouseWheel>", on_mousewheel)

    # 递归绑定所有子widget
    for child in widget.winfo_children():
        bind_mousewheel_to_canvas(child, canvas)


def bind_text_mousewheel(text_widget, canvas):
    """绑定Text widget的滚轮事件到Canvas"""
    def on_text_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    text_widget.bind("<MouseWheel>", on_text_mousewheel)


def create_mousewheel_binding(widget, canvas):
    """为widget创建滚轮绑定，返回事件处理器"""
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    widget.bind("<MouseWheel>", on_mousewheel)
    return on_mousewheel


class BaseMessageFrame:
    """基础消息Frame类"""

    def __init__(self, parent, bg_color, font, padding=10):
        """初始化基础消息Frame"""
        self.parent = parent
        self.bg_color = bg_color
        self.font = font
        self.padding = padding

        # 获取当前主题
        theme = config.get_theme()

        # 创建主Frame
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.bind_mousewheel_handler = None  # 存储滚轮事件处理器

        # 创建Text widget
        self.text_widget = tk.Text(self.frame, wrap=tk.WORD, font=font,
                                  bg=bg_color, fg=theme["COLOR_TEXT_DARK"],
                                  insertbackground=theme["COLOR_TEXT_DARK"],
                                  relief=tk.FLAT, padx=padding, pady=padding,
                                  width=1)

        # 配置Text widget的样式标签
        markdown_renderer.configure_text_tags(self.text_widget)

        self.text_widget.pack(fill=tk.X, expand=False)

        # 初始化文本宽度跟踪
        self._last_text_width = None

        # 绑定宽度变化事件
        def on_text_configure(event):
            if event.widget == self.text_widget:
                current_width = event.width
                if current_width > 1 and current_width != self._last_text_width:
                    self._last_text_width = current_width
                    self.text_widget.after(50, self.update_height)

        self.text_widget.bind('<Configure>', on_text_configure)

    def update_height(self):
        """根据内容更新高度"""
        self.text_widget.update_idletasks()

        # 获取逻辑行数
        end_index = self.text_widget.index(tk.END)
        logical_line_count = int(end_index.split('.')[0])

        try:
            # 计算显示行数
            if logical_line_count > 0:
                last_line_num = logical_line_count - 1
                last_line_end = self.text_widget.index(f"{last_line_num}.end")
                display_line_count = self.text_widget.count("1.0", last_line_end, "displaylines")[0]
            else:
                display_line_count = 0
        except Exception as e:
            display_line_count = int(self.text_widget.index(tk.END).split('.')[0])

        # 设置高度
        self.text_widget.configure(height=display_line_count)

        # 验证最后一行是否完全可见
        self.text_widget.update_idletasks()
        if logical_line_count > 0:
            last_line_num = logical_line_count - 1
            last_line_end = self.text_widget.index(f"{last_line_num}.end")
            last_line_end_bbox = self.text_widget.bbox(last_line_end)

            if last_line_end_bbox is not None:
                widget_height_pixels = self.text_widget.winfo_height()
                last_line_y = last_line_end_bbox[1]
                last_line_height = last_line_end_bbox[3]
                last_line_bottom = last_line_y + last_line_height
                bottom_space = widget_height_pixels - last_line_bottom

                first_line_bbox = self.text_widget.bbox("1.0")
                if first_line_bbox is not None:
                    first_line_height = first_line_bbox[3]

                    if first_line_height > 0:
                        if bottom_space < 0 or (bottom_space < last_line_height * 0.5):
                            needed_space = abs(bottom_space) if bottom_space < 0 else (last_line_height * 0.5 - bottom_space)
                            additional_lines = int(needed_space / first_line_height) + 1
                            adjusted_height = display_line_count + additional_lines
                            self.text_widget.configure(height=adjusted_height)

    def pack(self, **kwargs):
        """包装Frame的pack方法"""
        return self.frame.pack(**kwargs)

    def pack_forget(self):
        """隐藏Frame"""
        self.frame.pack_forget()

    def destroy(self):
        """销毁Frame"""
        self.frame.destroy()

    def set_content(self, content, tag=""):
        """设置文本内容"""
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        markdown_renderer.render_markdown(self.text_widget, content, tag)
        self.update_height()
        self.text_widget.configure(state=tk.DISABLED)

    def insert_content(self, content, tag=""):
        """插入文本内容"""
        self.text_widget.configure(state=tk.NORMAL)
        markdown_renderer.render_markdown(self.text_widget, content, tag)
        self.update_height()
        self.text_widget.configure(state=tk.DISABLED)

    def clear(self):
        """清空内容"""
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        self.update_height()

    def bind_mousewheel(self, canvas):
        """绑定滚轮事件到Canvas"""
        # 为整个Frame绑定
        if canvas and not self.frame.bind_mousewheel_handler:
            self.frame.bind_mousewheel_handler = create_mousewheel_binding(self.frame, canvas)

        # 为Text widget绑定
        bind_text_mousewheel(self.text_widget, canvas)


class UserMessageFrame(BaseMessageFrame):
    """用户消息Frame"""

    def __init__(self, parent, font, canvas=None):
        """初始化用户消息Frame"""
        theme = config.get_theme()
        super().__init__(parent, theme["COLOR_BG_CHAT"], font)

        # 创建标题行Frame，使用单独的pady来控制上下边距
        self.header_frame = tk.Frame(self.frame, bg=theme["COLOR_BG_CHAT"])
        self.header_frame.pack(fill=tk.X, pady=(self.padding, 0))

        # 添加标题行
        self.header_text = tk.Text(self.header_frame, wrap=tk.NONE, font=("Segoe UI", 10, "bold"),
                                  bg=theme["COLOR_BG_CHAT"], fg=config.COLOR_STATUS_BLUE,
                                  relief=tk.FLAT, height=1, padx=self.padding, pady=0)
        self.header_text.pack(fill=tk.X)
        self.header_text.configure(state=tk.DISABLED)

        # 调整主文本widget的边距
        self.text_widget.pack_forget()
        self.text_widget.pack(fill=tk.X, expand=False, pady=(0, self.padding))

        if canvas:
            self.bind_mousewheel(canvas)
            # 为header_frame和header_text也绑定滚轮
            create_mousewheel_binding(self.header_frame, canvas)
            bind_text_mousewheel(self.header_text, canvas)

    def set_message(self, message, canvas=None):
        """设置用户消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.header_text.configure(state=tk.NORMAL)
        self.header_text.delete(1.0, tk.END)
        self.header_text.insert(tk.END, f"👤 我 ({timestamp})")
        self.header_text.configure(state=tk.DISABLED)

        self.set_content(message, "user_message")

        if canvas:
            self.bind_mousewheel(canvas)


class AIMainTitleFrame:
    """AI主标题Frame（独立组件，显示🤖 DeepSeek (时间)）"""

    def __init__(self, parent, font, canvas=None):
        """初始化AI主标题Frame"""
        self.parent = parent
        self.font = font

        # 获取当前主题
        theme = config.get_theme()

        # 创建主Frame
        self.frame = tk.Frame(parent, bg=theme["COLOR_BG_CHAT"])

        # 创建标题行
        self.header_text = tk.Text(self.frame, wrap=tk.NONE, font=("Segoe UI", 10, "bold"),
                                  bg=theme["COLOR_BG_CHAT"], fg=config.COLOR_STATUS_RED,
                                  relief=tk.FLAT, height=1, padx=10, pady=5)
        self.header_text.pack(fill=tk.X)
        self.header_text.configure(state=tk.DISABLED)

        if canvas:
            self.bind_mousewheel(canvas)

    def set_title(self, thinking_enabled, canvas=None):
        """设置主标题"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.header_text.configure(state=tk.NORMAL)
        self.header_text.delete(1.0, tk.END)
        self.header_text.insert(tk.END, f"🤖 DeepSeek ({timestamp})")
        self.header_text.configure(state=tk.DISABLED)

        if canvas:
            self.bind_mousewheel(canvas)

    def pack(self, **kwargs):
        """包装Frame的pack方法"""
        return self.frame.pack(**kwargs)

    def pack_forget(self):
        """隐藏Frame"""
        self.frame.pack_forget()

    def destroy(self):
        """销毁Frame"""
        self.frame.destroy()

    def clear(self):
        """清空内容"""
        self.header_text.configure(state=tk.NORMAL)
        self.header_text.delete(1.0, tk.END)
        self.header_text.configure(state=tk.DISABLED)

    def bind_mousewheel(self, canvas):
        """绑定滚轮事件到Canvas"""
        create_mousewheel_binding(self.frame, canvas)
        bind_text_mousewheel(self.header_text, canvas)


class ThinkingFrame(BaseMessageFrame):
    """思考过程Frame"""

    def __init__(self, parent, font, canvas=None):
        """初始化思考过程Frame"""
        theme = config.get_theme()
        # 使用 FONT_CODE 作为默认字体，因为思考内容使用 thinking_content 标签（FONT_CODE）
        super().__init__(parent, theme["COLOR_BG_CHAT"], config.FONT_CODE)

        # 创建标题行Frame，使用单独的pady来控制上下边距
        self.header_frame = tk.Frame(self.frame, bg=theme["COLOR_BG_CHAT"])
        self.header_frame.pack(fill=tk.X, pady=(self.padding, 0))

        # 添加标题行
        self.header_text = tk.Text(self.header_frame, wrap=tk.NONE, font=("Segoe UI", 10, "bold"),
                                  bg=theme["COLOR_BG_CHAT"], fg=config.COLOR_STATUS_PURPLE,
                                  relief=tk.FLAT, height=1, padx=self.padding, pady=0)
        self.header_text.pack(fill=tk.X)
        self.header_text.configure(state=tk.DISABLED)

        # 调整主文本widget的边距
        self.text_widget.pack_forget()
        self.text_widget.pack(fill=tk.X, expand=False, pady=(0, self.padding))

        if canvas:
            self.bind_mousewheel(canvas)
            # 为header_frame和header_text也绑定滚轮
            create_mousewheel_binding(self.header_frame, canvas)
            bind_text_mousewheel(self.header_text, canvas)

    def update_height(self):
        """根据内容更新高度，添加额外一行以确保最后一行完全显示"""
        self.text_widget.update_idletasks()

        # 获取逻辑行数
        end_index = self.text_widget.index(tk.END)
        logical_line_count = int(end_index.split('.')[0])

        try:
            # 计算显示行数
            if logical_line_count > 0:
                last_line_num = logical_line_count - 1
                last_line_end = self.text_widget.index(f"{last_line_num}.end")
                display_line_count = self.text_widget.count("1.0", last_line_end, "displaylines")[0]
            else:
                display_line_count = 0
        except Exception as e:
            display_line_count = int(self.text_widget.index(tk.END).split('.')[0])

        # 添加额外一行以确保最后一行完全显示
        display_line_count += 1

        # 设置高度
        self.text_widget.configure(height=display_line_count)

    def set_thinking(self, content, canvas=None):
        """设置思考内容"""
        self.header_text.configure(state=tk.NORMAL)
        self.header_text.delete(1.0, tk.END)
        self.header_text.insert(tk.END, "🧠 思考过程")
        self.header_text.configure(state=tk.DISABLED)

        self.set_content(content, "thinking_content")

        if canvas:
            self.bind_mousewheel(canvas)

    def insert_thinking(self, content, canvas=None):
        """流式插入思考内容"""
        if self.header_text.get(1.0, tk.END).strip() == "":
            self.header_text.configure(state=tk.NORMAL)
            self.header_text.delete(1.0, tk.END)
            self.header_text.insert(tk.END, "🧠 思考过程")
            self.header_text.configure(state=tk.DISABLED)

        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, content, "thinking_content")
        self.update_height()
        self.text_widget.configure(state=tk.DISABLED)

        if canvas:
            self.bind_mousewheel(canvas)


class AIAnswerFrame(BaseMessageFrame):
    """AI回答Frame（用于显示最终回答）"""

    def __init__(self, parent, font, canvas=None):
        """初始化AI回答Frame"""
        theme = config.get_theme()
        super().__init__(parent, theme["COLOR_BG_CHAT"], font)

        # 创建标题行Frame，使用单独的pady来控制上下边距
        self.header_frame = tk.Frame(self.frame, bg=theme["COLOR_BG_CHAT"])
        self.header_frame.pack(fill=tk.X, pady=(self.padding, 0))

        # 添加标题行（初始隐藏）
        self.header_text = tk.Text(self.header_frame, wrap=tk.NONE, font=("Segoe UI", 10, "bold"),
                                  bg=theme["COLOR_BG_CHAT"], fg=config.COLOR_STATUS_GREEN,
                                  relief=tk.FLAT, height=1, padx=self.padding, pady=0)
        self.header_text.pack(fill=tk.X)
        self.header_text.configure(state=tk.DISABLED)
        self.header_text.pack_forget()  # 初始隐藏

        # 调整主文本widget的边距
        self.text_widget.pack_forget()
        self.text_widget.pack(fill=tk.X, expand=False, pady=(0, self.padding))

        if canvas:
            self.bind_mousewheel(canvas)
            # 为header_frame和header_text也绑定滚轮
            create_mousewheel_binding(self.header_frame, canvas)
            bind_text_mousewheel(self.header_text, canvas)

    def update_height(self):
        """根据内容更新高度，添加额外一行以确保最后一行完全显示"""
        self.text_widget.update_idletasks()

        # 获取逻辑行数
        end_index = self.text_widget.index(tk.END)
        logical_line_count = int(end_index.split('.')[0])

        try:
            # 计算显示行数
            if logical_line_count > 0:
                last_line_num = logical_line_count - 1
                last_line_end = self.text_widget.index(f"{last_line_num}.end")
                display_line_count = self.text_widget.count("1.0", last_line_end, "displaylines")[0]
            else:
                display_line_count = 0
        except Exception as e:
            display_line_count = int(self.text_widget.index(tk.END).split('.')[0])

        # 添加额外一行以确保最后一行完全显示
        display_line_count += 1

        # 设置高度
        self.text_widget.configure(height=display_line_count)

    def set_message(self, message, thinking_enabled=False, canvas=None):
        """设置AI回答内容"""
        # 如果有思考过程，显示"💡 最终回答"标题
        if thinking_enabled:
            self.header_text.configure(state=tk.NORMAL)
            self.header_text.delete(1.0, tk.END)
            self.header_text.insert(tk.END, "💡 最终回答")
            self.header_text.configure(state=tk.DISABLED)
            self.header_text.pack(fill=tk.X, pady=(self.padding, 0))
        else:
            self.header_text.pack_forget()

        self.set_content(message, "ai_message")

        if canvas:
            self.bind_mousewheel(canvas)

    def insert_message(self, content, canvas=None):
        """流式插入AI回答内容"""
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, content)
        self.update_height()
        self.text_widget.configure(state=tk.DISABLED)

        if canvas:
            self.bind_mousewheel(canvas)

    def show_header(self, text):
        """显示标题"""
        self.header_text.configure(state=tk.NORMAL)
        self.header_text.delete(1.0, tk.END)
        self.header_text.insert(tk.END, text)
        self.header_text.configure(state=tk.DISABLED)
        self.header_text.pack(fill=tk.X, pady=(self.padding, 0))

    def clear(self):
        """清空内容，包括标题"""
        super().clear()
        self.header_text.pack_forget()