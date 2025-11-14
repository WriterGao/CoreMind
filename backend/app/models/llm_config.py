"""
LLM模型配置
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, DateTime, Enum, JSON,
    ForeignKey, Boolean, Text, Float, Integer
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class LLMProvider(PyEnum):
    """LLM提供商"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    DEEPSEEK = "deepseek"
    ALIBABA_QWEN = "alibaba_qwen"
    ZHIPU_AI = "zhipu_ai"
    BAIDU_WENXIN = "baidu_wenxin"
    MOONSHOT = "moonshot"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class LLMConfig(Base):
    """LLM配置表"""
    __tablename__ = "llm_configs"
    
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
        comment="配置名称"
    )
    provider = Column(
        Enum(LLMProvider),
        nullable=False,
        comment="提供商"
    )
    model_name = Column(
        String(100),
        nullable=False,
        comment="模型名称"
    )
    api_key = Column(
        Text,
        comment="API密钥（加密存储）"
    )
    api_base = Column(
        String(500),
        comment="API基础URL"
    )
    config = Column(
        JSON,
        comment="额外配置（JSON格式）"
    )
    temperature = Column(
        Float,
        default=0.7,
        comment="温度参数"
    )
    max_tokens = Column(
        Integer,
        default=2000,
        comment="最大token数"
    )
    is_default = Column(
        Boolean,
        default=False,
        comment="是否默认配置"
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
        return f"<LLMConfig(id={self.id}, name={self.name}, provider={self.provider})>"

