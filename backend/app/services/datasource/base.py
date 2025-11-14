"""
数据源基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseDataSource(ABC):
    """数据源基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据源
        
        Args:
            config: 数据源配置
        """
        self.config = config
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        连接到数据源
        
        Returns:
            连接是否成功
        """
        pass
    
    @abstractmethod
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """
        获取数据
        
        Returns:
            数据列表，每个元素是一个字典，包含：
            - title: 文档标题
            - content: 文档内容
            - metadata: 元数据
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开连接
        
        Returns:
            断开是否成功
        """
        pass
    
    async def validate_config(self) -> Dict[str, Any]:
        """
        验证配置
        
        Returns:
            验证结果，包含：
            - valid: 是否有效
            - message: 验证消息
        """
        try:
            connected = await self.connect()
            if connected:
                await self.disconnect()
                return {"valid": True, "message": "配置验证成功"}
            else:
                return {"valid": False, "message": "无法连接到数据源"}
        except Exception as e:
            return {"valid": False, "message": f"配置验证失败: {str(e)}"}
    
    def preprocess_content(self, content: str) -> str:
        """
        预处理内容
        
        Args:
            content: 原始内容
            
        Returns:
            处理后的内容
        """
        # 移除多余空白
        content = " ".join(content.split())
        # 限制长度（可配置）
        max_length = self.config.get("max_content_length", 1000000)
        if len(content) > max_length:
            content = content[:max_length]
        return content

