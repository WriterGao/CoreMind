"""
对话记忆管理
"""
from typing import List, Dict, Any, Optional
from loguru import logger


class ConversationMemory:
    """对话记忆管理"""
    
    def __init__(
        self,
        max_messages: int = 20,
        max_tokens: int = 4000
    ):
        """
        初始化对话记忆
        
        Args:
            max_messages: 最大消息数量
            max_tokens: 最大token数量（近似）
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str):
        """
        添加消息
        
        Args:
            role: 角色（user/assistant/system）
            content: 消息内容
        """
        self.messages.append({
            "role": role,
            "content": content
        })
        
        # 限制消息数量
        if len(self.messages) > self.max_messages:
            # 保留system消息，删除最早的对话
            system_messages = [m for m in self.messages if m["role"] == "system"]
            other_messages = [m for m in self.messages if m["role"] != "system"]
            
            # 保留最新的消息
            other_messages = other_messages[-(self.max_messages - len(system_messages)):]
            
            self.messages = system_messages + other_messages
        
        logger.debug(f"添加消息: {role}, 当前消息数: {len(self.messages)}")
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        获取所有消息
        
        Returns:
            消息列表
        """
        return self.messages.copy()
    
    def clear(self):
        """清空消息"""
        self.messages.clear()
        logger.info("清空对话记忆")
    
    def set_system_message(self, content: str):
        """
        设置系统消息
        
        Args:
            content: 系统消息内容
        """
        # 移除旧的系统消息
        self.messages = [m for m in self.messages if m["role"] != "system"]
        
        # 添加新的系统消息到开头
        self.messages.insert(0, {
            "role": "system",
            "content": content
        })
        
        logger.info("设置系统消息")
    
    def get_last_messages(self, n: int) -> List[Dict[str, str]]:
        """
        获取最后N条消息
        
        Args:
            n: 消息数量
            
        Returns:
            消息列表
        """
        return self.messages[-n:] if n > 0 else []
    
    def count_tokens(self) -> int:
        """
        估算token数量（简单估算）
        
        Returns:
            token数量
        """
        total_chars = sum(len(m["content"]) for m in self.messages)
        # 粗略估算：英文约4个字符1个token，中文约1.5个字符1个token
        return int(total_chars / 3)

