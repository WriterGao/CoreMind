"""
向量存储服务
"""
from typing import List, Dict, Any, Optional
import os
import chromadb
from chromadb.config import Settings
from loguru import logger

# 彻底禁用 ChromaDB 遥测
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# 禁用 ChromaDB 遥测模块
try:
    import chromadb.telemetry.events as chroma_telemetry
    # 禁用遥测捕获
    chroma_telemetry.capture = lambda *args, **kwargs: None
except (ImportError, AttributeError):
    pass

from app.core.config import settings
from app.services.knowledge.embeddings import EmbeddingService


class VectorStore:
    """向量存储服务"""
    
    def __init__(
        self,
        collection_name: str,
        embedding_model: Optional[str] = None
    ):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
            embedding_model: 嵌入模型名称
        """
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self._embedding_service: Optional[EmbeddingService] = None
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化ChromaDB客户端"""
        try:
            # 创建持久化客户端
            # 注意：遥测已在 main.py 启动时通过环境变量禁用
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"成功初始化向量存储集合: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"初始化向量存储失败: {str(e)}")
            raise
    
    def _get_embedding_service(self) -> EmbeddingService:
        """懒加载嵌入服务"""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService(self.embedding_model)
        return self._embedding_service

    async def add_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表，每个文档包含content和metadata
            
        Returns:
            文档ID列表
        """
        try:
            if not documents:
                return []
            
            # 提取内容
            contents = [doc["content"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # 生成嵌入向量
            embedding_service = self._get_embedding_service()
            embeddings = await embedding_service.embed_texts(contents)
            
            # 生成ID
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
            
            # 添加到ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量存储")
            return ids
            
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {str(e)}")
            raise
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 元数据过滤条件
            
        Returns:
            搜索结果列表，每个结果包含content, metadata, distance
        """
        try:
            # 生成查询向量
            embedding_service = self._get_embedding_service()
            query_embedding = await embedding_service.embed_text(query)
            
            # 搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict,
            )
            
            # 格式化结果
            formatted_results = []
            if results and results["documents"]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "id": results["ids"][0][i]
                    })
            
            logger.info(f"搜索完成，找到 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return []
    
    async def delete_by_ids(self, ids: List[str]) -> bool:
        """
        根据ID删除文档
        
        Args:
            ids: 文档ID列表
            
        Returns:
            删除是否成功
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"成功删除 {len(ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return False
    
    async def delete_collection(self) -> bool:
        """
        删除整个集合
        
        Returns:
            删除是否成功
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"成功删除集合: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"删除集合失败: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            统计信息
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
            }
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {str(e)}")
            return {}

