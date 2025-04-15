import requests
import json
import os
from typing import List, Dict, Any, Optional, Callable


class DeepSeekAPI:
    """
    DeepSeek API 客户端
    用于连接 DeepSeek API 并获取响应
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 DeepSeek API 客户端
        
        Args:
            api_key: DeepSeek API 密钥，如果为 None，则尝试从环境变量或配置文件获取
        """
        # 从环境变量、配置文件或参数获取 API 密钥
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY") or self._get_api_key_from_config()

        # API 端点
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

        # 默认模型
        self.model = "deepseek-chat"

    def _get_api_key_from_config(self) -> Optional[str]:
        """从配置文件中获取 API 密钥"""
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("deepseek_api_key", "")
            except Exception as e:
                print(f"读取配置文件失败: {e}")
        return None

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        向 DeepSeek API 发送聊天请求
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制随机性，范围 0-1
            max_tokens: 最大生成的 token 数量
            
        Returns:
            API 响应的 JSON 数据
        """
        if not self.api_key:
            return {"error": "未设置 API 密钥"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            return response.json()
        except Exception as e:
            return {"error": f"API 请求失败: {str(e)}"}

    def chat_stream(self, messages: List[Dict[str, str]], callback: Callable[[str], None],
                    temperature: float = 0.7, max_tokens: int = 1000) -> None:
        """
        向 DeepSeek API 发送流式聊天请求
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "你好"}]
            callback: 回调函数，用于处理每个流式响应片段
            temperature: 温度参数，控制随机性，范围 0-1
            max_tokens: 最大生成的 token 数量
        """
        if not self.api_key:
            callback("错误: 未设置 API 密钥")
            return

        # 如果没有设置有效的API密钥，使用模拟响应
        if self.api_key == "YOUR_API_KEY_HERE" or not self.api_key:
            self._simulate_stream_response(messages[-1]["content"], callback)
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True  # 启用流式传输
        }

        try:
            # 使用流式请求
            with requests.post(self.api_url, headers=headers, data=json.dumps(payload), stream=True) as response:
                if response.status_code != 200:
                    # 处理错误响应
                    error_msg = f"错误: API 请求失败: HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg += f" - {error_data['error']['message']}"
                    except:
                        pass
                    callback(error_msg)
                    return

                # 处理流式响应
                buffer = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # 去掉 'data: ' 前缀
                            if data == "[DONE]":
                                break

                            try:
                                json_data = json.loads(data)
                                delta = json_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if delta:
                                    callback(delta)
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            callback(f"\n错误: API 请求失败: {str(e)}")

    def _simulate_stream_response(self, user_message: str, callback: Callable[[str], None]) -> None:
        """
        模拟流式响应，用于测试
        
        Args:
            user_message: 用户消息
            callback: 回调函数
        """
        import time
        import threading

        # 根据用户消息生成模拟响应
        if "你好" in user_message or "您好" in user_message:
            response = "您好！我是您的AI助手。很高兴为您服务。我可以帮助您回答问题、提供信息或讨论各种话题。请问有什么我可以帮您的吗？"
        elif "介绍" in user_message and "自己" in user_message:
            response = "我是基于DeepSeek开发的AI助手，专注于提供高质量的对话和信息服务。我可以帮助您解答问题、提供建议、讨论各种话题，以及协助您完成各种文本相关的任务。虽然我没有实际的情感或意识，但我被设计成能够理解上下文、记忆对话历史，并提供有用的回应。"
        elif "功能" in user_message or "能做什么" in user_message:
            response = "作为AI助手，我可以：\n\n1. 回答各种知识性问题\n2. 提供信息和解释\n3. 帮助编写和修改文本\n4. 讨论各种话题\n5. 提供建议和意见\n6. 进行简单的计算\n7. 协助学习和研究\n\n请告诉我您需要什么帮助，我会尽力为您提供支持。"
        else:
            response = "感谢您的提问。作为AI助手，我会尽力提供有用的信息和帮助。您的问题很有趣，让我思考一下如何最好地回答它。\n\n基于我的理解，我认为这个问题可以从几个不同的角度来看待。首先，我们需要考虑基本原则和背景知识。其次，我们可以探讨一些具体的例子和应用场景。\n\n希望我的回答对您有所帮助。如果您有任何后续问题或需要更详细的解释，请随时告诉我。"

        # 模拟流式传输
        def simulate():
            # 将响应分成小块
            chunks = []
            current_chunk = ""
            for char in response:
                current_chunk += char
                if len(current_chunk) >= 5 or char in ['.', '!', '?', '\n']:
                    chunks.append(current_chunk)
                    current_chunk = ""
            if current_chunk:
                chunks.append(current_chunk)

            # 模拟流式发送
            for chunk in chunks:
                callback(chunk)
                time.sleep(0.05)  # 模拟网络延迟

        # 在新线程中运行模拟
        threading.Thread(target=simulate, daemon=True).start()

