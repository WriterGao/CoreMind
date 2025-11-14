"""
对话模型
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, Integer, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from app.core.database import Base


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="会话ID"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    assistant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assistant_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联的助手配置ID"
    )
    knowledge_base_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联的知识库ID"
    )
    title = Column(
        String(200),
        nullable=False,
        comment="会话标题"
    )
    system_prompt = Column(
        Text,
        comment="系统提示词"
    )
    model = Column(
        String(100),
        default="gpt-4",
        comment="使用的模型"
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
    message_count = Column(
        Integer,
        default=0,
        comment="消息数量"
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
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="消息ID"
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="会话ID"
    )
    role = Column(
        String(20),
        nullable=False,
        comment="角色：user/assistant/system"
    )
    content = Column(
        Text,
        nullable=False,
        comment="消息内容"
    )
    msg_metadata = Column(
        JSON,
        comment="元数据（如工具调用、知识库引用等）"
    )
    tokens = Column(
        Integer,
        comment="token数量"
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role})>"

