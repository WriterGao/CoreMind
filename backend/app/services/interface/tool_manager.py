"""
工具管理器
"""
from typing import List, Dict, Any
from loguru import logger

from app.services.interface.executor import InterfaceExecutor


class ToolManager:
    """工具管理器 - 用于LangChain集成"""
    
    def __init__(self):
        self.executor = InterfaceExecutor()
        self.tools = []
    
    def register_interface(self, interface_config: Dict[str, Any]):
        """
        注册接口为工具
        
        Args:
            interface_config: 接口配置
        """
        tool = {
            "name": interface_config.get("name"),
            "description": interface_config.get("description"),
            "parameters": interface_config.get("parameters", {}),
            "config": interface_config
        }
        
        self.tools.append(tool)
        logger.info(f"注册工具: {tool['name']}")
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        获取工具模式（用于LLM）
        
        Returns:
            工具模式列表
        """
        schemas = []
        
        for tool in self.tools:
            schema = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            schemas.append(schema)
        
        return schemas
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 参数
            
        Returns:
            执行结果
        """
        # 查找工具
        tool = None
        for t in self.tools:
            if t["name"] == tool_name:
                tool = t
                break
        
        if not tool:
            return {
                "success": False,
                "error": f"未找到工具: {tool_name}"
            }
        
        # 执行
        result = await self.executor.execute(tool["config"], parameters)
        return result
    
    def list_tools(self) -> List[str]:
        """
        列出所有工具名称
        
        Returns:
            工具名称列表
        """
        return [tool["name"] for tool in self.tools]

