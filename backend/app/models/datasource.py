"""
数据源模型
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, DateTime, Enum, JSON, 
    ForeignKey, Boolean, Text, Integer
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class DataSourceType(PyEnum):
    """数据源类型"""
    LOCAL_FILE = "local_file"  # 本地文件
    DATABASE = "database"  # 数据库
    API = "api"  # API接口
    WEB_CRAWLER = "web_crawler"  # 网页爬虫
    CLOUD_STORAGE = "cloud_storage"  # 云存储


class DataSource(Base):
    """数据源表"""
    __tablename__ = "datasources"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="数据源ID"
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
        comment="数据源名称"
    )
    description = Column(
        Text,
        comment="数据源描述"
    )
    type = Column(
        Enum(DataSourceType),
        nullable=False,
        comment="数据源类型"
    )
    config = Column(
        JSON,
        nullable=False,
        comment="数据源配置（JSON格式）"
    )
    usage_doc = Column(
        Text,
        comment="使用规范文档（如数据库表设计、接口文档等）"
    )
    schema_info = Column(
        JSON,
        comment="结构信息（如数据库schema、API参数等）"
    )
    examples = Column(
        JSON,
        comment="使用示例（JSON数组）"
    )
    is_active = Column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    sync_frequency = Column(
        Integer,
        comment="同步频率（分钟）"
    )
    last_sync_at = Column(
        DateTime,
        comment="最后同步时间"
    )
    sync_status = Column(
        String(50),
        default="pending",
        comment="同步状态：pending/running/success/failed"
    )
    sync_error = Column(
        Text,
        comment="同步错误信息"
    )
    total_documents = Column(
        Integer,
        default=0,
        comment="文档总数"
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
        return f"<DataSource(id={self.id}, name={self.name}, type={self.type})>"

