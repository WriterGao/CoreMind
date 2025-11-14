"""
接口管理API
"""
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.interface import CustomInterface, InterfaceType
from app.services.interface import InterfaceExecutor

router = APIRouter()


class InterfaceCreate(BaseModel):
    """接口创建模型"""
    name: str
    description: str = ""
    type: InterfaceType
    config: dict
    parameters: dict = {}
    code: str = ""


class InterfaceResponse(BaseModel):
    """接口响应模型"""
    id: str
    name: str
    description: str
    type: InterfaceType
    config: dict
    parameters: dict
    is_active: bool
    execution_count: int


class InterfaceExecuteRequest(BaseModel):
    """接口执行请求"""
    parameters: dict = {}


@router.post("", response_model=InterfaceResponse)
async def create_interface(
    interface_data: InterfaceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建接口"""
    
    # 创建接口
    interface = CustomInterface(
        user_id=uuid.UUID(current_user["user_id"]),
        name=interface_data.name,
        description=interface_data.description,
        type=interface_data.type,
        config=interface_data.config,
        parameters=interface_data.parameters,
        code=interface_data.code,
    )
    
    db.add(interface)
    await db.commit()
    await db.refresh(interface)
    
    return interface


@router.get("", response_model=List[InterfaceResponse])
async def list_interfaces(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取接口列表"""
    
    result = await db.execute(
        select(CustomInterface).where(
            CustomInterface.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    interfaces = result.scalars().all()
    
    return interfaces


@router.get("/{interface_id}", response_model=InterfaceResponse)
async def get_interface(
    interface_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取接口详情"""
    
    result = await db.execute(
        select(CustomInterface).where(
            CustomInterface.id == uuid.UUID(interface_id),
            CustomInterface.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    return interface


@router.delete("/{interface_id}")
async def delete_interface(
    interface_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除接口"""
    
    result = await db.execute(
        select(CustomInterface).where(
            CustomInterface.id == uuid.UUID(interface_id),
            CustomInterface.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    await db.delete(interface)
    await db.commit()
    
    return {"message": "接口已删除"}


@router.post("/{interface_id}/execute")
async def execute_interface(
    interface_id: str,
    execute_data: InterfaceExecuteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """执行接口"""
    
    result = await db.execute(
        select(CustomInterface).where(
            CustomInterface.id == uuid.UUID(interface_id),
            CustomInterface.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口不存在"
        )
    
    # 执行接口
    executor = InterfaceExecutor()
    
    config = {
        "type": interface.type.value,
        "url": interface.config.get("url"),
        "method": interface.config.get("method"),
        "headers": interface.config.get("headers"),
        "param_mapping": interface.config.get("param_mapping"),
        "code": interface.code,
    }
    
    result = await executor.execute(config, execute_data.parameters)
    
    # 更新执行统计
    interface.execution_count += 1
    from datetime import datetime
    interface.last_executed_at = datetime.utcnow()
    await db.commit()
    
    return result

