"""
知识库模型
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, 
    Boolean, Text, Integer, Float
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from app.core.database import Base


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="知识库ID"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    name = Column(
        String(100),
        nullable=False,
        comment="知识库名称"
    )
    description = Column(
        Text,
        comment="知识库描述"
    )
    embedding_model = Column(
        String(100),
        nullable=False,
        default="text-embedding-ada-002",
        comment="嵌入模型"
    )
    collection_name = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="ChromaDB集合名称"
    )
    chunk_size = Column(
        Integer,
        default=1000,
        comment="文本切片大小"
    )
    chunk_overlap = Column(
        Integer,
        default=200,
        comment="文本切片重叠"
    )
    total_documents = Column(
        Integer,
        default=0,
        comment="文档总数"
    )
    total_chunks = Column(
        Integer,
        default=0,
        comment="切片总数"
    )
    is_active = Column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"


class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="文档ID"
    )
    knowledge_base_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="知识库ID"
    )
    datasource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="数据源ID"
    )
    title = Column(
        String(200),
        nullable=False,
        comment="文档标题"
    )
    content = Column(
        Text,
        nullable=False,
        comment="文档内容"
    )
    file_path = Column(
        String(500),
        comment="文件路径"
    )
    file_type = Column(
        String(50),
        comment="文件类型"
    )
    file_size = Column(
        Integer,
        comment="文件大小（字节）"
    )
    doc_metadata = Column(
        Text,
        comment="元数据（JSON字符串）"
    )
    chunk_count = Column(
        Integer,
        default=0,
        comment="切片数量"
    )
    is_processed = Column(
        Boolean,
        default=False,
        comment="是否已处理"
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title})>"


class DocumentChunk(Base):
    """文档切片表"""
    __tablename__ = "document_chunks"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="切片ID"
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="文档ID"
    )
    knowledge_base_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="知识库ID"
    )
    content = Column(
        Text,
        nullable=False,
        comment="切片内容"
    )
    chunk_index = Column(
        Integer,
        nullable=False,
        comment="切片索引"
    )
    vector_id = Column(
        String(100),
        comment="向量数据库中的ID"
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id})>"

