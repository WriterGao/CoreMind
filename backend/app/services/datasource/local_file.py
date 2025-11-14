"""
本地文件数据源
"""
import os
from pathlib import Path
from typing import List, Dict, Any
import aiofiles
from loguru import logger

from app.services.datasource.base import BaseDataSource
from app.utils.file_parser import FileParser


class LocalFileDataSource(BaseDataSource):
    """本地文件数据源"""
    
    async def connect(self) -> bool:
        """连接到本地文件系统"""
        try:
            file_path = self.config.get("file_path")
            if not file_path:
                raise ValueError("未指定文件路径")
            
            path = Path(file_path)
            
            # 检查路径是否存在
            if not path.exists():
                raise FileNotFoundError(f"文件或目录不存在: {file_path}")
            
            self.connected = True
            logger.info(f"成功连接到本地文件: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"连接本地文件失败: {str(e)}")
            return False
    
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """获取文件数据"""
        if not self.connected:
            await self.connect()
        
        results = []
        file_path = self.config.get("file_path")
        path = Path(file_path)
        
        try:
            # 如果是目录，遍历所有支持的文件
            if path.is_dir():
                results = await self._process_directory(path)
            else:
                # 单个文件
                result = await self._process_file(path)
                if result:
                    results.append(result)
            
            logger.info(f"从本地文件获取了 {len(results)} 个文档")
            return results
            
        except Exception as e:
            logger.error(f"获取本地文件数据失败: {str(e)}")
            return []
    
    async def _process_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """处理目录"""
        results = []
        supported_extensions = self.config.get(
            "supported_extensions",
            [".txt", ".pdf", ".docx", ".xlsx", ".csv", ".md"]
        )
        
        # 递归遍历
        recursive = self.config.get("recursive", True)
        
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")
        
        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                result = await self._process_file(file_path)
                if result:
                    results.append(result)
        
        return results
    
    async def _process_file(self, file_path: Path) -> Dict[str, Any]:
        """处理单个文件"""
        try:
            # 使用文件解析器
            parser = FileParser()
            content = await parser.parse_file(str(file_path))
            
            if not content:
                return None
            
            # 预处理内容
            content = self.preprocess_content(content)
            
            return {
                "title": file_path.name,
                "content": content,
                "metadata": {
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lower(),
                    "file_size": file_path.stat().st_size,
                    "modified_time": file_path.stat().st_mtime,
                }
            }
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
            return None
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        return True

