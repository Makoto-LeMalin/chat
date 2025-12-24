"""UI组件工厂函数"""

import tkinter as tk
from tkinter import ttk
import config


def create_label(parent, text="", **kwargs):
    """创建标签"""
    theme = config.get_theme()
    defaults = {
        'font': config.FONT_SMALL,
        'bg': theme.get('COLOR_BG_CONFIG', config.COLOR_BG_CONFIG),
        'fg': theme.get('COLOR_TEXT_GRAY', config.COLOR_TEXT_GRAY)
    }
    defaults.update(kwargs)
    return tk.Label(parent, text=text, **defaults)


def create_button(parent, text, command, **kwargs):
    """创建按钮"""
    defaults = {
        'font': config.FONT_SMALL,
        'fg': config.COLOR_TEXT_WHITE,
        'relief': tk.FLAT,
        'padx': 20,
        'pady': 8
    }
    defaults.update(kwargs)
    btn = tk.Button(parent, text=text, command=command, **defaults)
    return btn


def create_entry(parent, textvariable=None, **kwargs):
    """创建输入框"""
    theme = config.get_theme()
    defaults = {
        'font': config.FONT_SMALL,
        'bg': theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR),
        'fg': theme.get('COLOR_TEXT_WHITE', config.COLOR_TEXT_WHITE),
        'insertbackground': theme.get('COLOR_TEXT_WHITE', config.COLOR_TEXT_WHITE),
        'relief': tk.FLAT
    }
    defaults.update(kwargs)
    return tk.Entry(parent, textvariable=textvariable, **defaults)


def create_text_widget(parent, **kwargs):
    """创建文本输入框"""
    theme = config.get_theme()
    defaults = {
        'wrap': tk.WORD,
        'font': config.FONT_TEXT,
        'bg': theme.get('COLOR_BG_CHAT', config.COLOR_BG_CHAT),
        'fg': theme.get('COLOR_TEXT_DARK', config.COLOR_TEXT_DARK),
        'insertbackground': theme.get('COLOR_TEXT_DARK', config.COLOR_TEXT_DARK),
        'relief': tk.FLAT,
        'padx': 15,
        'pady': 15
    }
    defaults.update(kwargs)
    return tk.Text(parent, **defaults)


def _bind_mousewheel_recursive(widget, canvas):
    """递归地为widget及其所有子widget绑定滚轮事件"""
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"  # 阻止事件继续传播
    
    widget.bind("<MouseWheel>", on_mousewheel)
    
    # 递归绑定所有子widget
    for child in widget.winfo_children():
        _bind_mousewheel_recursive(child, canvas)


def create_scrollable_canvas(parent, bg_color=None, **kwargs):
    """创建可滚动的Canvas组件
    
    返回: (canvas, content_frame, scrollbar)
    """
    theme = config.get_theme()
    if bg_color is None:
        bg_color = theme.get('COLOR_BG_CHAT', config.COLOR_BG_CHAT)
    
    # 创建滚动条
    scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 创建Canvas
    canvas = tk.Canvas(parent, bg=bg_color, highlightthickness=0,
                      yscrollcommand=scrollbar.set, **kwargs)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # 创建内容框架
    content_frame = tk.Frame(canvas, bg=bg_color)
    canvas_window = canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)
    
    # 配置滚动
    scrollbar.config(command=canvas.yview)
    
    # 绑定Canvas大小变化事件
    def configure_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas_width = event.width
        canvas.itemconfig(canvas_window, width=canvas_width)
    
    canvas.bind('<Configure>', configure_scroll_region)
    content_frame.bind('<Configure>', 
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    # 绑定鼠标滚轮事件（递归绑定到所有子widget）
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    
    canvas.bind("<MouseWheel>", on_mousewheel)
    _bind_mousewheel_recursive(content_frame, canvas)
    
    # 当添加新widget时，也需要绑定滚轮事件
    # 通过重写pack方法来实现（但这可能过于复杂）
    # 更好的方法是在创建对话对时手动绑定
    
    return canvas, content_frame, scrollbar


def create_config_frame(parent, title, pack_pady=None, **kwargs):
    """创建配置框架"""
    theme = config.get_theme()
    defaults = {
        'bg': theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR),  # 使用SIDEBAR颜色，与历史记录栏深色部分一致
        'padx': 15,
        'pady': 15
    }
    defaults.update(kwargs)
    
    frame = tk.Frame(parent, **defaults)
    if pack_pady is None:
        pack_pady = 5  # 减小默认间距
    frame.pack(fill=tk.X, padx=10, pady=pack_pady)
    
    # 标题
    create_label(frame, text=title, font=config.FONT_MEDIUM,
                bg=theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR), 
                fg=theme.get('COLOR_TEXT_WHITE', config.COLOR_TEXT_WHITE)).pack(
                anchor=tk.W, pady=(0, 10))
    
    return frame


def create_scale_with_label(parent, label_text, variable, from_val, to_val, 
                            resolution=None, **kwargs):
    """创建带标签的滑动条"""
    theme = config.get_theme()
    # 标签框架
    label_frame = tk.Frame(parent, bg=theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR))
    label_frame.pack(fill=tk.X, pady=5)
    
    create_label(label_frame, text=label_text, 
                bg=theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR),
                fg=theme.get('COLOR_TEXT_GRAY', config.COLOR_TEXT_GRAY)).pack(side=tk.LEFT)
    
    value_label = create_label(label_frame, textvariable=variable,
                             bg=theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR), 
                             fg=theme.get('COLOR_TEXT_WHITE', config.COLOR_TEXT_WHITE))
    value_label.pack(side=tk.RIGHT)
    
    # 滑动条
    defaults = {
        'variable': variable,
        'orient': tk.HORIZONTAL,
        'bg': theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR),
        'fg': theme.get('COLOR_TEXT_WHITE', config.COLOR_TEXT_WHITE),
        'highlightthickness': 0,
        'sliderrelief': tk.FLAT,
        'length': 200
    }
    if resolution:
        defaults['resolution'] = resolution
    defaults.update(kwargs)
    
    scale = tk.Scale(parent, from_=from_val, to=to_val, **defaults)
    scale.pack(fill=tk.X, pady=5)
    
    return scale


def create_checkbutton(parent, text="", variable=None, command=None, **kwargs):
    """创建复选框"""
    theme = config.get_theme()
    # 如果kwargs中指定了bg，使用指定的值，否则使用SIDEBAR颜色
    bg_color = kwargs.get('bg', theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR))
    defaults = {
        'variable': variable,
        'bg': bg_color,
        'fg': theme.get('COLOR_TEXT_WHITE', config.COLOR_TEXT_WHITE),
        'selectcolor': theme.get('COLOR_BG_CONFIG', config.COLOR_BG_CONFIG),
        'activebackground': bg_color,
        'font': config.FONT_SMALL
    }
    if text:
        defaults['text'] = text
    if command:
        defaults['command'] = command
    defaults.update(kwargs)
    return tk.Checkbutton(parent, **defaults)


def create_combobox(parent, textvariable, values, command=None, **kwargs):
    """创建下拉框"""
    defaults = {
        'textvariable': textvariable,
        'values': values,
        'font': config.FONT_SMALL,
        'state': "readonly"
    }
    defaults.update(kwargs)
    
    combo = ttk.Combobox(parent, **defaults)
    if command:
        combo.bind("<<ComboboxSelected>>", command)
    return combo


def create_frame_with_checkbox(parent, label_text, variable, command=None, **kwargs):
    """创建带复选框的框架"""
    theme = config.get_theme()
    # 如果kwargs中指定了bg，使用指定的值，否则使用SIDEBAR颜色
    bg_color = kwargs.get('bg', theme.get('COLOR_BG_SIDEBAR', config.COLOR_BG_SIDEBAR))
    defaults = {
        'bg': bg_color
    }
    defaults.update(kwargs)
    
    frame = tk.Frame(parent, **defaults)
    frame.pack(fill=tk.X, pady=5)
    
    create_label(frame, text=label_text, 
                bg=bg_color,
                fg=theme.get('COLOR_TEXT_GRAY', config.COLOR_TEXT_GRAY)).pack(side=tk.LEFT)
    
    checkbox = create_checkbutton(frame, text="", variable=variable, command=command,
                                 bg=bg_color)
    checkbox.pack(side=tk.RIGHT)
    
    return frame, checkbox

