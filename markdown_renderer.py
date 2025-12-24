"""Markdown渲染模块"""

import html.parser
import markdown
import tkinter as tk
import config


def configure_text_tags(text_widget):
    """配置Text widget的样式标签"""
    theme = config.get_theme()
    
    text_widget.tag_config("user_tag", foreground=theme["COLOR_STATUS_BLUE"], 
                          font=("Segoe UI", 10, "bold"))
    text_widget.tag_config("user_message", foreground=theme["COLOR_TEXT_DARK"], 
                          font=config.FONT_TEXT)
    text_widget.tag_config("ai_tag", foreground=theme["COLOR_STATUS_RED"], 
                          font=("Segoe UI", 10, "bold"))
    text_widget.tag_config("ai_message", foreground=theme["COLOR_TEXT_DARKER"], 
                          font=config.FONT_TEXT)
    text_widget.tag_config("thinking_tag", foreground=theme["COLOR_STATUS_PURPLE"], 
                          font=("Segoe UI", 10, "bold"))
    text_widget.tag_config("thinking_content", foreground=theme["COLOR_TEXT_MEDIUM_GRAY"], 
                          font=config.FONT_CODE)
    text_widget.tag_config("separator", foreground=theme["COLOR_TEXT_GRAY"], 
                          font=("Segoe UI", 9))
    text_widget.tag_config("md_h1", foreground=theme["COLOR_TEXT_DARK"], 
                          font=config.FONT_H1)
    text_widget.tag_config("md_h2", foreground=theme["COLOR_TEXT_DARKER"], 
                          font=config.FONT_H2)
    text_widget.tag_config("md_h3", foreground=theme["COLOR_TEXT_DARKER"], 
                          font=config.FONT_H3)
    text_widget.tag_config("md_bold", font=config.FONT_BOLD)
    text_widget.tag_config("md_code", foreground=theme["COLOR_STATUS_RED"], 
                          font=config.FONT_CODE, 
                          background=theme["COLOR_CODE_BG"], relief=tk.SUNKEN, borderwidth=1)
    text_widget.tag_config("md_list", foreground=theme["COLOR_TEXT_DARKER"], 
                          font=config.FONT_TEXT)
    text_widget.tag_config("md_quote", foreground=theme["COLOR_TEXT_MEDIUM_GRAY"], 
                          font=config.FONT_ITALIC,
                          lmargin1=20, lmargin2=20)


def render_markdown(text_widget, text, base_tag=""):
    """渲染Markdown格式文本到Text widget"""
    # 将Markdown转换为HTML
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'nl2br'])
    html_content = md.convert(text)
    
    # 解析HTML并应用到Text widget
    parser = HTMLToTextWidgetParser(text_widget, base_tag)
    parser.feed(html_content)
    parser.close()


class HTMLToTextWidgetParser(html.parser.HTMLParser):
    """将HTML解析并转换为Text widget的格式"""
    def __init__(self, text_widget, base_tag=""):
        super().__init__()
        self.text_widget = text_widget
        self.base_tag = base_tag
        self.tag_stack = []
        self.current_tag = base_tag
    
    def handle_starttag(self, tag, attrs):
        """处理开始标签"""
        self.tag_stack.append(tag)
        
        # 根据标签类型应用样式
        if tag == 'h1':
            self.current_tag = ("md_h1", self.base_tag)
        elif tag == 'h2':
            self.current_tag = ("md_h2", self.base_tag)
        elif tag == 'h3':
            self.current_tag = ("md_h3", self.base_tag)
        elif tag == 'strong' or tag == 'b':
            self.current_tag = ("md_bold", self.base_tag)
        elif tag == 'code':
            self.current_tag = ("md_code", self.base_tag)
        elif tag == 'blockquote':
            self.current_tag = ("md_quote", self.base_tag)
        elif tag == 'ul' or tag == 'ol':
            self.current_tag = ("md_list", self.base_tag)
        elif tag == 'li':
            self.current_tag = ("md_list", self.base_tag)
        elif tag == 'hr':
            self.text_widget.insert(tk.END, "─" * config.SEPARATOR_LENGTH + "\n", 
                                   ("separator", self.base_tag))
        elif tag == 'br':
            self.text_widget.insert(tk.END, "\n", self.base_tag)
        else:
            self.current_tag = self.base_tag
    
    def handle_endtag(self, tag):
        """处理结束标签"""
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        
        if tag in ['h1', 'h2', 'h3', 'p', 'li', 'blockquote']:
            self.text_widget.insert(tk.END, "\n", self.base_tag)
        elif tag in ['ul', 'ol']:
            self.text_widget.insert(tk.END, "\n", self.base_tag)
        
        # 恢复为基本标签
        self.current_tag = self.base_tag
    
    def handle_data(self, data):
        """处理文本数据"""
        if data.strip():
            # 移除HTML实体
            data = html.parser.unescape(data)
            self.text_widget.insert(tk.END, data, self.current_tag)

