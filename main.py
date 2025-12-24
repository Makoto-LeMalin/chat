"""主程序 - 使用模块化重构后的代码"""

import ctypes
try:
    # Windows 高DPI支持
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import json
import os
import threading
from datetime import datetime
import config
import ui_components as ui
import chat_display as chat
import markdown_renderer as md
import api_client
import history_manager


class ModernDeepSeekClient:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek AI Assistant")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.configure(bg=config.COLOR_BG_MAIN)
        self.root.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        # 设置窗口图标
        try:
            self.root.iconbitmap(config.ICON_FILE)
        except:
            pass

        # 字体配置
        self.text_font = config.FONT_TEXT
        self.small_font = config.FONT_SMALL

        # API客户端和历史管理器
        self.api_client = None
        self.history_manager = history_manager.HistoryManager()

        # 对话数据
        self.conversation_history = []
        self.conversation_pairs = {}  # 存储ConversationPair对象
        self.current_pair_index = -1
        self.conversation_pair_frames = {}

        # 思考模式变量
        self.thinking_enabled_var = None

        # 加载配置
        self.config_file = config.CONFIG_FILE
        self.config = self.load_config()
        
        # 边栏折叠状态（在配置加载后初始化）
        self.sidebar_collapsed_var = tk.BooleanVar(value=self.config.get("sidebar_collapsed", False))
        self.history_sidebar_collapsed_var = tk.BooleanVar(value=self.config.get("history_sidebar_collapsed", False))
        
        # 初始化主题
        dark_mode = self.config.get("dark_mode", False)
        config.set_theme(dark_mode)
        self.dark_mode_var = tk.BooleanVar(value=dark_mode)

        # 创建UI
        self.create_modern_ui()

        # 尝试自动初始化客户端
        if self.config.get("api_key") and self.config.get("base_url"):
            self.auto_init_client()

        # 初始更新思考模式状态
        self.update_thinking_status()
        
        # 存储UI组件引用以便主题切换
        self.ui_widgets = {}

    def load_config(self):
        """加载配置文件"""
        default_config = config.DEFAULT_CONFIG.copy()

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    for key in default_config:
                        if key in loaded_config:
                            default_config[key] = loaded_config[key]
                print(f"配置已从 {self.config_file} 加载")
            except Exception as e:
                print(f"加载配置失败: {e}")

        return default_config

    def _build_config_dict(self):
        """构建当前配置字典"""
        return {
            "api_key": self.api_key_var.get(),
            "base_url": self.base_url_var.get(),
            "model": self.model_var.get(),
            "max_tokens": self.max_tokens_var.get(),
            "temperature": self.temperature_var.get(),
            "stream": self.stream_var.get(),
            "thinking_enabled": self.thinking_enabled_var.get(),
            "dark_mode": self.dark_mode_var.get(),
            "sidebar_collapsed": self.sidebar_collapsed_var.get(),
            "history_sidebar_collapsed": self.history_sidebar_collapsed_var.get()
        }

    def save_config(self, config_dict=None):
        """保存配置到文件"""
        if config_dict is None:
            config_dict = self._build_config_dict()

        try:
            # 确保config目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def create_modern_ui(self):
        """创建现代化UI"""
        # 主容器
        main_container = tk.Frame(self.root, bg=config.COLOR_BG_MAIN)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 折叠按钮变量
        theme = config.get_theme()
        sidebar_collapsed = self.sidebar_collapsed_var.get()
        
        # 侧边栏（根据初始状态设置宽度）
        sidebar_width = config.SIDEBAR_COLLAPSED_WIDTH if sidebar_collapsed else config.SIDEBAR_WIDTH
        self.sidebar = tk.Frame(main_container, bg=theme["COLOR_BG_CONFIG"], 
                          width=sidebar_width)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.sidebar.pack_propagate(False)
        
        # 侧边栏内容容器（用于折叠/展开）
        self.sidebar_content = tk.Frame(self.sidebar, bg=theme["COLOR_BG_CONFIG"])
        
        # 根据初始状态决定是否显示内容
        if not sidebar_collapsed:
            self.sidebar_content.pack(fill=tk.BOTH, expand=True)
        
        # 折叠按钮（放在边栏右上角，在内容之后创建以确保显示在最上层）
        self.sidebar_toggle_btn = tk.Button(
            self.sidebar,
            text="◀" if not sidebar_collapsed else "▶",
            font=("Segoe UI", 12, "bold"),
            bg=theme["COLOR_BG_CONFIG"],
            fg=theme["COLOR_TEXT_WHITE"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_sidebar,
            width=3
        )
        self.sidebar_toggle_btn.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-5, y=5)
        # 确保按钮显示在最上层
        self.sidebar_toggle_btn.lift()

        # API配置区域（增加顶部间距，避免与折叠按钮重叠）
        config_frame = ui.create_config_frame(self.sidebar_content, "API配置", pack_pady=(65, 5))
        
        # 获取主题颜色
        theme = config.get_theme()
        
        # API密钥
        ui.create_label(config_frame, text="API密钥:", bg=theme["COLOR_BG_SIDEBAR"],
                      fg=config.COLOR_TEXT_GRAY).pack(anchor=tk.W, pady=(5, 0))
        self.api_key_var = tk.StringVar(value=self.config["api_key"])
        self.api_key_entry = ui.create_entry(config_frame, textvariable=self.api_key_var, show="•",
                                       bg=theme["COLOR_BG_INPUT"])
        self.api_key_entry.pack(fill=tk.X, pady=5, ipady=5)

        # API端点
        ui.create_label(config_frame, text="API端点:", bg=theme["COLOR_BG_SIDEBAR"],
                      fg=config.COLOR_TEXT_GRAY).pack(anchor=tk.W, pady=(5, 0))
        self.base_url_var = tk.StringVar(value=self.config["base_url"])
        self.base_url_entry = ui.create_entry(config_frame, textvariable=self.base_url_var,
                                        bg=theme["COLOR_BG_INPUT"])
        self.base_url_entry.pack(fill=tk.X, pady=5, ipady=5)

        # 模型选择
        ui.create_label(config_frame, text="模型:", bg=theme["COLOR_BG_SIDEBAR"],
                      fg=config.COLOR_TEXT_GRAY).pack(anchor=tk.W, pady=(5, 0))
        self.model_var = tk.StringVar(value=self.config["model"])
        model_combo = ui.create_combobox(config_frame, self.model_var, config.MODELS,
                                        command=self.on_model_changed)
        model_combo.pack(fill=tk.X, pady=5, ipady=5)

        # 连接按钮
        btn_frame = tk.Frame(config_frame, bg=theme["COLOR_BG_SIDEBAR"])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        self.init_btn = ui.create_button(btn_frame, "🔗 连接", self.init_client,
                                        bg=config.COLOR_BUTTON_BLUE)
        self.init_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ui.create_button(btn_frame, "🔄 测试", self.test_connection,
                        bg=config.COLOR_BUTTON_GREEN).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 参数设置区域
        param_frame = ui.create_config_frame(self.sidebar_content, "生成参数")

        # 思考模式开关
        if self.thinking_enabled_var is None:
            self.thinking_enabled_var = tk.BooleanVar(
                value=self.config.get("thinking_enabled", False))
        thinking_frame, self.thinking_check = ui.create_frame_with_checkbox(
            param_frame, "思考模式:", self.thinking_enabled_var,
            command=self.on_thinking_mode_toggle)
        
        ui.create_label(param_frame, text="启用深度推理过程",
                       bg=theme["COLOR_BG_SIDEBAR"], fg=config.COLOR_TEXT_LIGHT_GRAY,
                       font=config.FONT_TINY).pack(anchor=tk.W, padx=5, pady=(0, 10))

        # 最大token数
        self.max_tokens_var = tk.IntVar(value=self.config["max_tokens"])
        initial_max = config.MODEL_MAX_TOKENS.get(self.config.get("model"), 8000)
        self.max_tokens_scale = ui.create_scale_with_label(
            param_frame, "最大长度:", self.max_tokens_var, 100, initial_max)
        if self.max_tokens_var.get() > initial_max:
            self.max_tokens_var.set(initial_max)

        # 温度参数
        self.temperature_var = tk.DoubleVar(value=self.config["temperature"])
        ui.create_scale_with_label(param_frame, "随机性:", self.temperature_var,
                                 0.0, 2.0, resolution=0.1)

        # 流式响应开关
        self.stream_var = tk.BooleanVar(value=self.config["stream"])
        ui.create_checkbutton(param_frame, "流式响应", self.stream_var,
                            bg=theme["COLOR_BG_SIDEBAR"]).pack(anchor=tk.W, pady=5)

        # 夜间模式开关
        theme_frame, self.dark_mode_check = ui.create_frame_with_checkbox(
            self.sidebar_content, "🌙 夜间模式:", self.dark_mode_var,
            command=self.on_theme_toggle)
        theme_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # 保存配置按钮
        ui.create_button(self.sidebar_content, "💾 保存配置", self.save_current_config,
                        bg=config.COLOR_BUTTON_PURPLE, pady=10).pack(
                        fill=tk.X, padx=10, pady=10)

        # 折叠按钮变量
        history_collapsed = self.history_sidebar_collapsed_var.get()
        theme = config.get_theme()
        
        # 历史记录栏（根据初始状态设置宽度）
        history_sidebar_width = config.SIDEBAR_COLLAPSED_WIDTH if history_collapsed else config.HISTORY_SIDEBAR_WIDTH
        self.history_sidebar = tk.Frame(main_container, bg=config.COLOR_BG_CONFIG,
                                  width=history_sidebar_width)
        self.history_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.history_sidebar.pack_propagate(False)
        
        # 历史边栏内容容器（用于折叠/展开）
        self.history_sidebar_content = tk.Frame(self.history_sidebar, bg=config.COLOR_BG_CONFIG)
        
        # 根据初始状态决定是否显示内容
        if not history_collapsed:
            self.history_sidebar_content.pack(fill=tk.BOTH, expand=True)
        
        # 折叠按钮（放在历史栏右上角，在内容之后创建以确保显示在最上层）
        self.history_toggle_btn = tk.Button(
            self.history_sidebar,
            text="◀" if not history_collapsed else "▶",
            font=("Segoe UI", 12, "bold"),
            bg=theme["COLOR_BG_CONFIG"],
            fg=theme["COLOR_TEXT_WHITE"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_history_sidebar,
            width=3
        )
        self.history_toggle_btn.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-5, y=5)
        # 确保按钮显示在最上层
        self.history_toggle_btn.lift()

        ui.create_label(self.history_sidebar_content, text="📚 对话历史", font=config.FONT_MEDIUM,
                       bg=config.COLOR_BG_CONFIG, fg=config.COLOR_TEXT_WHITE).pack(pady=(15, 10))

        ui.create_button(self.history_sidebar_content, "🔄 刷新", self.refresh_history,
                        bg=config.COLOR_BUTTON_BLUE, pady=5).pack(fill=tk.X, padx=10, pady=(0, 10))

        # 历史记录列表
        history_list_frame = tk.Frame(self.history_sidebar_content, bg=config.COLOR_BG_CONFIG)
        history_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.history_canvas, self.history_content, _ = ui.create_scrollable_canvas(
            history_list_frame, bg_color=config.COLOR_BG_SIDEBAR)

        self.history_buttons = []

        # 主聊天区域（放在历史栏右边，占据剩余空间）
        chat_container = tk.Frame(main_container, bg=config.COLOR_BG_MAIN)
        chat_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 聊天标题栏
        title_bar = tk.Frame(chat_container, bg=config.COLOR_BG_CHAT, 
                           height=config.TITLE_BAR_HEIGHT)
        title_bar.pack(fill=tk.X, padx=2, pady=2)
        title_bar.pack_propagate(False)

        ui.create_label(title_bar, text="DeepSeek AI Assistant",
                       font=config.FONT_MEDIUM, bg=config.COLOR_BG_CHAT).pack(
                       side=tk.LEFT, padx=20)

        # 状态指示器
        self.status_indicator = ui.create_label(title_bar, text="●", fg=config.COLOR_STATUS_RED,
                                               font=("Segoe UI", 12), bg=config.COLOR_BG_CHAT)
        self.status_indicator.pack(side=tk.RIGHT, padx=20)
        self.status_label = ui.create_label(title_bar, text="未连接",
                                           font=self.small_font, bg=config.COLOR_BG_CHAT)
        self.status_label.pack(side=tk.RIGHT, padx=(0, 5))

        # 聊天显示区域
        chat_frame = tk.Frame(chat_container, bg=config.COLOR_BG_CHAT)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(2, 0))

        self.chat_canvas, self.chat_content_frame, _ = ui.create_scrollable_canvas(
            chat_frame, bg_color=config.COLOR_BG_CHAT)

        # 输入区域
        input_frame = tk.Frame(chat_container, bg=config.COLOR_BG_CHAT)
        input_frame.pack(fill=tk.X, padx=2, pady=2)

        self.input_text = ui.create_text_widget(input_frame, height=config.INPUT_HEIGHT)
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 5))

        # 输入按钮区域
        btn_frame = tk.Frame(input_frame, bg=config.COLOR_BG_CHAT)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        left_btn_frame = tk.Frame(btn_frame, bg=config.COLOR_BG_CHAT)
        left_btn_frame.pack(side=tk.LEFT)
        ui.create_button(left_btn_frame, "🗑️ 清空对话", self.clear_chat,
                        bg=config.COLOR_BUTTON_RED, padx=15, pady=5).pack(side=tk.LEFT)
        ui.create_button(left_btn_frame, "📤 导出对话", self.export_chat,
                        bg=config.COLOR_BUTTON_BLUE, padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        right_btn_frame = tk.Frame(btn_frame, bg=config.COLOR_BG_CHAT)
        right_btn_frame.pack(side=tk.RIGHT)
        ui.create_button(right_btn_frame, "📋 清空输入", self.clear_input,
                        bg=config.COLOR_BUTTON_GRAY, padx=15, pady=5).pack(side=tk.RIGHT, padx=(5, 0))
        self.send_btn = ui.create_button(right_btn_frame, "🚀 发送消息", self.send_message,
                                        bg=config.COLOR_BUTTON_GREEN, padx=20, pady=5,
                                        state=tk.DISABLED)
        self.send_btn.pack(side=tk.RIGHT, padx=5)

        ui.create_label(btn_frame, text="Ctrl+Enter 发送消息 | Shift+Enter 换行",
                       font=config.FONT_TINY, bg=config.COLOR_BG_CHAT,
                       fg=config.COLOR_TEXT_MEDIUM_GRAY).pack(side=tk.LEFT, padx=(10, 0))

        # 绑定快捷键
        self.input_text.bind("<Control-Return>", lambda e: self.send_message())
        self.input_text.bind("<Shift-Return>", lambda e: None)

        # 设置初始提示
        self.show_welcome_message()
        self.refresh_history()
        
        # 保存chat_container引用，以便后续使用
        self.chat_container = chat_container
        
        # 绑定窗口大小变化事件，更新所有对话对的高度
        self.root.bind('<Configure>', self._on_window_configure)
        self._last_window_width = self.root.winfo_width()

    def show_welcome_message(self):
        """显示欢迎消息"""
        welcome = """🤖 欢迎使用 DeepSeek AI Assistant!

请在左侧配置您的 API 密钥，然后点击"连接"按钮开始使用。

功能特点：
• 支持流式响应，实时查看生成过程
• 可调整生成参数（长度、随机性）
• 保存和加载配置
• 导出对话记录

开始对话吧！"""

        welcome_label = ui.create_label(self.chat_content_frame, text=welcome,
                                       font=self.text_font, bg=config.COLOR_BG_CHAT,
                                       justify=tk.LEFT, padx=20, pady=20)
        welcome_label.pack(fill=tk.X, padx=10, pady=10)

    def on_thinking_mode_toggle(self):
        """思考模式切换回调"""
        if self._is_reasoner_model():
            self.thinking_enabled_var.set(True)
            self.thinking_check.config(state=tk.DISABLED)
        else:
            self.thinking_check.config(state=tk.NORMAL)
        self.update_thinking_status()

    def update_thinking_status(self):
        """更新思考模式状态显示"""
        if self._is_reasoner_model():
            self.thinking_check.config(text="思考模式 (已锁定)")
        else:
            if self.thinking_enabled_var.get():
                self.thinking_check.config(text="思考模式 ✓")
            else:
                self.thinking_check.config(text="思考模式 ✗")

    def on_theme_toggle(self):
        """夜间模式切换回调"""
        dark_mode = self.dark_mode_var.get()
        config.set_theme(dark_mode)
        self._apply_theme()

    def save_sidebar_state_only(self):
        """只保存边栏折叠状态，不保存其他配置"""
        try:
            # 加载当前配置文件（如果存在）
            current_config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)

            # 只更新边栏相关的配置
            current_config["sidebar_collapsed"] = self.sidebar_collapsed_var.get()
            current_config["history_sidebar_collapsed"] = self.history_sidebar_collapsed_var.get()
            # 如果需要，也可以保存主题状态
            current_config["dark_mode"] = self.dark_mode_var.get()

            # 确保config目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            # 保存更新后的配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"保存边栏状态失败: {e}")
            return False

    def toggle_sidebar(self):
        """切换左侧边栏折叠/展开状态"""
        collapsed = not self.sidebar_collapsed_var.get()
        self.sidebar_collapsed_var.set(collapsed)

        if collapsed:
            # 折叠：隐藏内容，缩小宽度
            self.sidebar_content.pack_forget()
            self.sidebar.config(width=config.SIDEBAR_COLLAPSED_WIDTH)
            self.sidebar_toggle_btn.config(text="▶")
        else:
            # 展开：显示内容，恢复宽度
            self.sidebar.config(width=config.SIDEBAR_WIDTH)
            self.sidebar_content.pack(fill=tk.BOTH, expand=True)
            self.sidebar_toggle_btn.config(text="◀")

        # 只保存边栏折叠状态，不保存其他配置
        self.save_sidebar_state_only()

    def toggle_history_sidebar(self):
        """切换右侧历史边栏折叠/展开状态"""
        collapsed = not self.history_sidebar_collapsed_var.get()
        self.history_sidebar_collapsed_var.set(collapsed)

        if collapsed:
            # 折叠：隐藏内容，缩小宽度
            self.history_sidebar_content.pack_forget()
            self.history_sidebar.config(width=config.SIDEBAR_COLLAPSED_WIDTH)
            self.history_toggle_btn.config(text="▶")  # 折叠时显示右箭头
        else:
            # 展开：显示内容，恢复宽度
            self.history_sidebar.config(width=config.HISTORY_SIDEBAR_WIDTH)
            self.history_sidebar_content.pack(fill=tk.BOTH, expand=True)
            self.history_toggle_btn.config(text="◀")  # 展开时显示左箭头

        # 只保存边栏折叠状态，不保存其他配置
        self.save_sidebar_state_only()

    def _apply_theme(self):
        """应用当前主题到所有UI组件"""
        theme = config.get_theme()
        
        # 更新主窗口
        self.root.configure(bg=theme["COLOR_BG_MAIN"])
        
        # 递归更新所有widget的颜色
        self._update_widget_colors(self.root, theme)
        
        # 更新所有对话对的颜色
        for pair in self.conversation_pairs.values():
            if hasattr(pair, 'pair_frame'):
                pair.pair_frame.config(bg=theme["COLOR_BG_PAIR"])
                if hasattr(pair, 'checkbox'):
                    pair.checkbox.config(bg=theme["COLOR_BG_PAIR"], 
                                       activebackground=theme["COLOR_BG_PAIR"])
                if hasattr(pair, 'text_widget'):
                    pair.text_widget.config(bg=theme["COLOR_BG_CHAT"])
                    # 重新配置text tags
                    import markdown_renderer
                    markdown_renderer.configure_text_tags(pair.text_widget)
        
        # 更新输入框
        if hasattr(self, 'input_text'):
            self.input_text.config(bg=theme["COLOR_BG_CHAT"], 
                                 fg=theme["COLOR_TEXT_DARK"],
                                 insertbackground=theme["COLOR_TEXT_DARK"])
        
        # 更新API密钥和API端点输入框
        if hasattr(self, 'api_key_entry'):
            self.api_key_entry.config(bg=theme["COLOR_BG_INPUT"],
                                    fg=theme["COLOR_TEXT_WHITE"],
                                    insertbackground=theme["COLOR_TEXT_WHITE"])
        if hasattr(self, 'base_url_entry'):
            self.base_url_entry.config(bg=theme["COLOR_BG_INPUT"],
                                      fg=theme["COLOR_TEXT_WHITE"],
                                      insertbackground=theme["COLOR_TEXT_WHITE"])
        
        # 更新折叠按钮
        if hasattr(self, 'sidebar_toggle_btn'):
            self.sidebar_toggle_btn.config(bg=theme["COLOR_BG_CONFIG"],
                                         fg=theme["COLOR_TEXT_WHITE"])
        if hasattr(self, 'history_toggle_btn'):
            self.history_toggle_btn.config(bg=theme["COLOR_BG_CONFIG"],
                                         fg=theme["COLOR_TEXT_WHITE"])

    def _update_widget_colors(self, widget, theme):
        """递归更新widget及其子widget的颜色"""
        widget_type = widget.winfo_class()
        
        # 更新Frame的背景色
        if widget_type == 'Frame':
            try:
                current_bg = widget.cget('bg')
                # 根据当前背景色映射到新主题
                if current_bg in [config.LIGHT_THEME["COLOR_BG_MAIN"], config.DARK_THEME["COLOR_BG_MAIN"]]:
                    widget.config(bg=theme["COLOR_BG_MAIN"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_SIDEBAR"], config.DARK_THEME["COLOR_BG_SIDEBAR"]]:
                    widget.config(bg=theme["COLOR_BG_SIDEBAR"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_CONFIG"], config.DARK_THEME["COLOR_BG_CONFIG"]]:
                    widget.config(bg=theme["COLOR_BG_CONFIG"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_CHAT"], config.DARK_THEME["COLOR_BG_CHAT"]]:
                    widget.config(bg=theme["COLOR_BG_CHAT"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_PAIR"], config.DARK_THEME["COLOR_BG_PAIR"]]:
                    widget.config(bg=theme["COLOR_BG_PAIR"])
            except:
                pass
        
        # 更新Label的前景色和背景色
        elif widget_type == 'Label':
            try:
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                
                # 映射背景色
                if current_bg in [config.LIGHT_THEME["COLOR_BG_MAIN"], config.DARK_THEME["COLOR_BG_MAIN"]]:
                    widget.config(bg=theme["COLOR_BG_MAIN"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_SIDEBAR"], config.DARK_THEME["COLOR_BG_SIDEBAR"]]:
                    widget.config(bg=theme["COLOR_BG_SIDEBAR"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_CONFIG"], config.DARK_THEME["COLOR_BG_CONFIG"]]:
                    widget.config(bg=theme["COLOR_BG_CONFIG"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_CHAT"], config.DARK_THEME["COLOR_BG_CHAT"]]:
                    widget.config(bg=theme["COLOR_BG_CHAT"])
                
                # 映射前景色
                if current_fg in [config.LIGHT_THEME["COLOR_TEXT_WHITE"], config.DARK_THEME["COLOR_TEXT_WHITE"]]:
                    widget.config(fg=theme["COLOR_TEXT_WHITE"])
                elif current_fg in [config.LIGHT_THEME["COLOR_TEXT_GRAY"], config.DARK_THEME["COLOR_TEXT_GRAY"]]:
                    widget.config(fg=theme["COLOR_TEXT_GRAY"])
                elif current_fg in [config.LIGHT_THEME["COLOR_TEXT_DARK"], config.DARK_THEME["COLOR_TEXT_DARK"]]:
                    widget.config(fg=theme["COLOR_TEXT_DARK"])
                elif current_fg in [config.LIGHT_THEME["COLOR_TEXT_LIGHT_GRAY"], config.DARK_THEME["COLOR_TEXT_LIGHT_GRAY"]]:
                    widget.config(fg=theme["COLOR_TEXT_LIGHT_GRAY"])
                elif current_fg in [config.LIGHT_THEME["COLOR_TEXT_MEDIUM_GRAY"], config.DARK_THEME["COLOR_TEXT_MEDIUM_GRAY"]]:
                    widget.config(fg=theme["COLOR_TEXT_MEDIUM_GRAY"])
            except:
                pass
        
        # 更新Entry的前景色和背景色
        elif widget_type == 'Entry':
            try:
                current_bg = widget.cget('bg')
                # 检查是否是输入框（使用COLOR_BG_INPUT）
                if current_bg in [config.LIGHT_THEME["COLOR_BG_INPUT"], config.DARK_THEME["COLOR_BG_INPUT"]]:
                    widget.config(bg=theme["COLOR_BG_INPUT"],
                                fg=theme["COLOR_TEXT_WHITE"],
                                insertbackground=theme["COLOR_TEXT_WHITE"])
                else:
                    # 普通输入框使用SIDEBAR颜色
                    widget.config(bg=theme["COLOR_BG_SIDEBAR"], 
                                fg=theme["COLOR_TEXT_WHITE"],
                                insertbackground=theme["COLOR_TEXT_WHITE"])
            except:
                pass
        
        # 更新Checkbutton的背景色和前景色
        elif widget_type == 'Checkbutton':
            try:
                current_bg = widget.cget('bg')
                # 映射背景色
                if current_bg in [config.LIGHT_THEME["COLOR_BG_SIDEBAR"], config.DARK_THEME["COLOR_BG_SIDEBAR"]]:
                    widget.config(bg=theme["COLOR_BG_SIDEBAR"],
                               activebackground=theme["COLOR_BG_SIDEBAR"],
                               fg=theme["COLOR_TEXT_WHITE"],
                               selectcolor=theme["COLOR_BG_CONFIG"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_CONFIG"], config.DARK_THEME["COLOR_BG_CONFIG"]]:
                    widget.config(bg=theme["COLOR_BG_CONFIG"],
                               activebackground=theme["COLOR_BG_CONFIG"],
                               fg=theme["COLOR_TEXT_WHITE"],
                               selectcolor=theme["COLOR_BG_CONFIG"])
            except:
                pass
        
        # 更新Scale的背景色和前景色
        elif widget_type == 'Scale':
            try:
                current_bg = widget.cget('bg')
                # 映射背景色
                if current_bg in [config.LIGHT_THEME["COLOR_BG_SIDEBAR"], config.DARK_THEME["COLOR_BG_SIDEBAR"]]:
                    widget.config(bg=theme["COLOR_BG_SIDEBAR"],
                                fg=theme["COLOR_TEXT_WHITE"],
                                troughcolor=theme["COLOR_BG_CONFIG"],
                                activebackground=theme["COLOR_BG_CONFIG"])
            except:
                pass
        
        # 更新Button的背景色和前景色
        elif widget_type == 'Button':
            try:
                current_bg = widget.cget('bg')
                # 保持按钮的原有颜色主题（如蓝色、绿色等），只更新背景相关的
                if current_bg not in [theme["COLOR_BUTTON_BLUE"], theme["COLOR_BUTTON_GREEN"],
                                     theme["COLOR_BUTTON_RED"], theme["COLOR_BUTTON_PURPLE"],
                                     theme["COLOR_BUTTON_GRAY"], theme["COLOR_STATUS_GREEN"]]:
                    # 如果不是按钮颜色，可能是背景色
                    if current_bg in [config.LIGHT_THEME["COLOR_BG_CONFIG"], config.DARK_THEME["COLOR_BG_CONFIG"]]:
                        widget.config(bg=theme["COLOR_BG_CONFIG"])
                    elif current_bg in [config.LIGHT_THEME["COLOR_BG_SIDEBAR"], config.DARK_THEME["COLOR_BG_SIDEBAR"]]:
                        widget.config(bg=theme["COLOR_BG_SIDEBAR"])
                widget.config(fg=theme["COLOR_TEXT_WHITE"])
            except:
                pass
        
        # 更新Canvas的背景色
        elif widget_type == 'Canvas':
            try:
                current_bg = widget.cget('bg')
                if current_bg in [config.LIGHT_THEME["COLOR_BG_CHAT"], config.DARK_THEME["COLOR_BG_CHAT"]]:
                    widget.config(bg=theme["COLOR_BG_CHAT"])
                elif current_bg in [config.LIGHT_THEME["COLOR_BG_SIDEBAR"], config.DARK_THEME["COLOR_BG_SIDEBAR"]]:
                    widget.config(bg=theme["COLOR_BG_SIDEBAR"])
            except:
                pass
        
        # 递归处理子widget
        try:
            for child in widget.winfo_children():
                self._update_widget_colors(child, theme)
        except:
            pass

    def update_status(self, status, color=config.COLOR_STATUS_RED):
        """更新状态指示器"""
        self.status_indicator.config(fg=color)
        self.status_label.config(text=status)

    def _is_reasoner_model(self):
        """检查当前是否使用 reasoner 模型"""
        return self.model_var.get() == "deepseek-reasoner"

    def _is_thinking_enabled(self):
        """检查思考模式是否启用"""
        return self._is_reasoner_model() or self.thinking_enabled_var.get()

    def on_model_changed(self, event=None):
        """模型切换事件处理"""
        if self._is_reasoner_model():
            self.thinking_enabled_var.set(True)
            self.thinking_check.config(state=tk.DISABLED)
            self.update_thinking_status()
            max_tokens = config.MODEL_MAX_TOKENS['deepseek-reasoner']
            self.max_tokens_scale.config(to=max_tokens)
            if self.max_tokens_var.get() > max_tokens:
                self.max_tokens_var.set(max_tokens)
        else:
            self.thinking_check.config(state=tk.NORMAL)
            self.update_thinking_status()
            max_tokens = config.MODEL_MAX_TOKENS['deepseek-chat']
            self.max_tokens_scale.config(to=max_tokens)
            if self.max_tokens_var.get() > max_tokens:
                self.max_tokens_var.set(max_tokens)

    def auto_init_client(self):
        """自动初始化客户端"""
        api_key = self.config["api_key"]
        base_url = self.config["base_url"]
        thinking_enabled = self.config.get("thinking_enabled", False)

        if api_key and base_url:
            try:
                self.api_client = api_client.DeepSeekAPIClient(api_key, base_url)
                self.update_status("已连接", config.COLOR_STATUS_GREEN)
                self.send_btn.config(state=tk.NORMAL)
                self.init_btn.config(text="✅ 已连接", bg=config.COLOR_STATUS_GREEN)
                self.thinking_enabled_var.set(thinking_enabled)
                self.update_thinking_status()
            except Exception as e:
                self.update_status("连接失败")
                messagebox.showerror("连接失败", f"自动连接失败:\n{str(e)}")

    def init_client(self):
        """初始化OpenAI客户端"""
        api_key = self.api_key_var.get().strip()
        base_url = self.base_url_var.get().strip()

        if not api_key:
            messagebox.showwarning("警告", "请输入API密钥")
            return

        try:
            self.api_client = api_client.DeepSeekAPIClient(api_key, base_url)
            self.config = self._build_config_dict()
            self.config["api_key"] = api_key
            self.config["base_url"] = base_url
            self.save_config(self.config)

            self.update_status("已连接", config.COLOR_STATUS_GREEN)
            self.send_btn.config(state=tk.NORMAL)
            self.init_btn.config(text="✅ 已连接", bg=config.COLOR_STATUS_GREEN)
            self.update_thinking_status()
            messagebox.showinfo("成功", "客户端初始化成功！")
        except Exception as e:
            self.update_status("连接失败")
            messagebox.showerror("错误", f"初始化失败: {str(e)}")
            self.api_client = None

    def test_connection(self):
        """测试API连接"""
        if not self.api_client:
            messagebox.showwarning("警告", "请先初始化客户端")
            return

        try:
            self.update_status("测试中...", config.COLOR_STATUS_ORANGE)
            response = self.api_client.test_connection(self.model_var.get())
            if response:
                self.update_status("连接成功", config.COLOR_STATUS_GREEN)
                messagebox.showinfo("成功", f"API连接测试成功！\n模型: {self.model_var.get()}")
        except Exception as e:
            self.update_status("测试失败")
            messagebox.showerror("错误", f"连接测试失败: {str(e)}")

    def save_current_config(self):
        """保存当前配置"""
        if self.save_config():
            messagebox.showinfo("成功", "配置已保存！")
        else:
            messagebox.showerror("错误", "保存配置失败")

    def send_message(self):
        """发送消息"""
        if not self.api_client:
            messagebox.showwarning("警告", "请先初始化客户端")
            return

        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return

        thread = threading.Thread(target=self._send_message_thread, args=(user_input,))
        thread.daemon = True
        thread.start()

    def _send_message_thread(self, user_input):
        """实际发送消息的线程函数"""
        try:
            self.root.after(0, self._display_user_message, user_input)
            self.conversation_history.append({"role": "user", "content": user_input})

            # 构建API消息
            api_messages = [{"role": msg["role"], "content": msg["content"]}
                          for msg in self.conversation_history]

            params = self.api_client.build_params(
                model=self.model_var.get(),
                messages=api_messages,
                max_tokens=self.max_tokens_var.get(),
                temperature=self.temperature_var.get(),
                stream=self.stream_var.get(),
                is_reasoner_model=self._is_reasoner_model(),
                thinking_enabled=self.thinking_enabled_var.get()
            )

            print(f"API调用参数: {params}")

            if self.stream_var.get():
                self.root.after(0, self._display_ai_stream, params)
            else:
                self.root.after(0, self._display_ai_response, params)

            self.root.after(0, self.clear_input)
        except Exception as e:
            self.root.after(0, self._display_error, str(e))

    def _display_user_message(self, message):
        """显示用户消息"""
        self.current_pair_index = len(self.conversation_pairs)
        user_msg_index = len(self.conversation_history)

        # 使用ConversationPair类创建对话对
        pair = chat.ConversationPair(
            self.chat_content_frame,
            self.current_pair_index,
            user_msg_index,
            self._on_checkbox_toggle,
            self.text_font,
            self.chat_canvas,
            delete_callback=self._delete_conversation_pair
        )

        pair.display_user_message(message, self.chat_canvas)

        # 存储对话对
        self.conversation_pairs[self.current_pair_index] = pair
        self.conversation_pair_frames[self.current_pair_index] = pair.pair_frame

        # 更新滚动区域
        chat.update_scroll_region(self.chat_canvas, self.chat_content_frame)
        self.update_status("正在生成...", config.COLOR_STATUS_ORANGE)

    def _display_ai_response(self, params):
        """显示非流式AI响应"""
        try:
            response = self.api_client.create_completion(**params)
            ai_reply = response.choices[0].message.content

            reasoning_content = ""
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content

            # 保存对话历史
            msg = {"role": "assistant", "content": ai_reply}
            if reasoning_content:
                msg["reasoning_content"] = reasoning_content
            self.conversation_history.append(msg)

            # 显示AI消息
            if self.current_pair_index >= 0 and self.current_pair_index in self.conversation_pairs:
                pair = self.conversation_pairs[self.current_pair_index]
                pair.display_ai_message(
                    ai_reply, reasoning_content, self._is_thinking_enabled(),
                    self.chat_canvas, len(self.conversation_history) - 1
                )
                chat.update_scroll_region(self.chat_canvas, self.chat_content_frame)

            tokens = response.usage.total_tokens if response.usage else 'N/A'
            self.update_status(f"已完成 | Tokens: {tokens}", config.COLOR_STATUS_GREEN)
        except Exception as e:
            self._display_error(str(e))

    def _display_ai_stream(self, params):
        """显示流式AI响应"""
        try:
            if self.current_pair_index < 0 or self.current_pair_index not in self.conversation_pairs:
                return

            pair = self.conversation_pairs[self.current_pair_index]
            pair.start_ai_stream(self._is_thinking_enabled(), self.chat_canvas)

            full_response = ""
            reasoning_content = ""
            in_thinking_phase = True
            thinking_char_count = 0
            answer_char_count = 0

            stream = self.api_client.create_completion_stream(**params)

            for chunk in stream:
                delta = chunk.choices[0].delta

                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    thinking_chunk = delta.reasoning_content
                    reasoning_content += thinking_chunk
                    pair.insert_thinking_chunk(thinking_chunk, self.chat_canvas,
                                             self.chat_content_frame)
                    thinking_char_count += len(thinking_chunk)
                    self.root.update()

                if hasattr(delta, 'content') and delta.content:
                    if in_thinking_phase and reasoning_content:
                        pair.text_widget.insert(tk.END, "\n\n💡 最终回答:\n", "ai_tag")
                        in_thinking_phase = False
                        chat.update_text_height(pair.text_widget)
                        chat.update_scroll_region(self.chat_canvas, self.chat_content_frame)

                    content_chunk = delta.content
                    full_response += content_chunk
                    pair.insert_answer_chunk(content_chunk, self.chat_canvas,
                                            self.chat_content_frame, answer_char_count)
                    answer_char_count += len(content_chunk)
                    self.root.update()

            # 完成流式显示
            pair.finish_ai_stream(
                full_response, reasoning_content, self._is_thinking_enabled(),
                self.chat_canvas, self.chat_content_frame,
                len(self.conversation_history)
            )

            # 保存对话历史
            msg = {"role": "assistant", "content": full_response}
            if reasoning_content:
                msg["reasoning_content"] = reasoning_content
            self.conversation_history.append(msg)
            pair.ai_msg_index = len(self.conversation_history) - 1

            self.update_status("流式响应完成", config.COLOR_STATUS_GREEN)
        except Exception as e:
            self._display_error(str(e))

    def _display_error(self, error_msg):
        """显示错误信息"""
        error_frame = tk.Frame(self.chat_content_frame, bg=config.COLOR_BG_ERROR,
                             relief=tk.SOLID, borderwidth=1)
        error_frame.pack(fill=tk.X, padx=10, pady=5)

        ui.create_label(error_frame, text=f"❌ 错误\n{error_msg}",
                       font=self.text_font, bg=config.COLOR_BG_ERROR,
                       fg=config.COLOR_TEXT_ERROR, justify=tk.LEFT,
                       padx=10, pady=10).pack(fill=tk.X)

        chat.update_scroll_region(self.chat_canvas, self.chat_content_frame)
        self.update_status("错误")
        messagebox.showerror("错误", f"API请求失败:\n{error_msg}")

    def _on_checkbox_toggle(self, pair_index, checkbox_var):
        """Checkbutton切换回调"""
        if pair_index not in self.conversation_pairs:
            return

        pair = self.conversation_pairs[pair_index]
        is_selected = checkbox_var.get()
        pair.set_selected(is_selected)

    def _delete_conversation_pair(self, pair_index):
        """删除指定的对话对"""
        if pair_index not in self.conversation_pairs:
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", "确定要删除这个对话对吗？"):
            return
        
        # 获取要删除的对话对
        pair = self.conversation_pairs[pair_index]
        user_msg_index = pair.user_msg_index
        ai_msg_index = pair.ai_msg_index
        
        # 确定要删除的消息索引（按从大到小的顺序）
        indices_to_delete = []
        if user_msg_index is not None and user_msg_index < len(self.conversation_history):
            indices_to_delete.append(user_msg_index)
        if ai_msg_index is not None and ai_msg_index < len(self.conversation_history):
            indices_to_delete.append(ai_msg_index)
        indices_to_delete = sorted(set(indices_to_delete), reverse=True)  # 从大到小排序
        
        # 从对话历史中删除消息（从后往前删除，避免索引变化问题）
        for idx in indices_to_delete:
            if 0 <= idx < len(self.conversation_history):
                del self.conversation_history[idx]
        
        num_deleted_msgs = len(indices_to_delete)
        
        # 销毁UI元素
        if pair_index in self.conversation_pair_frames:
            self.conversation_pair_frames[pair_index].destroy()
            del self.conversation_pair_frames[pair_index]
        if pair_index in self.conversation_pairs:
            del self.conversation_pairs[pair_index]
        
        # 重新索引后续的对话对
        # 创建新的字典来存储重新索引后的对话对
        new_conversation_pairs = {}
        new_conversation_pair_frames = {}
        
        # 首先更新所有对话对的消息索引（基于删除的消息）
        for idx, pair_obj in self.conversation_pairs.items():
            # 更新消息索引（减去删除的消息数量）
            if pair_obj.user_msg_index is not None:
                adjustment = 0
                for deleted_idx in indices_to_delete:
                    if pair_obj.user_msg_index > deleted_idx:
                        adjustment += 1
                pair_obj.user_msg_index -= adjustment
            
            if pair_obj.ai_msg_index is not None:
                adjustment = 0
                for deleted_idx in indices_to_delete:
                    if pair_obj.ai_msg_index > deleted_idx:
                        adjustment += 1
                pair_obj.ai_msg_index -= adjustment
        
        # 然后重新索引对话对的索引（pair_index）
        for old_idx in sorted(self.conversation_pairs.keys()):
            if old_idx < pair_index:
                # 索引不变
                new_conversation_pairs[old_idx] = self.conversation_pairs[old_idx]
                if old_idx in self.conversation_pair_frames:
                    new_conversation_pair_frames[old_idx] = self.conversation_pair_frames[old_idx]
            elif old_idx > pair_index:
                # 索引减1
                new_idx = old_idx - 1
                pair_obj = self.conversation_pairs[old_idx]
                pair_obj.pair_index = new_idx
                
                # 更新复选框回调中的索引
                pair_obj.checkbox.config(
                    command=lambda idx=new_idx, var=pair_obj.checkbox_var: 
                        self._on_checkbox_toggle(idx, var)
                )
                
                # 更新删除按钮回调中的索引
                if hasattr(pair_obj, 'delete_button') and pair_obj.delete_callback:
                    pair_obj.delete_button.config(
                        command=lambda idx=new_idx: self._delete_conversation_pair(idx)
                    )
                
                new_conversation_pairs[new_idx] = pair_obj
                if old_idx in self.conversation_pair_frames:
                    new_conversation_pair_frames[new_idx] = self.conversation_pair_frames[old_idx]
        
        # 更新字典
        self.conversation_pairs = new_conversation_pairs
        self.conversation_pair_frames = new_conversation_pair_frames
        
        # 更新 current_pair_index
        if self.current_pair_index == pair_index:
            # 如果删除的是当前对话对，设置为-1或前一个
            self.current_pair_index = -1
        elif self.current_pair_index > pair_index:
            # 如果删除的是之前的对话对，索引减1
            self.current_pair_index -= 1
        
        # 如果删除后没有对话对了，显示欢迎消息
        if len(self.conversation_pairs) == 0:
            for widget in self.chat_content_frame.winfo_children():
                widget.destroy()
            self.show_welcome_message()
            self.current_pair_index = -1
        
        # 更新滚动区域
        chat.update_scroll_region(self.chat_canvas, self.chat_content_frame)
        
        # 更新状态
        self.update_status("已连接" if self.api_client else "未连接",
                         config.COLOR_STATUS_GREEN if self.api_client else config.COLOR_STATUS_RED)

    def clear_chat(self):
        """清空对话"""
        if messagebox.askyesno("确认", "确定要清空对话历史吗？"):
            for frame in self.conversation_pair_frames.values():
                frame.destroy()
            self.conversation_pair_frames.clear()
            self.conversation_history.clear()
            self.conversation_pairs.clear()
            self.current_pair_index = -1

            for widget in self.chat_content_frame.winfo_children():
                widget.destroy()

            self.show_welcome_message()
            self.update_status("已连接" if self.api_client else "未连接",
                             config.COLOR_STATUS_GREEN if self.api_client else config.COLOR_STATUS_RED)
            
            # 更新canvas滚动区域并滚动到顶部
            import chat_display as chat
            self.chat_content_frame.update_idletasks()
            self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
            self.chat_canvas.yview_moveto(0.0)

    def clear_input(self):
        """清空输入框"""
        self.input_text.delete("1.0", tk.END)

    def refresh_history(self):
        """刷新历史记录列表"""
        for btn in self.history_buttons:
            btn.destroy()
        self.history_buttons.clear()

        history_files = self.history_manager.get_history_files()
        # 在循环外部获取一次主题，确保所有按钮使用相同的主题
        theme = config.get_theme()

        for mtime, filepath, filename in history_files:
            try:
                title = self.history_manager.extract_title_from_file(filepath)
                if not title:
                    continue

                btn_frame = tk.Frame(self.history_content, bg=config.COLOR_BG_CONFIG,
                                     relief=tk.FLAT)
                btn_frame.pack(fill=tk.X, padx=5, pady=3)

                # 左侧：历史记录按钮
                left_frame = tk.Frame(btn_frame, bg=config.COLOR_BG_CONFIG)
                left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                btn = ui.create_button(left_frame, title[:40] + ('...' if len(title) > 40 else ''),
                                       command=lambda fp=filepath: self.load_history_from_file(fp),
                                       bg=config.COLOR_BG_SIDEBAR, anchor=tk.W,
                                       padx=10, pady=8, cursor="hand2")
                btn.pack(fill=tk.X)

                def on_enter(e, b=btn):
                    b.config(bg=config.COLOR_BUTTON_HOVER)

                def on_leave(e, b=btn):
                    b.config(bg=config.COLOR_BG_SIDEBAR)

                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)

                # 右侧：删除按钮
                delete_btn = tk.Button(
                    btn_frame,
                    text="🗑️",
                    font=("Segoe UI", 10),
                    bg=theme["COLOR_BG_CONFIG"],
                    fg=theme["COLOR_TEXT_MEDIUM_GRAY"],
                    activebackground=theme["COLOR_BUTTON_RED"],
                    activeforeground="white",
                    relief=tk.FLAT,
                    cursor="hand2",
                    command=lambda fp=filepath, fn=filename: self.delete_history_file(fp, fn),
                    width=3,
                    padx=5,
                    anchor="nw"
                )
                delete_btn.pack(side=tk.RIGHT, padx=(5, 0))

                # 删除按钮悬停效果 - 使用闭包捕获当前按钮实例
                # 关键修复：为每个按钮创建独立的事件处理函数
                def create_delete_handlers(btn_instance, theme_color):
                    """为删除按钮创建独立的事件处理器"""

                    def on_delete_enter(e):
                        btn_instance.config(fg=theme_color["COLOR_BUTTON_RED"])

                    def on_delete_leave(e):
                        btn_instance.config(fg=theme_color["COLOR_TEXT_MEDIUM_GRAY"])

                    return on_delete_enter, on_delete_leave

                # 为当前删除按钮创建独立的事件处理器
                on_delete_enter, on_delete_leave = create_delete_handlers(delete_btn, theme)
                delete_btn.bind("<Enter>", on_delete_enter)
                delete_btn.bind("<Leave>", on_delete_leave)

                self.history_buttons.append(btn_frame)
            except Exception as e:
                print(f"加载历史记录 {filename} 失败: {e}")
                continue

        self.history_content.update_idletasks()
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def delete_history_file(self, filepath, filename):
        """删除历史对话文件"""
        if not messagebox.askyesno("确认删除", f"确定要删除历史对话文件吗？\n\n{filename}"):
            return
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                messagebox.showinfo("成功", "历史对话文件已删除")
                # 刷新历史记录列表
                self.refresh_history()
            else:
                messagebox.showwarning("警告", "文件不存在")
        except Exception as e:
            messagebox.showerror("错误", f"删除文件失败: {str(e)}")
    
    def load_history_from_file(self, filepath):
        """从文件加载对话历史"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            imported_history = self.history_manager.parse_chat_history(content)

            if not imported_history:
                messagebox.showwarning("警告", "未能从文件中解析出对话内容")
                return

            # 询问用户是追加还是替换
            if self.conversation_history:
                choice = messagebox.askyesnocancel(
                    "加载选项",
                    "当前已有对话历史。\n\n点击'是'：追加到现有对话\n点击'否'：替换现有对话\n点击'取消'：取消加载"
                )
                if choice is None:
                    return
                elif choice:
                    self.conversation_history.extend(imported_history)
                else:
                    self.conversation_history = imported_history
                    for frame in self.conversation_pair_frames.values():
                        frame.destroy()
                    self.conversation_pair_frames.clear()
                    self.conversation_pairs.clear()
                    self.current_pair_index = -1
                    for widget in self.chat_content_frame.winfo_children():
                        widget.destroy()
            else:
                self.conversation_history = imported_history

            # 显示导入提示
            ui.create_label(self.chat_content_frame,
                          text=f"📥 已加载 {len(imported_history)} 条对话记录",
                          font=self.text_font, bg=config.COLOR_BG_CHAT,
                          fg=config.COLOR_STATUS_BLUE, padx=10, pady=5).pack(
                          fill=tk.X, padx=10, pady=5)

            # 显示导入的对话内容
            current_pair_idx = len(self.conversation_pairs)
            base_msg_index = len(self.conversation_history) - len(imported_history)

            i = 0
            while i < len(imported_history):
                msg = imported_history[i]

                if msg["role"] == "user":
                    user_msg_index = base_msg_index + i

                    pair = chat.ConversationPair(
                        self.chat_content_frame,
                        current_pair_idx,
                        user_msg_index,
                        self._on_checkbox_toggle,
                        self.text_font,
                        self.chat_canvas,
                        delete_callback=self._delete_conversation_pair
                    )

                    pair.display_user_message(msg["content"], self.chat_canvas)

                    ai_msg_index = None
                    if i + 1 < len(imported_history) and imported_history[i + 1]["role"] == "assistant":
                        i += 1
                        ai_msg = imported_history[i]
                        ai_msg_index = base_msg_index + i

                        pair.text_widget.configure(state=tk.NORMAL)
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        pair.text_widget.insert(tk.END, f"\n🤖 DeepSeek AI ({timestamp})\n", "ai_tag")
                        if ai_msg.get("reasoning_content"):
                            pair.text_widget.insert(tk.END, "🧠 思考过程:\n", "thinking_tag")
                            md.render_markdown(pair.text_widget, ai_msg["reasoning_content"],
                                             "thinking_content")
                            pair.text_widget.insert(tk.END, "\n\n💡 最终回答:\n", "ai_tag")
                        md.render_markdown(pair.text_widget, ai_msg["content"], "ai_message")
                        pair.text_widget.insert(tk.END, f"\n{'─' * config.SEPARATOR_LENGTH}\n",
                                              "separator")
                        chat.update_text_height(pair.text_widget)
                        # 确保滚动到底部
                        pair.text_widget.see(tk.END)
                        pair.text_widget.configure(state=tk.DISABLED)

                    self.conversation_pairs[current_pair_idx] = pair
                    self.conversation_pair_frames[current_pair_idx] = pair.pair_frame
                    pair.ai_msg_index = ai_msg_index
                    current_pair_idx += 1

                i += 1

            chat.update_scroll_region(self.chat_canvas, self.chat_content_frame)
            messagebox.showinfo("成功", f"成功加载 {len(imported_history)} 条对话记录！")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")

    def export_chat(self):
        """导出对话"""
        if not self.conversation_history:
            messagebox.showwarning("警告", "没有对话内容可导出")
            return

        def generate_title_callback(message_indices):
            return self._generate_chat_title(message_indices)

        file_path, error = self.history_manager.export_chat(
            self.conversation_history,
            {idx: pair.get_pair_info() for idx, pair in self.conversation_pairs.items()},
            self.model_var.get(),
            generate_title_callback
        )

        if error:
            messagebox.showerror("错误", error)
        elif file_path:
            messagebox.showinfo("成功", f"对话已导出到:\n{file_path}")
            self.refresh_history()
            self.update_status("已连接" if self.api_client else "未连接",
                             config.COLOR_STATUS_GREEN if self.api_client else config.COLOR_STATUS_RED)

    def _on_window_configure(self, event):
        """窗口大小变化时的回调"""
        # 只响应主窗口的大小变化，忽略子widget的变化
        if event.widget != self.root:
            return
        
        current_width = self.root.winfo_width()
        
        # 只有当宽度真正改变时才更新（避免频繁更新）
        if current_width != self._last_window_width:
            self._last_window_width = current_width
            # 延迟更新，避免在调整大小过程中频繁更新（减少延迟时间以提高响应性）
            self.root.after(50, self._update_all_pair_heights)
    
    def _update_all_pair_heights(self):
        """更新所有对话对的高度"""
        for pair in self.conversation_pairs.values():
            if pair and hasattr(pair, 'text_widget'):
                chat.update_text_height(pair.text_widget)
        # 更新滚动区域
        if hasattr(self, 'chat_canvas') and hasattr(self, 'chat_content_frame'):
            chat.update_scroll_region(self.chat_canvas, self.chat_content_frame)

    def _generate_chat_title(self, message_indices=None):
        """使用AI生成对话标题"""
        if not self.api_client:
            return None

        if not self.conversation_history:
            return None

        try:
            summary_messages = [{
                "role": "system",
                "content": f"请根据以下对话内容，生成一个简洁的标题（不超过{config.TITLE_MAX_LENGTH}个字）。标题应该概括对话的主要主题或内容。只返回标题，不要其他内容，不要加引号。"
            }]

            content = self.history_manager.generate_title_content(
                self.conversation_history, message_indices
            )
            if not content:
                return None

            summary_messages.append({"role": "user", "content": content})

            use_chat_model = self._is_reasoner_model()
            response = self.api_client.generate_title(
                summary_messages, self.model_var.get(), use_chat_model
            )

            title = self.history_manager.parse_title_from_response(response)
            if title:
                print(f"成功生成标题: {title}")
            return title
        except Exception as e:
            print(f"生成标题失败: {e}")
            return None


def set_dpi_aware():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

# 在 main() 函数中调用
def main():
    set_dpi_aware()  # 添加这一行
    root = tk.Tk()
    app = ModernDeepSeekClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()

