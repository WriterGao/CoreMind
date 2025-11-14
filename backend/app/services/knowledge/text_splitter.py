"""
文本切分服务
"""
from typing import List, Dict, Any
from loguru import logger


class TextSplitterService:
    """文本切分服务"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        初始化文本切分服务
        
        Args:
            chunk_size: 切片大小
            chunk_overlap: 切片重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """
        切分文本
        
        Args:
            text: 原始文本
            
        Returns:
            文本切片列表
        """
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
            )
            
            chunks = text_splitter.split_text(text)
            logger.info(f"文本切分完成，生成 {len(chunks)} 个切片")
            return chunks
            
        except Exception as e:
            logger.error(f"文本切分失败: {str(e)}")
            return [text]  # 失败时返回原文本
    
    def split_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        切分文档列表
        
        Args:
            documents: 文档列表，每个文档包含title, content, metadata
            
        Returns:
            切片列表，每个切片包含content, metadata
        """
        all_chunks = []
        
        for doc in documents:
            title = doc.get("title", "")
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            # 切分文本
            chunks = self.split_text(content)
            
            # 为每个切片添加元数据
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "title": title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                })
                
                all_chunks.append({
                    "content": chunk,
                    "metadata": chunk_metadata
                })
        
        logger.info(f"文档切分完成，共 {len(all_chunks)} 个切片")
        return all_chunks

