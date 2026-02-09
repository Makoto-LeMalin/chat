"""历史记录管理模块"""

import os
import re
from datetime import datetime
from tkinter import filedialog

import config


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, chat_history_dir=config.CHAT_HISTORY_DIR):
        """初始化历史记录管理器"""
        self.chat_history_dir = chat_history_dir
        if not os.path.exists(self.chat_history_dir):
            os.makedirs(self.chat_history_dir)
    
    def parse_chat_history(self, content):
        """解析对话历史文件"""
        history = []
        lines = content.split('\n')
        
        current_role = None
        current_content = []
        current_reasoning = None
        in_round = False
        in_thinking = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过文件头（标题、导出时间、模型等）
            if line.startswith('# DeepSeek AI 对话记录') or \
               line.startswith('标题:') or \
               line.startswith('导出时间:') or \
               line.startswith('模型:') or \
               (line.startswith('# ') and i < 3) or \
               line == '':
                i += 1
                continue
            
            # 检测对话轮次
            round_match = re.match(r'^##\s+第(\d+)轮\s+-\s+(.+)$', line)
            if round_match:
                # 保存上一轮的内容
                if current_role and current_content:
                    msg = {
                        "role": current_role,
                        "content": '\n'.join(current_content).strip()
                    }
                    if current_reasoning:
                        msg["reasoning_content"] = current_reasoning.strip()
                    history.append(msg)
                
                # 开始新的一轮
                role_name = round_match.group(2).strip()
                if role_name == "我":
                    current_role = "user"
                elif "DeepSeek" in role_name or "AI" in role_name:
                    current_role = "assistant"
                else:
                    current_role = None
                
                current_content = []
                current_reasoning = None
                in_round = True
                in_thinking = False
                i += 1
                continue
            
            # 检测思考过程标题
            if line.startswith('### 🧠 思考过程') or line.startswith('### 思考过程'):
                in_thinking = True
                current_reasoning = []
                i += 1
                continue
            
            # 检测最终回答标题
            if line.startswith('### 💡 最终回答') or line.startswith('### 最终回答'):
                in_thinking = False
                if current_reasoning:
                    current_reasoning = '\n'.join(current_reasoning)
                i += 1
                continue
            
            # 跳过分隔线
            if line == '---' or line == '***':
                i += 1
                continue
            
            # 收集内容
            if in_round and current_role:
                if in_thinking and current_reasoning is not None:
                    # 收集思考过程内容
                    current_reasoning.append(lines[i])
                else:
                    # 收集正常内容
                    current_content.append(lines[i])
            
            i += 1
        
        # 保存最后一轮的内容
        if current_role and current_content:
            msg = {
                "role": current_role,
                "content": '\n'.join(current_content).strip()
            }
            if current_reasoning:
                if isinstance(current_reasoning, list):
                    current_reasoning = '\n'.join(current_reasoning)
                msg["reasoning_content"] = current_reasoning.strip()
            history.append(msg)
        
        return history
    
    def get_history_files(self):
        """获取历史记录文件列表"""
        if not os.path.exists(self.chat_history_dir):
            return []
        
        history_files = []
        for filename in os.listdir(self.chat_history_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(self.chat_history_dir, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    history_files.append((mtime, filepath, filename))
                except:
                    continue
        
        # 按时间从新到旧排序
        history_files.sort(reverse=True)
        return history_files
    
    def extract_title_from_file(self, filepath):
        """从文件中提取标题"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_lines = [f.readline().strip() for _ in range(10)]
            
            # 检查是否有标题（优先检查"标题:"格式，然后检查"# 标题"格式）
            title = None
            for line in first_lines:
                if line.startswith('标题:'):
                    title = line.replace('标题:', '').strip()
                    break
            
            # 如果没有找到"标题:"格式，检查"# 标题"格式
            if not title:
                for line in first_lines:
                    if line.startswith('# ') and not line.startswith('# DeepSeek AI 对话记录'):
                        title = line.replace('# ', '').strip()
                        break
            
            # 如果没有标题，使用文件名（去掉扩展名和时间戳）
            if not title:
                name_without_ext = os.path.basename(filepath).replace('.md', '')
                # 格式通常是 deepseek_chat_YYYYMMDD_HHMMSS
                if 'deepseek_chat_' in name_without_ext:
                    date_str = name_without_ext.replace('deepseek_chat_', '')
                    try:
                        dt = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                        title = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        title = name_without_ext
                else:
                    title = name_without_ext
            
            return title
        except Exception as e:
            print(f"提取标题失败: {e}")
            return None
    
    def export_chat(self, conversation_history, conversation_pairs, model, 
                   generate_title_callback=None):
        """导出对话到文件（使用 Tk filedialog）"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="导出对话",
            initialdir=self.chat_history_dir,
            initialfile=f"deepseek_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        if not file_path:
            return None, None
        return self.export_chat_to_path(file_path, conversation_history, conversation_pairs, model, generate_title_callback)

    def export_chat_to_path(self, file_path, conversation_history, conversation_pairs, model,
                            generate_title_callback=None):
        """导出对话到指定路径（不弹窗，供 Qt 等非 Tk 前端调用）"""
        if not conversation_history:
            return None, "没有对话内容可导出"
        if not file_path:
            return None, None
        try:
            # 检查是否有选中的对话对
            selected_pairs = [idx for idx, pair in conversation_pairs.items() 
                            if pair.get('selected', False)]
            
            # 确定要导出的消息索引
            messages_to_export = []
            if selected_pairs:
                # 只导出选中的对话对
                for pair_idx in sorted(selected_pairs):
                    pair = conversation_pairs[pair_idx]
                    user_idx = pair.get('user_msg_index')
                    ai_idx = pair.get('ai_msg_index')
                    if user_idx is not None and user_idx < len(conversation_history):
                        messages_to_export.append(user_idx)
                    if ai_idx is not None and ai_idx < len(conversation_history):
                        messages_to_export.append(ai_idx)
            else:
                # 导出全部对话
                messages_to_export = list(range(len(conversation_history)))
            
            # 对消息索引进行排序，确保按照conversation_history的顺序
            messages_to_export = sorted(set(messages_to_export))
            
            # 生成标题（使用AI总结，只基于要导出的对话）
            title = None
            if generate_title_callback:
                title = generate_title_callback(messages_to_export)
            
            if not title:
                title = "DeepSeek AI 对话记录"
            
            if not messages_to_export:
                return None, "没有可导出的对话内容"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入标题
                f.write(f"# {title}\n\n")
                f.write(f"标题: {title}\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"模型: {model}\n")
                if selected_pairs:
                    f.write(f"导出模式: 选中对话（共{len(selected_pairs)}对）\n")
                else:
                    f.write(f"导出模式: 全部对话\n")
                f.write("\n")
                
                # 导出选中的消息（按顺序）
                export_round = 1
                for msg_idx in messages_to_export:
                    if msg_idx >= len(conversation_history):
                        continue
                    msg = conversation_history[msg_idx]
                    role = "我" if msg["role"] == "user" else "DeepSeek AI"
                    f.write(f"## 第{export_round}轮 - {role}\n\n")
                    
                    # 如果有思考过程，先导出思考过程
                    if msg.get("reasoning_content"):
                        f.write("### 🧠 思考过程\n\n")
                        f.write(f"{msg['reasoning_content']}\n\n")
                        f.write("### 💡 最终回答\n\n")
                    
                    f.write(f"{msg['content']}\n\n")
                    f.write("---\n\n")
                    export_round += 1
            
            return file_path, None
            
        except Exception as e:
            return None, f"导出失败: {str(e)}"
    
    def generate_title_content(self, conversation_history, message_indices=None, 
                             max_length=config.MAX_TITLE_GEN_LENGTH):
        """生成用于标题生成的对话内容"""
        # 确定要使用的消息
        if message_indices is None:
            messages_to_use = conversation_history
        else:
            messages_to_use = [conversation_history[idx] 
                             for idx in message_indices 
                             if idx < len(conversation_history)]
        
        if not messages_to_use:
            return None
        
        # 收集对话内容用于生成标题
        content_parts = []
        total_length = 0
        round_num = 1
        i = 0
        
        while i < len(messages_to_use):
            msg = messages_to_use[i]
            
            if msg["role"] == "user":
                # 用户消息：包含完整内容
                user_content = msg['content']
                # 如果内容太长，适当截取但保留更多信息
                if len(user_content) > config.MAX_CONTENT_PREVIEW * 2:
                    user_content = user_content[:config.MAX_CONTENT_PREVIEW * 2] + "..."
                
                # 检查下一条消息是否是AI回复（形成对话对）
                if i + 1 < len(messages_to_use) and messages_to_use[i + 1]["role"] == "assistant":
                    # 这是一对对话，一起处理
                    ai_msg = messages_to_use[i + 1]
                    
                    # 构建完整的对话对内容
                    pair_content_parts = [f"第{round_num}轮对话\n\n用户:\n{user_content}"]
                    
                    # AI消息：包含思考过程和完整回答
                    ai_content_parts = []
                    
                    # 包含思考过程（如果存在）
                    if ai_msg.get("reasoning_content"):
                        reasoning = ai_msg['reasoning_content']
                        # 思考过程如果太长，适当截取但保留更多
                        if len(reasoning) > config.MAX_CONTENT_PREVIEW * 2:
                            reasoning = reasoning[:config.MAX_CONTENT_PREVIEW * 2] + "..."
                        ai_content_parts.append(f"思考过程:\n{reasoning}")
                    
                    # 包含主要回答内容
                    answer_content = ai_msg['content']
                    if len(answer_content) > config.MAX_CONTENT_PREVIEW * 2:
                        answer_content = answer_content[:config.MAX_CONTENT_PREVIEW * 2] + "..."
                    ai_content_parts.append(f"回答:\n{answer_content}")
                    
                    pair_content_parts.append(f"AI:\n" + "\n\n".join(ai_content_parts))
                    content = "\n\n".join(pair_content_parts)
                    
                    round_num += 1
                    i += 2  # 跳过AI消息，因为已经处理了
                else:
                    # 只有用户消息，没有对应的AI回复
                    content = f"第{round_num}轮 - 用户:\n{user_content}"
                    round_num += 1
                    i += 1
            else:
                # 单独的AI消息（不应该出现，但为了健壮性处理）
                ai_content_parts = []
                
                # 包含思考过程（如果存在）
                if msg.get("reasoning_content"):
                    reasoning = msg['reasoning_content']
                    if len(reasoning) > config.MAX_CONTENT_PREVIEW * 2:
                        reasoning = reasoning[:config.MAX_CONTENT_PREVIEW * 2] + "..."
                    ai_content_parts.append(f"思考过程:\n{reasoning}")
                
                # 包含主要回答内容
                answer_content = msg['content']
                if len(answer_content) > config.MAX_CONTENT_PREVIEW * 2:
                    answer_content = answer_content[:config.MAX_CONTENT_PREVIEW * 2] + "..."
                ai_content_parts.append(f"回答:\n{answer_content}")
                
                content = f"第{round_num}轮 - AI:\n" + "\n\n".join(ai_content_parts)
                round_num += 1
                i += 1
            
            # 检查是否超过长度限制
            content_length = len(content)
            if total_length + content_length > max_length:
                # 如果这是第一条消息，至少包含部分内容
                if not content_parts:
                    # 截取部分内容
                    remaining = max_length - total_length - 50
                    if remaining > 100:
                        content = content[:remaining] + "\n...（对话内容较长，已截取部分）"
                        content_parts.append(content)
                else:
                    content_parts.append("\n...（对话内容较长，已截取部分）")
                break
            
            content_parts.append(content)
            total_length += content_length
        
        if not content_parts:
            return None
        
        # 使用更清晰的分隔符
        return "\n\n---\n\n".join(content_parts)
    
    def parse_title_from_response(self, response):
        """从API响应中解析标题"""
        if not response or not response.choices:
            return None
        
        choice = response.choices[0]
        if not choice.message:
            return None
        
        message = choice.message
        
        # 保存原始返回内容
        raw_title = message.content
        
        # 如果content为空，尝试使用reasoning_content
        if not raw_title or raw_title.strip() == '':
            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                raw_title = message.reasoning_content
            else:
                return None
        
        title = raw_title.strip()
        
        # 清理标题（移除可能的引号、换行等）
        title = title.strip('"').strip("'").strip()
        title = title.replace('\n', ' ').replace('\r', ' ')
        # 移除多余空格
        title = ' '.join(title.split())
        
        if not title or title.lower() in ['deepseek ai 对话记录', '对话记录', 'chat history']:
            return None
        
        return title

