"""
接口执行器
"""
from typing import Dict, Any, Optional
import httpx
from loguru import logger


class InterfaceExecutor:
    """接口执行器"""
    
    async def execute(
        self,
        interface_config: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行接口
        
        Args:
            interface_config: 接口配置
            parameters: 执行参数
            
        Returns:
            执行结果
        """
        interface_type = interface_config.get("type")
        
        try:
            if interface_type == "function":
                return await self._execute_function(interface_config, parameters)
            elif interface_type == "api":
                return await self._execute_api(interface_config, parameters)
            elif interface_type == "database":
                return await self._execute_database(interface_config, parameters)
            elif interface_type == "file":
                return await self._execute_file(interface_config, parameters)
            else:
                raise ValueError(f"不支持的接口类型: {interface_type}")
                
        except Exception as e:
            logger.error(f"执行接口失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_function(
        self,
        config: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行函数接口"""
        try:
            # 获取函数代码
            code = config.get("code", "")
            
            # 创建安全的执行环境
            exec_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "range": range,
                    "sum": sum,
                    "max": max,
                    "min": min,
                }
            }
            
            # 执行代码
            exec(code, exec_globals)
            
            # 调用主函数
            if "main" in exec_globals:
                result = exec_globals["main"](**parameters)
                return {
                    "success": True,
                    "result": result
                }
            else:
                raise ValueError("代码中未找到main函数")
                
        except Exception as e:
            logger.error(f"执行函数失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_api(
        self,
        config: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行API接口"""
        try:
            url = config.get("url", "")
            method = config.get("method", "GET").upper()
            headers = config.get("headers", {})
            
            # 参数映射
            param_mapping = config.get("param_mapping", {})
            mapped_params = {}
            for key, value in param_mapping.items():
                if value in parameters:
                    mapped_params[key] = parameters[value]
            
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(
                        url,
                        headers=headers,
                        params=mapped_params,
                        timeout=30.0
                    )
                elif method == "POST":
                    response = await client.post(
                        url,
                        headers=headers,
                        json=mapped_params,
                        timeout=30.0
                    )
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                
                return {
                    "success": True,
                    "result": response.json(),
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"执行API失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_database(
        self,
        config: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行数据库操作"""
        try:
            # 这里可以实现数据库操作
            # 为了安全考虑，可以限制只能执行SELECT查询
            query = config.get("query", "")
            
            # 参数替换
            for key, value in parameters.items():
                query = query.replace(f":{key}", str(value))
            
            # 执行查询（示例，需要根据实际数据库类型实现）
            return {
                "success": True,
                "result": "数据库操作功能待实现"
            }
            
        except Exception as e:
            logger.error(f"执行数据库操作失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_file(
        self,
        config: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行文件操作"""
        try:
            operation = config.get("operation", "read")
            file_path = parameters.get("file_path", "")
            
            if operation == "read":
                import aiofiles
                async with aiofiles.open(file_path, "r") as f:
                    content = await f.read()
                return {
                    "success": True,
                    "result": content
                }
            elif operation == "write":
                content = parameters.get("content", "")
                import aiofiles
                async with aiofiles.open(file_path, "w") as f:
                    await f.write(content)
                return {
                    "success": True,
                    "result": "文件写入成功"
                }
            else:
                raise ValueError(f"不支持的文件操作: {operation}")
                
        except Exception as e:
            logger.error(f"执行文件操作失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

