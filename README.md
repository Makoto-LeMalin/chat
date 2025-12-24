# DeepSeek AI Assistant

一个基于 Python 和 Tkinter 的现代化 DeepSeek API 客户端桌面应用程序，支持流式对话、历史记录管理和 Markdown 渲染。

## 功能特点

### 🤖 核心功能
- **多模型支持**：支持 deepseek-chat 和 deepseek-reasoner 模型
- **流式响应**：实时查看 AI 思考过程和回答生成
- **思考模式**：显示模型的推理过程（仅限 deepseek-chat 模型）
- **对话管理**：支持导出、导入和删除对话历史

### 🎨 用户界面
- **现代化设计**：采用侧边栏布局，界面简洁美观
- **主题切换**：支持浅色/深色主题（夜间模式）
- **响应式布局**：侧边栏可折叠，适应不同屏幕尺寸
- **Markdown 渲染**：完美支持 Markdown 格式的显示和渲染

### 💾 数据管理
- **历史记录**：自动保存对话历史到本地文件
- **配置文件**：保存 API 密钥和设置到本地
- **批量操作**：支持批量导出选中的对话对
- **文件导入**：支持从 Markdown 文件导入历史对话

### ⚙️ 高级功能
- **参数调节**：可调节生成温度、最大 token 数等参数
- **连接测试**：一键测试 API 连接状态
- **自动标题生成**：使用 AI 为对话生成标题
- **多线程处理**：后台线程处理 API 请求，界面不卡顿

## 安装和运行

### 环境要求
- Python 3.8 或更高版本
- Windows 操作系统（也可在其他平台运行，但需要调整打包配置）

### 依赖安装
运行以下命令安装所需依赖：

```bash
pip install -r requirements.txt
```

`requirements.txt` 内容：
```text
openai>=1.0.0
markdown>=3.5
PyInstaller>=6.0.0  # 仅用于打包
```

### 运行方式

#### 方式1：直接运行源代码
```bash
python main.py
```

#### 方式2：打包为可执行文件
```bash
python build.py
```
打包后的程序将生成在 `dist/` 目录中。

## 配置文件

首次运行时，程序会自动创建配置文件 `config/deepseek_config.json`，包含以下配置项：

```json
{
  "api_key": "your_api_key_here",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "max_tokens": 2000,
  "temperature": 0.7,
  "stream": true,
  "thinking_enabled": false,
  "dark_mode": false,
  "sidebar_collapsed": false,
  "history_sidebar_collapsed": false
}
```

## 使用指南

### 1. 获取 API 密钥
1. 访问 DeepSeek 平台
2. 注册账号并登录
3. 在 API 密钥管理页面创建新的 API 密钥
4. 将密钥复制到应用程序的 API 密钥输入框

### 2. 基本使用流程
- **连接 API**：输入 API 密钥和端点，点击"连接"按钮
- **开始对话**：在底部输入框输入问题，按 `Ctrl+Enter` 或点击发送按钮
- **管理对话**：使用右侧历史记录栏查看、加载或删除历史对话
- **导出对话**：选择特定对话对或全部对话，导出为 Markdown 文件

### 3. 界面说明
- **左侧边栏**：API 配置和生成参数设置
- **中间区域**：对话显示区域，支持 Markdown 渲染
- **右侧边栏**：历史记录管理
- **底部区域**：消息输入和功能按钮

### 4. 键盘快捷键
- `Ctrl+Enter`：发送消息
- `Shift+Enter`：在输入框中换行
- 鼠标滚轮：上下滚动对话内容

## 项目结构

```
DeepSeek-AI-Assistant/
├── main.py              # 主程序入口
├── config.py            # 配置和常量定义
├── ui_components.py     # UI 组件工厂函数
├── chat_display.py      # 对话显示模块
├── markdown_renderer.py # Markdown 渲染模块
├── api_client.py        # API 客户端封装
├── history_manager.py   # 历史记录管理模块
├── build.py            # 打包脚本
├── requirements.txt    # 依赖列表
├── config/             # 配置文件目录
│   └── deepseek_config.json
├── chat_history/       # 对话历史目录
│   └── *.md
├── icon/              # 图标目录（可选）
│   └── deepseek.ico
└── dist/              # 打包输出目录（打包后生成）
```

## 核心模块说明

- **main.py**：主程序文件，负责初始化应用程序、创建用户界面和处理主要业务逻辑。
- **config.py**：定义应用程序的常量、颜色主题和配置管理函数。
- **ui_components.py**：包含创建各种 UI 组件的工厂函数，使界面代码更加模块化。
- **chat_display.py**：处理对话的显示逻辑，包括消息排版、滚动管理和交互功能。
- **markdown_renderer.py**：将 Markdown 文本渲染为 Tkinter Text 控件中的格式化文本。
- **api_client.py**：封装 DeepSeek API 的调用，处理参数构建、流式响应和错误处理。
- **history_manager.py**：管理对话历史的导入、导出、解析和显示。

## 常见问题

**Q1: 如何获取 DeepSeek API 密钥？**
**A:** 访问 DeepSeek 平台，注册账号后在 API 管理页面创建。

**Q2: 支持哪些模型？**
**A:** 目前支持 deepseek-chat 和 deepseek-reasoner 模型。

**Q3: 思考模式是什么？**
**A:** 思考模式会显示模型的推理过程（中间思考步骤），但仅 deepseek-chat 模型需要手动启用，deepseek-reasoner 模型默认启用。

**Q4: 对话历史保存在哪里？**
**A:** 对话历史保存在 chat_history/ 目录下的 Markdown 文件中。

**Q5: 如何导出对话？**
**A:** 可以选中特定对话对的复选框，然后点击"导出对话"按钮。如果不选择，则导出全部对话。

**Q6: 程序支持中文吗？**
**A:** 是的，界面完全支持中文，也支持中文对话。

## 故障排除

### 连接问题
- 检查 API 密钥是否正确
- 确认网络连接正常
- 验证 API 端点地址是否正确

### 显示问题
- 如果 Markdown 渲染异常，尝试重新发送消息
- 调整窗口大小以重新计算文本布局

### 打包问题
- 确保 PyInstaller 已正确安装
- 检查图标文件路径是否正确
- 打包时关闭所有相关 Python 进程

## 开发说明

### 自定义主题
在 config.py 中修改 `LIGHT_THEME` 和 `DARK_THEME` 字典来自定义颜色主题。

### 添加新功能
1. 在相应模块中添加新功能代码
2. 在 ui_components.py 中添加对应的 UI 组件
3. 在 main.py 中集成新功能

### 代码规范
- 使用 PEP 8 代码风格
- 添加适当的注释和文档字符串
- 保持模块间的低耦合

## 版本历史

### v1.0.0
- 初始版本发布
- 支持基本的对话功能
- 支持历史记录管理
- 支持 Markdown 渲染
- 支持浅色/深色主题

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送电子邮件到开发者邮箱

## 注意

本项目是第三方客户端，与 DeepSeek 官方无直接关联。API 使用请遵守 DeepSeek 平台的相关条款和限制。