"""
用户模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="用户ID"
    )
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名"
    )
    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱"
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="密码哈希"
    )
    full_name = Column(
        String(100),
        comment="全名"
    )
    is_active = Column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    is_superuser = Column(
        Boolean,
        default=False,
        comment="是否超级用户"
    )
    avatar_url = Column(
        String(500),
        comment="头像URL"
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
        return f"<User(id={self.id}, username={self.username})>"

