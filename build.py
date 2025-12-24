import PyInstaller.__main__
import os
import sys

# 确保在正确的目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 从 config 模块获取图标文件名
try:
    import config
    icon_file = config.ICON_FILE
    print(f"使用图标文件: {icon_file}")
except ImportError:
    icon_file = "icon/deepseek.ico"
    print(f"无法导入 config，使用默认图标: {icon_file}")

# 检查图标文件是否存在
if os.path.exists(icon_file):
    print(f"图标文件存在: {icon_file}")
else:
    print(f"警告: 图标文件不存在: {icon_file}")
    icon_file = None

args = [
    'main.py',
    '--name=DeepSeek-Api',
    '--windowed',  # 不显示控制台窗口
    '--onefile',   # 打包为单个exe文件
]

# 只在图标文件存在时添加图标参数
if icon_file and os.path.exists(icon_file):
    args.append(f'--icon={icon_file}')
    print(f"已添加图标: {icon_file}")
else:
    print("跳过图标设置")

args.extend([
    '--add-data=config.py;.',
    '--add-data=ui_components.py;.',
    '--add-data=chat_display.py;.',
    '--add-data=markdown_renderer.py;.',
    '--add-data=api_client.py;.',
    '--add-data=history_manager.py;.',
    '--hidden-import=tkinter',
    '--hidden-import=openai',
    '--clean',
])

print("打包参数:", args)
PyInstaller.__main__.run(args)