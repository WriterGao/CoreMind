"""
文件解析工具
"""
from pathlib import Path
from typing import Optional
import aiofiles
from loguru import logger


class FileParser:
    """文件解析器"""
    
    async def parse_file(self, file_path: str) -> Optional[str]:
        """
        解析文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容文本
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        try:
            if suffix == ".txt":
                return await self._parse_txt(file_path)
            elif suffix == ".pdf":
                return await self._parse_pdf(file_path)
            elif suffix == ".docx":
                return await self._parse_docx(file_path)
            elif suffix == ".xlsx":
                return await self._parse_xlsx(file_path)
            elif suffix == ".csv":
                return await self._parse_csv(file_path)
            elif suffix == ".md":
                return await self._parse_txt(file_path)  # Markdown作为文本处理
            else:
                logger.warning(f"不支持的文件类型: {suffix}")
                return None
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {str(e)}")
            return None
    
    async def _parse_txt(self, file_path: str) -> str:
        """解析文本文件"""
        async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = await f.read()
        return content
    
    async def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"解析PDF失败: {str(e)}")
            return ""
    
    async def _parse_docx(self, file_path: str) -> str:
        """解析Word文档"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_parts.append(paragraph.text)
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"解析DOCX失败: {str(e)}")
            return ""
    
    async def _parse_xlsx(self, file_path: str) -> str:
        """解析Excel文件"""
        try:
            import pandas as pd
            
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            text_parts = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                # 转换为文本
                sheet_text = df.to_string(index=False)
                text_parts.append(f"工作表: {sheet_name}\n{sheet_text}")
            
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"解析XLSX失败: {str(e)}")
            return ""
    
    async def _parse_csv(self, file_path: str) -> str:
        """解析CSV文件"""
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            return df.to_string(index=False)
        except Exception as e:
            logger.error(f"解析CSV失败: {str(e)}")
            return ""

