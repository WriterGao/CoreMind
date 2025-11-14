"""
LLM服务 - 支持多种LLM提供商
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
from app.models.llm_config import LLMConfig, LLMProvider
from app.utils.crypto import decrypt_text
from app.core.logging import setup_logging

logger = setup_logging()


class LLMService:
    """LLM服务类"""
    
    def __init__(self, llm_config: LLMConfig):
        """
        初始化LLM服务
        
        Args:
            llm_config: LLM配置对象
        """
        self.config = llm_config
        self.provider = llm_config.provider
        self.model_name = llm_config.model_name
        self.api_key = decrypt_text(llm_config.api_key) if llm_config.api_key else ""
        self.api_base = llm_config.api_base or ""
        self.temperature = llm_config.temperature
        self.max_tokens = llm_config.max_tokens
        self.extra_config = llm_config.config or {}

        if self.provider not in {LLMProvider.OLLAMA} and not self.api_key:
            raise ValueError("当前LLM配置未设置API密钥，请在LLM配置页面补充后重试。")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        发送聊天消息
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
            
        Returns:
            AI回复内容
        """
        # 构建消息列表
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)
        
        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._call_openai(chat_messages)
            elif self.provider == LLMProvider.DEEPSEEK:
                return await self._call_deepseek(chat_messages)
            elif self.provider == LLMProvider.ALIBABA_QWEN:
                return await self._call_alibaba_qwen(chat_messages)
            elif self.provider == LLMProvider.ZHIPU_AI:
                return await self._call_zhipu_ai(chat_messages)
            elif self.provider == LLMProvider.MOONSHOT:
                return await self._call_moonshot(chat_messages)
            elif self.provider == LLMProvider.OLLAMA:
                return await self._call_ollama(chat_messages)
            elif self.provider == LLMProvider.CUSTOM:
                return await self._call_custom(chat_messages)
            else:
                raise ValueError(f"不支持的LLM提供商: {self.provider}")
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """调用OpenAI API"""
        url = f"{self.api_base.rstrip('/')}/chat/completions" if self.api_base else "https://api.openai.com/v1/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError(
                        f"API密钥认证失败（401 Unauthorized）。"
                        f"请检查：\n"
                        f"1. API密钥是否正确（格式：sk-xxx）\n"
                        f"2. API密钥是否已激活\n"
                        f"3. API密钥是否有访问此模型的权限"
                    )
                elif e.response.status_code == 429:
                    raise ValueError(
                        f"请求频率过高（429 Too Many Requests）。"
                        f"请稍后重试或检查：\n"
                        f"1. API调用频率限制\n"
                        f"2. 账户余额是否充足"
                    )
                else:
                    error_detail = ""
                    try:
                        error_body = e.response.json()
                        error_detail = error_body.get("error", {}).get("message", str(error_body))
                    except:
                        error_detail = e.response.text[:200]
                    raise ValueError(f"API调用失败（{e.response.status_code}）: {error_detail}")
            except httpx.RequestError as e:
                raise ValueError(f"网络请求失败: {str(e)}。请检查网络连接。")
    
    async def _call_deepseek(self, messages: List[Dict[str, str]]) -> str:
        """调用DeepSeek API"""
        url = f"{self.api_base.rstrip('/')}/chat/completions" if self.api_base else "https://api.deepseek.com/v1/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError(
                        f"API密钥认证失败（401 Unauthorized）。"
                        f"请检查API密钥是否正确。"
                    )
                else:
                    error_detail = ""
                    try:
                        error_body = e.response.json()
                        error_detail = error_body.get("message", error_body.get("error", ""))
                    except:
                        error_detail = e.response.text[:200]
                    raise ValueError(f"API调用失败（{e.response.status_code}）: {error_detail}")
            except httpx.RequestError as e:
                raise ValueError(f"网络请求失败: {str(e)}。请检查网络连接。")
    
    async def _call_alibaba_qwen(self, messages: List[Dict[str, str]]) -> str:
        """调用阿里云通义千问API"""
        # 判断使用兼容模式还是旧版API
        if self.api_base:
            # 用户自定义URL，判断是否为兼容模式
            if "compatible-mode" in self.api_base:
                # 兼容模式：类似OpenAI格式
                url = f"{self.api_base.rstrip('/')}/chat/completions"
                request_data = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            else:
                # 旧版API格式
                url = self.api_base.rstrip('/')
                if not url.endswith("/generation"):
                    url = f"{url}/api/v1/services/aigc/text-generation/generation"
                
                # 转换消息格式
                qwen_messages = []
                for msg in messages:
                    if msg["role"] in ["system", "user", "assistant"]:
                        qwen_messages.append({"role": msg["role"], "content": msg["content"]})
                
                request_data = {
                    "model": self.model_name,
                    "input": {
                        "messages": qwen_messages
                    },
                    "parameters": {
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                }
        else:
            # 默认使用兼容模式
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            request_data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_data
                )
                response.raise_for_status()
                result = response.json()
                
                # 兼容模式返回格式
                if "choices" in result:
                    return result["choices"][0]["message"]["content"]
                # 旧版API返回格式
                elif "output" in result and "choices" in result["output"]:
                    return result["output"]["choices"][0]["message"]["content"]
                else:
                    raise ValueError(f"未知的响应格式: {result}")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError(
                        f"API密钥认证失败（401 Unauthorized）。"
                        f"请检查：\n"
                        f"1. API密钥是否正确（格式：sk-xxx）\n"
                        f"2. API密钥是否已激活\n"
                        f"3. API密钥是否有足够的权限"
                    )
                elif e.response.status_code == 403:
                    raise ValueError(
                        f"API访问被拒绝（403 Forbidden）。"
                        f"请检查：\n"
                        f"1. API密钥是否有访问此模型的权限\n"
                        f"2. 账户余额是否充足"
                    )
                else:
                    error_detail = ""
                    try:
                        error_body = e.response.json()
                        error_detail = error_body.get("message", error_body.get("error", ""))
                    except:
                        error_detail = e.response.text[:200]
                    
                    raise ValueError(
                        f"API调用失败（{e.response.status_code}）: {error_detail}"
                    )
            except httpx.RequestError as e:
                raise ValueError(
                    f"网络请求失败: {str(e)}。"
                    f"请检查：\n"
                    f"1. 网络连接是否正常\n"
                    f"2. API服务地址是否正确"
                )
    
    async def _call_zhipu_ai(self, messages: List[Dict[str, str]]) -> str:
        """调用智谱AI API"""
        url = f"{self.api_base.rstrip('/')}/chat/completions" if self.api_base else "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _call_moonshot(self, messages: List[Dict[str, str]]) -> str:
        """调用月之暗面Kimi API"""
        url = f"{self.api_base.rstrip('/')}/chat/completions" if self.api_base else "https://api.moonshot.cn/v1/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """调用Ollama本地API"""
        url = f"{self.api_base.rstrip('/')}/api/chat" if self.api_base else "http://localhost:11434/api/chat"
        
        # Ollama使用不同的消息格式
        ollama_messages = []
        for msg in messages:
            if msg["role"] != "system":  # Ollama不支持system角色
                ollama_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                json={
                    "model": self.model_name,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]
    
    async def _call_custom(self, messages: List[Dict[str, str]]) -> str:
        """调用自定义API"""
        if not self.api_base:
            raise ValueError("自定义LLM需要配置api_base")
        
        url = f"{self.api_base.rstrip('/')}/chat/completions"
        
        # 使用自定义配置
        custom_config = self.extra_config.copy()
        custom_config.update({
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        })
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # 合并自定义headers
        if "headers" in self.extra_config:
            headers.update(self.extra_config["headers"])
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=custom_config
            )
            response.raise_for_status()
            result = response.json()
            
            # 尝试多种响应格式
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            elif "content" in result:
                return result["content"]
            elif "text" in result:
                return result["text"]
            else:
                return str(result)

