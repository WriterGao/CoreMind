"""
API数据源
"""
from typing import List, Dict, Any
import httpx
from loguru import logger

from app.services.datasource.base import BaseDataSource


class APIDataSource(BaseDataSource):
    """API数据源"""
    
    async def connect(self) -> bool:
        """测试API连接"""
        try:
            url = self.config.get("url")
            if not url:
                raise ValueError("未指定API URL")
            
            # 测试连接
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.config.get("headers", {}),
                    timeout=10.0
                )
                response.raise_for_status()
            
            self.connected = True
            logger.info(f"成功连接到API: {url}")
            return True
            
        except Exception as e:
            logger.error(f"连接API失败: {str(e)}")
            return False
    
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """获取API数据"""
        if not self.connected:
            await self.connect()
        
        results = []
        
        try:
            url = self.config.get("url")
            method = self.config.get("method", "GET").upper()
            headers = self.config.get("headers", {})
            params = self.config.get("params", {})
            body = self.config.get("body", {})
            
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=30.0
                    )
                elif method == "POST":
                    response = await client.post(
                        url,
                        headers=headers,
                        json=body,
                        timeout=30.0
                    )
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                data = response.json()
            
            # 解析响应数据
            results = self._parse_response(data)
            
            logger.info(f"从API获取了 {len(results)} 个文档")
            return results
            
        except Exception as e:
            logger.error(f"获取API数据失败: {str(e)}")
            return []
    
    def _parse_response(self, data: Any) -> List[Dict[str, Any]]:
        """解析API响应"""
        results = []
        
        # 获取数据路径配置
        data_path = self.config.get("data_path", "")
        title_field = self.config.get("title_field", "title")
        content_fields = self.config.get("content_fields", ["content"])
        
        # 根据数据路径提取数据
        if data_path:
            for path_part in data_path.split("."):
                if isinstance(data, dict):
                    data = data.get(path_part, [])
                else:
                    break
        
        # 确保数据是列表
        if not isinstance(data, list):
            data = [data]
        
        # 解析每条数据
        for item in data:
            if not isinstance(item, dict):
                continue
            
            # 提取标题
            title = str(item.get(title_field, "未命名"))
            
            # 提取并合并内容字段
            content_parts = []
            for field in content_fields:
                if field in item:
                    content_parts.append(str(item[field]))
            
            content = " ".join(content_parts)
            
            if content:
                results.append({
                    "title": title,
                    "content": self.preprocess_content(content),
                    "metadata": item
                })
        
        return results
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        return True

