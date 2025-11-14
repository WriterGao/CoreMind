"""
自定义接口模型
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


class InterfaceType(PyEnum):
    """接口类型"""
    FUNCTION = "function"  # 内部函数
    API = "api"  # 外部API
    DATABASE = "database"  # 数据库操作
    FILE = "file"  # 文件处理


class CustomInterface(Base):
    """自定义接口表"""
    __tablename__ = "custom_interfaces"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="接口ID"
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
        comment="接口名称"
    )
    description = Column(
        Text,
        comment="接口描述"
    )
    type = Column(
        Enum(InterfaceType),
        nullable=False,
        comment="接口类型"
    )
    config = Column(
        JSON,
        nullable=False,
        comment="接口配置（JSON格式）"
    )
    parameters = Column(
        JSON,
        comment="参数定义（JSON Schema格式）"
    )
    response_schema = Column(
        JSON,
        comment="响应格式（JSON Schema）"
    )
    code = Column(
        Text,
        comment="函数代码（仅函数类型）"
    )
    is_active = Column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    execution_count = Column(
        Integer,
        default=0,
        comment="执行次数"
    )
    last_executed_at = Column(
        DateTime,
        comment="最后执行时间"
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
        return f"<CustomInterface(id={self.id}, name={self.name}, type={self.type})>"

