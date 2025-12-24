"""对话显示模块"""

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
    
    widget.bind("<MouseWheel>", on_mousewheel)
    
    # 递归绑定所有子widget（除了Text widget，它们有自己的绑定）
    for child in widget.winfo_children():
        if not isinstance(child, tk.Text):
            bind_mousewheel_to_canvas(child, canvas)


def bind_text_mousewheel(text_widget, canvas):
    """绑定Text widget的滚轮事件到Canvas"""
    def on_text_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    text_widget.bind("<MouseWheel>", on_text_mousewheel)


def update_text_height(text_widget):
    """根据内容动态更新Text widget的高度（考虑自动换行）"""
    text_widget.update_idletasks()
    
    # 获取逻辑行数，用于后续计算
    end_index = text_widget.index(tk.END)
    logical_line_count = int(end_index.split('.')[0])
    
    try:
        # 计算到最后一行的显示行数（不包含末尾换行符）
        if logical_line_count > 0:
            last_line_num = logical_line_count - 1
            # 获取最后一行的最后一个字符位置
            last_line_end = text_widget.index(f"{last_line_num}.end")
            # 计算到最后一行的显示行数（不包含末尾换行符）
            display_line_count = text_widget.count("1.0", last_line_end, "displaylines")[0]
        else:
            display_line_count = 0
        
    except Exception as e:
        # 如果count方法失败，回退到原来的方法
        display_line_count = int(text_widget.index(tk.END).split('.')[0])
    
    # 使用显示行数设置高度
    text_widget.configure(height=display_line_count)
    
    # 设置高度后，验证最后一行是否完全可见
    # 使用更安全的方法：检查最后一行的完整显示，而不是基于bottom_space减少高度
    text_widget.update_idletasks()
    if logical_line_count > 0:
        last_line_num = logical_line_count - 1
        last_line_end = text_widget.index(f"{last_line_num}.end")
        last_line_end_bbox_after = text_widget.bbox(last_line_end)
        
        if last_line_end_bbox_after is not None:
            # 获取Text widget的实际高度（像素）
            widget_height_pixels = text_widget.winfo_height()
            # 获取最后一行的完整高度（包括行高）
            last_line_y = last_line_end_bbox_after[1]
            last_line_height = last_line_end_bbox_after[3]
            last_line_bottom = last_line_y + last_line_height
            
            # 计算最后一行底部到widget底部的距离
            bottom_space = widget_height_pixels - last_line_bottom
            
            # 获取第一行的行高，用于计算
            first_line_bbox = text_widget.bbox("1.0")
            if first_line_bbox is not None:
                first_line_height = first_line_bbox[3]
                
                if first_line_height > 0:
                    # 如果最后一行被裁剪（底部空间为负或太小），增加高度
                    # 只增加，不减少，确保内容完整显示
                    if bottom_space < 0 or (bottom_space < last_line_height * 0.5):
                        # 需要增加高度以确保最后一行完全可见
                        needed_space = abs(bottom_space) if bottom_space < 0 else (last_line_height * 0.5 - bottom_space)
                        additional_lines = int(needed_space / first_line_height) + 1
                        adjusted_height = display_line_count + additional_lines
                        text_widget.configure(height=adjusted_height)
                        display_line_count = adjusted_height
    


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
        
        # 左侧：选择框
        checkbox_frame = tk.Frame(self.pair_frame, bg=theme["COLOR_BG_PAIR"], 
                                 width=config.CHECKBOX_FRAME_WIDTH)
        checkbox_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        checkbox_frame.pack_propagate(False)
        
        # 创建Checkbutton
        self.checkbox_var = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(checkbox_frame, variable=self.checkbox_var,
                                       bg=theme["COLOR_BG_PAIR"], 
                                       activebackground=theme["COLOR_BG_PAIR"],
                                       command=lambda: checkbox_toggle_callback(
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
                # 延迟检查，避免在鼠标移动到按钮上时立即隐藏
                self.pair_frame.after(100, self._check_and_hide_delete_button)
            
            def on_button_enter(e):
                # 按钮悬停时改变颜色
                theme = config.get_theme()
                self.delete_button.config(fg=theme["COLOR_BUTTON_RED"])
            
            def on_button_leave(e):
                # 按钮离开时恢复颜色并隐藏
                theme = config.get_theme()
                self.delete_button.config(fg=theme["COLOR_TEXT_MEDIUM_GRAY"])
                self.pair_frame.after(100, self._check_and_hide_delete_button)
            
            self.pair_frame.bind("<Enter>", on_enter)
            self.pair_frame.bind("<Leave>", on_leave)
            self.delete_button.bind("<Enter>", on_button_enter)
            self.delete_button.bind("<Leave>", on_button_leave)
        
        # 右侧：对话内容区域
        content_frame = tk.Frame(self.pair_frame, bg=theme["COLOR_BG_CHAT"])
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Text widget显示对话内容
        self.text_widget = tk.Text(content_frame, wrap=tk.WORD, font=self.text_font,
                                  bg=theme["COLOR_BG_CHAT"], 
                                  fg=theme["COLOR_TEXT_DARK"],
                                  insertbackground=theme["COLOR_TEXT_DARK"],
                                  relief=tk.FLAT, 
                                  padx=10, pady=10, width=1)
        
        # 配置Text widget的样式标签
        markdown_renderer.configure_text_tags(self.text_widget)
        
        self.text_widget.pack(fill=tk.X, expand=False)
        
        # 绑定Text widget的宽度变化事件，当宽度改变时重新计算高度
        self._last_text_width = None
        def on_text_configure(event):
            if event.widget == self.text_widget:
                current_width = event.width
                # 只响应宽度变化，忽略高度变化
                if current_width > 1 and current_width != self._last_text_width:
                    self._last_text_width = current_width
                    # 延迟更新，避免频繁更新
                    self.text_widget.after(50, lambda: update_text_height(self.text_widget))
        
        self.text_widget.bind('<Configure>', on_text_configure)
        
        # 如果提供了canvas，绑定滚轮事件到整个frame及其所有子widget
        # 注意：必须在所有子widget创建完成后才绑定
        if self.canvas:
            bind_mousewheel_to_canvas(self.pair_frame, self.canvas)
        
        # AI消息索引（将在AI消息显示时更新）
        self.ai_msg_index = None
    
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
    
    def display_user_message(self, message, canvas):
        """显示用户消息"""
        # 绑定滚轮事件
        bind_text_mousewheel(self.text_widget, canvas)
        
        # 显示用户消息
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, f"👤 我 ({timestamp})\n", "user_tag")
        markdown_renderer.render_markdown(self.text_widget, message, "user_message")
        
        # 根据内容动态设置高度
        update_text_height(self.text_widget)
        self.text_widget.configure(state=tk.DISABLED)
    
    def display_ai_message(self, ai_reply, reasoning_content, thinking_enabled, 
                          canvas, ai_msg_index):
        """显示AI消息"""
        self.ai_msg_index = ai_msg_index
        
        # 绑定滚轮事件
        bind_text_mousewheel(self.text_widget, canvas)
        
        self.text_widget.configure(state=tk.NORMAL)
        
        # AI消息样式
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.insert(tk.END, f"\n🤖 DeepSeek ({timestamp})\n", "ai_tag")
        
        # 显示思考过程
        if reasoning_content and thinking_enabled:
            self.text_widget.insert(tk.END, "🧠 思考过程:\n", "thinking_tag")
            markdown_renderer.render_markdown(self.text_widget, reasoning_content, 
                                            "thinking_content")
            self.text_widget.insert(tk.END, "\n\n💡 最终回答:\n", "ai_tag")
        
        # 使用Markdown渲染AI回复
        markdown_renderer.render_markdown(self.text_widget, ai_reply, "ai_message")
        self.text_widget.insert(tk.END, f"\n{'─' * config.SEPARATOR_LENGTH}\n", 
                               "separator")
        
        # 根据内容动态设置高度
        update_text_height(self.text_widget)
        self.text_widget.configure(state=tk.DISABLED)
    
    def start_ai_stream(self, thinking_enabled, canvas):
        """开始流式显示AI响应"""
        self.text_widget.configure(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.insert(tk.END, f"\n🤖 DeepSeek ({timestamp})\n", "ai_tag")
        
        # 如果是思考模式，添加思考标签
        if thinking_enabled:
            self.text_widget.insert(tk.END, "🧠 思考过程:\n", "thinking_tag")
            self.text_widget.see(tk.END)
        
        # 绑定滚轮事件
        bind_text_mousewheel(self.text_widget, canvas)
    
    def insert_thinking_chunk(self, chunk, canvas, content_frame):
        """插入思考内容块"""
        self.text_widget.insert(tk.END, chunk, "thinking_content")
        update_text_height(self.text_widget)
        self.text_widget.see(tk.END)
        update_scroll_region(canvas, content_frame)
    
    def insert_answer_chunk(self, chunk, canvas, content_frame, char_count):
        """插入回答内容块"""
        self.text_widget.insert(tk.END, chunk, "ai_message")
        
        # 每10个字符或每行更新一次
        if char_count % config.SCROLL_UPDATE_THRESHOLD == 0 or '\n' in chunk:
            update_text_height(self.text_widget)
            self.text_widget.see(tk.END)
            update_scroll_region(canvas, content_frame)
        else:
            self.text_widget.see(tk.END)
    
    def finish_ai_stream(self, full_response, reasoning_content, thinking_enabled,
                        canvas, content_frame, ai_msg_index):
        """完成流式显示，重新渲染Markdown"""
        import re
        
        self.ai_msg_index = ai_msg_index
        
        # 检查是否包含Markdown格式
        has_markdown = bool(
            re.search(r'(\*\*|__|`|#|>|[-*+]\s)', full_response) or 
            (reasoning_content and re.search(r'(\*\*|__|`|#|>|[-*+]\s)', reasoning_content))
        )
        
        if has_markdown:
            # 记录流式内容结束位置（在插入分隔线之前）
            stream_end_pos = self.text_widget.index(tk.END)
            
            # 查找思考内容和回答的位置
            thinking_start_pos = None
            thinking_end_pos = None
            answer_start_pos = None
            
            # 查找思考内容开始位置（"🧠 思考过程:\n"之后）
            content = self.text_widget.get("1.0", stream_end_pos)
            thinking_marker = "🧠 思考过程:\n"
            answer_marker = "💡 最终回答:\n"
            
            if thinking_marker in content:
                thinking_start_idx = content.find(thinking_marker)
                # thinking_start_pos 应该是标记之后的位置（思考内容开始）
                thinking_start_pos = f"1.0+{thinking_start_idx + len(thinking_marker)}c"
                
                if answer_marker in content:
                    answer_marker_idx = content.find(answer_marker)
                    thinking_end_pos = f"1.0+{answer_marker_idx}c"
                    answer_start_pos = f"1.0+{answer_marker_idx + len(answer_marker)}c"
                else:
                    thinking_end_pos = stream_end_pos
            
            # 重新渲染思考内容
            if reasoning_content and thinking_start_pos and thinking_end_pos:
                # 只删除思考内容，保留 "🧠 思考过程:\n" 标记
                self.text_widget.delete(thinking_start_pos, thinking_end_pos)
                self.text_widget.mark_set("insert", thinking_start_pos)
                markdown_renderer.render_markdown(self.text_widget, reasoning_content, 
                                                "thinking_content")
                
                # 重新查找回答开始位置（answer_marker 应该在重新渲染后的内容中）
                if answer_marker in content:
                    # 重新获取当前内容，查找 answer_marker 的新位置
                    current_pos = self.text_widget.index(tk.END)
                    content_after_render = self.text_widget.get("1.0", current_pos)
                    if answer_marker in content_after_render:
                        answer_marker_idx = content_after_render.find(answer_marker)
                        answer_start_pos = f"1.0+{answer_marker_idx + len(answer_marker)}c"
            
            # 重新渲染回答内容
            if full_response and answer_start_pos:
                current_end_pos = self.text_widget.index(tk.END)
                self.text_widget.delete(answer_start_pos, current_end_pos)
                self.text_widget.mark_set("insert", answer_start_pos)
                markdown_renderer.render_markdown(self.text_widget, full_response, 
                                                "ai_message")
        
        # 插入分隔线
        self.text_widget.insert(tk.END, f"\n{'─' * config.SEPARATOR_LENGTH}\n", 
                               "separator")
        
        # 最终更新高度
        update_text_height(self.text_widget)
        # 确保滚动到底部
        self.text_widget.see(tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        
        # 更新滚动区域
        update_scroll_region(canvas, content_frame)
    
    def set_selected(self, selected):
        """设置选择状态"""
        theme = config.get_theme()
        if selected:
            # 选中时使用稍亮的背景色（根据主题调整）
            # 检查是否为深色主题（通过检查背景色是否等于深色主题的背景色）
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
            'checkbox': self.checkbox,
            'text_widget': self.text_widget
        }

