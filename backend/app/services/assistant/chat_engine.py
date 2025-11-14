"""
对话引擎
"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from loguru import logger

from app.core.config import settings
from app.services.assistant.memory import ConversationMemory
from app.services.knowledge.vectorstore import VectorStore
from app.services.interface.tool_manager import ToolManager


class ChatEngine:
    """对话引擎"""
    
    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
    ):
        """
        初始化对话引擎
        
        Args:
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            system_prompt: 系统提示词
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.memory = ConversationMemory()
        self.vectorstore: Optional[VectorStore] = None
        self.tool_manager = ToolManager()
        self.llm = None
        
        # 设置系统提示词
        if system_prompt:
            self.memory.set_system_message(system_prompt)
        else:
            default_prompt = "你是CoreMind AI助手，一个智能、友好、专业的AI助手。"
            self.memory.set_system_message(default_prompt)
        
        self._initialize_llm()
    
    def _initialize_llm(self):
        """初始化LLM"""
        try:
            if settings.OPENAI_API_KEY:
                from langchain_openai import ChatOpenAI
                
                self.llm = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    openai_api_key=settings.OPENAI_API_KEY,
                )
                logger.info(f"使用OpenAI模型: {self.model}")
            
            elif settings.AZURE_OPENAI_API_KEY:
                from langchain_openai import AzureChatOpenAI
                
                self.llm = AzureChatOpenAI(
                    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    openai_api_key=settings.AZURE_OPENAI_API_KEY,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                logger.info("使用Azure OpenAI模型")
            
            else:
                # 使用本地模型（Ollama）
                from langchain.llms import Ollama
                
                self.llm = Ollama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.OLLAMA_MODEL,
                    temperature=self.temperature,
                )
                logger.info(f"使用Ollama本地模型: {settings.OLLAMA_MODEL}")
        
        except Exception as e:
            logger.error(f"初始化LLM失败: {str(e)}")
            raise
    
    def set_knowledge_base(self, vectorstore: VectorStore):
        """
        设置知识库
        
        Args:
            vectorstore: 向量存储
        """
        self.vectorstore = vectorstore
        logger.info("设置知识库")
    
    def register_tools(self, interfaces: List[Dict[str, Any]]):
        """
        注册工具
        
        Args:
            interfaces: 接口配置列表
        """
        for interface in interfaces:
            self.tool_manager.register_interface(interface)
        logger.info(f"注册了 {len(interfaces)} 个工具")
    
    async def chat(
        self,
        message: str,
        use_knowledge_base: bool = True,
        use_tools: bool = False,
    ) -> str:
        """
        对话
        
        Args:
            message: 用户消息
            use_knowledge_base: 是否使用知识库
            use_tools: 是否使用工具
            
        Returns:
            AI回复
        """
        try:
            # 添加用户消息到记忆
            self.memory.add_message("user", message)
            
            # 检索相关知识
            context = ""
            if use_knowledge_base and self.vectorstore:
                context = await self._retrieve_knowledge(message)
            
            # 构建提示
            messages = self.memory.get_messages()
            
            # 如果有知识库上下文，添加到最后一条用户消息
            if context:
                enhanced_message = f"相关知识：\n{context}\n\n用户问题：{message}"
                messages[-1]["content"] = enhanced_message
            
            # 转换为LangChain消息格式
            from langchain.schema import HumanMessage, AIMessage, SystemMessage
            
            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    lc_messages.append(AIMessage(content=msg["content"]))
            
            # 调用LLM
            response = await self.llm.ainvoke(lc_messages)
            
            # 提取回复内容
            if hasattr(response, "content"):
                reply = response.content
            else:
                reply = str(response)
            
            # 添加助手回复到记忆
            self.memory.add_message("assistant", reply)
            
            logger.info("对话完成")
            return reply
            
        except Exception as e:
            logger.error(f"对话失败: {str(e)}")
            return f"抱歉，我遇到了一个错误: {str(e)}"
    
    async def stream_chat(
        self,
        message: str,
        use_knowledge_base: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话
        
        Args:
            message: 用户消息
            use_knowledge_base: 是否使用知识库
            
        Yields:
            AI回复片段
        """
        try:
            # 添加用户消息到记忆
            self.memory.add_message("user", message)
            
            # 检索相关知识
            context = ""
            if use_knowledge_base and self.vectorstore:
                context = await self._retrieve_knowledge(message)
            
            # 构建提示
            messages = self.memory.get_messages()
            
            if context:
                enhanced_message = f"相关知识：\n{context}\n\n用户问题：{message}"
                messages[-1]["content"] = enhanced_message
            
            # 转换为LangChain消息格式
            from langchain.schema import HumanMessage, AIMessage, SystemMessage
            
            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    lc_messages.append(AIMessage(content=msg["content"]))
            
            # 流式调用
            full_response = ""
            async for chunk in self.llm.astream(lc_messages):
                if hasattr(chunk, "content"):
                    content = chunk.content
                else:
                    content = str(chunk)
                
                full_response += content
                yield content
            
            # 添加完整回复到记忆
            self.memory.add_message("assistant", full_response)
            
            logger.info("流式对话完成")
            
        except Exception as e:
            logger.error(f"流式对话失败: {str(e)}")
            yield f"抱歉，我遇到了一个错误: {str(e)}"
    
    async def _retrieve_knowledge(self, query: str, top_k: int = 3) -> str:
        """
        检索知识库
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            知识库上下文
        """
        try:
            results = await self.vectorstore.search(query, top_k=top_k)
            
            if not results:
                return ""
            
            # 构建上下文
            context_parts = []
            for i, result in enumerate(results, 1):
                content = result["content"]
                context_parts.append(f"[{i}] {content}")
            
            context = "\n\n".join(context_parts)
            logger.info(f"检索到 {len(results)} 条相关知识")
            return context
            
        except Exception as e:
            logger.error(f"检索知识库失败: {str(e)}")
            return ""
    
    def clear_memory(self):
        """清空对话记忆"""
        self.memory.clear()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        获取对话历史
        
        Returns:
            对话历史
        """
        return self.memory.get_messages()

