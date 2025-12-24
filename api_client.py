"""API客户端模块"""

from openai import OpenAI


class DeepSeekAPIClient:
    """DeepSeek API客户端封装"""
    
    def __init__(self, api_key, base_url):
        """初始化，但此时不创建客户端，因为base_url可能变化"""
        self.api_key = api_key
        self.default_base_url = base_url
        # 先创建一个默认客户端，后续可根据需要创建新的
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def build_params(self, model, messages, max_tokens, temperature, stream, 
                    is_reasoner_model, thinking_enabled):
        """构建API调用参数"""
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        # 思考模式参数处理
        # 如果是 deepseek-chat 模型且启用了思考模式，添加 thinking 参数
        if not is_reasoner_model and thinking_enabled:
            params["extra_body"] = {"thinking": {"type": "enabled"}}
        # deepseek-reasoner 模型默认启用思考模式，不需要额外参数
        
        return params

    def _get_client(self, base_url=None):
        """获取指定base_url的客户端实例"""
        if base_url and base_url != getattr(self.client, '_base_url', None):
            # 如果base_url变化，创建新的客户端实例
            return OpenAI(api_key=self.api_key, base_url=base_url)
        return self.client
    
    def create_completion(self, base_url=None, **params):
        """创建对话完成（非流式）"""
        client = self._get_client(base_url)
        return client.chat.completions.create(**params)
    
    def create_completion_stream(self, base_url=None, **params):
        """创建对话完成（流式）"""
        client = self._get_client(base_url)
        return client.chat.completions.create(**params)
    
    def test_connection(self, model, base_url=None, max_tokens=10, temperature=0.1):
        """测试API连接"""
        client = self._get_client(base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "你好！请回复'连接成功'"}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def generate_title(self, messages, model, use_chat_model=False):
        """生成对话标题"""
        # 如果使用reasoner模型，临时切换到chat模型生成标题
        if use_chat_model:
            model = "deepseek-chat"
        
        api_params = {
            "model": model,
            "messages": messages,
            "max_tokens": 50,
            "temperature": 0.7,
            "stream": False
        }
        
        response = self.client.chat.completions.create(**api_params)
        return response

