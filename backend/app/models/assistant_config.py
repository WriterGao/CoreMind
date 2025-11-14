"""
AI助手配置
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, JSON,
    ForeignKey, Boolean, Text, Integer
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from app.core.database import Base


class AssistantConfig(Base):
    """AI助手配置表"""
    __tablename__ = "assistant_configs"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="配置ID"
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
        comment="助手名称"
    )
    description = Column(
        Text,
        comment="助手描述"
    )
    llm_config_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llm_configs.id", ondelete="SET NULL"),
        comment="使用的LLM配置ID"
    )
    system_prompt = Column(
        Text,
        comment="系统提示词"
    )
    knowledge_base_ids = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        comment="关联的知识库ID列表"
    )
    datasource_ids = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        comment="可用的数据源ID列表"
    )
    interface_ids = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        comment="可用的接口ID列表"
    )
    enable_knowledge_base = Column(
        Boolean,
        default=True,
        comment="是否启用知识库检索"
    )
    enable_datasource = Column(
        Boolean,
        default=True,
        comment="是否启用数据源查询"
    )
    enable_interface = Column(
        Boolean,
        default=True,
        comment="是否启用接口调用"
    )
    auto_route = Column(
        Boolean,
        default=True,
        comment="是否自动路由（智能判断使用知识库还是数据源）"
    )
    max_history = Column(
        Integer,
        default=10,
        comment="最大历史消息数"
    )
    config = Column(
        JSON,
        comment="其他配置（JSON格式）"
    )
    is_default = Column(
        Boolean,
        default=False,
        comment="是否默认助手"
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
        return f"<AssistantConfig(id={self.id}, name={self.name})>"

