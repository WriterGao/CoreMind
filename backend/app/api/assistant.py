"""
AI助手配置管理API
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from uuid import UUID
import uuid as uuid_lib

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.assistant_config import AssistantConfig

router = APIRouter()


class AssistantConfigCreate(BaseModel):
    """创建助手配置"""
    name: str
    description: Optional[str] = None
    llm_config_id: Optional[str] = None
    system_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = []
    datasource_ids: Optional[List[str]] = []
    interface_ids: Optional[List[str]] = []
    enable_knowledge_base: Optional[bool] = True
    enable_datasource: Optional[bool] = True
    enable_interface: Optional[bool] = True
    auto_route: Optional[bool] = True
    max_history: Optional[int] = 10
    config: Optional[dict] = None
    is_default: Optional[bool] = False


class AssistantConfigUpdate(BaseModel):
    """更新助手配置"""
    name: Optional[str] = None
    description: Optional[str] = None
    llm_config_id: Optional[str] = None
    system_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None
    datasource_ids: Optional[List[str]] = None
    interface_ids: Optional[List[str]] = None
    enable_knowledge_base: Optional[bool] = None
    enable_datasource: Optional[bool] = None
    enable_interface: Optional[bool] = None
    auto_route: Optional[bool] = None
    max_history: Optional[int] = None
    config: Optional[dict] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AssistantConfigResponse(BaseModel):
    """助手配置响应"""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    llm_config_id: Optional[str] = None
    system_prompt: Optional[str] = None
    knowledge_base_ids: List[str]
    datasource_ids: List[str]
    interface_ids: List[str]
    enable_knowledge_base: bool
    enable_datasource: bool
    enable_interface: bool
    auto_route: bool
    max_history: int
    config: Optional[dict] = None
    is_default: bool
    is_active: bool
    
    class Config:
        from_attributes = True


@router.post("", response_model=AssistantConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_assistant(
    assistant_data: AssistantConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建AI助手配置"""
    # 如果设置为默认，先取消其他默认配置
    if assistant_data.is_default:
        await db.execute(
            update(AssistantConfig)
            .where(AssistantConfig.user_id == uuid_lib.UUID(current_user["user_id"]))
            .where(AssistantConfig.is_default == True)
            .values(is_default=False)
        )
    
    # 转换UUID列表
    knowledge_base_uuids = [UUID(kid) for kid in assistant_data.knowledge_base_ids] if assistant_data.knowledge_base_ids else []
    datasource_uuids = [UUID(did) for did in assistant_data.datasource_ids] if assistant_data.datasource_ids else []
    interface_uuids = [UUID(iid) for iid in assistant_data.interface_ids] if assistant_data.interface_ids else []
    
    # 创建助手配置
    assistant = AssistantConfig(
        user_id=uuid_lib.UUID(current_user["user_id"]),
        name=assistant_data.name,
        description=assistant_data.description,
        llm_config_id=UUID(assistant_data.llm_config_id) if assistant_data.llm_config_id else None,
        system_prompt=assistant_data.system_prompt,
        knowledge_base_ids=knowledge_base_uuids,
        datasource_ids=datasource_uuids,
        interface_ids=interface_uuids,
        enable_knowledge_base=assistant_data.enable_knowledge_base,
        enable_datasource=assistant_data.enable_datasource,
        enable_interface=assistant_data.enable_interface,
        auto_route=assistant_data.auto_route,
        max_history=assistant_data.max_history,
        config=assistant_data.config,
        is_default=assistant_data.is_default
    )
    
    db.add(assistant)
    await db.commit()
    await db.refresh(assistant)
    
    return AssistantConfigResponse(
        id=str(assistant.id),
        user_id=str(assistant.user_id),
        name=assistant.name,
        description=assistant.description,
        llm_config_id=str(assistant.llm_config_id) if assistant.llm_config_id else None,
        system_prompt=assistant.system_prompt,
        knowledge_base_ids=[str(kid) for kid in assistant.knowledge_base_ids] if assistant.knowledge_base_ids else [],
        datasource_ids=[str(did) for did in assistant.datasource_ids] if assistant.datasource_ids else [],
        interface_ids=[str(iid) for iid in assistant.interface_ids] if assistant.interface_ids else [],
        enable_knowledge_base=assistant.enable_knowledge_base,
        enable_datasource=assistant.enable_datasource,
        enable_interface=assistant.enable_interface,
        auto_route=assistant.auto_route,
        max_history=assistant.max_history,
        config=assistant.config,
        is_default=assistant.is_default,
        is_active=assistant.is_active
    )


@router.get("", response_model=List[AssistantConfigResponse])
async def get_assistants(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取当前用户的所有助手配置"""
    result = await db.execute(
        select(AssistantConfig)
        .where(AssistantConfig.user_id == uuid_lib.UUID(current_user["user_id"]))
        .order_by(AssistantConfig.is_default.desc(), AssistantConfig.created_at.desc())
    )
    assistants = result.scalars().all()
    
    return [
        AssistantConfigResponse(
            id=str(assistant.id),
            user_id=str(assistant.user_id),
            name=assistant.name,
            description=assistant.description,
            llm_config_id=str(assistant.llm_config_id) if assistant.llm_config_id else None,
            system_prompt=assistant.system_prompt,
            knowledge_base_ids=[str(kid) for kid in assistant.knowledge_base_ids] if assistant.knowledge_base_ids else [],
            datasource_ids=[str(did) for did in assistant.datasource_ids] if assistant.datasource_ids else [],
            interface_ids=[str(iid) for iid in assistant.interface_ids] if assistant.interface_ids else [],
            enable_knowledge_base=assistant.enable_knowledge_base,
            enable_datasource=assistant.enable_datasource,
            enable_interface=assistant.enable_interface,
            auto_route=assistant.auto_route,
            max_history=assistant.max_history,
            config=assistant.config,
            is_default=assistant.is_default,
            is_active=assistant.is_active
        )
        for assistant in assistants
    ]


@router.get("/{assistant_id}", response_model=AssistantConfigResponse)
async def get_assistant(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取指定助手配置"""
    result = await db.execute(
        select(AssistantConfig).where(
            AssistantConfig.id == uuid_lib.UUID(assistant_id),
            AssistantConfig.user_id == uuid_lib.UUID(current_user["user_id"])
        )
    )
    assistant = result.scalar_one_or_none()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="助手配置不存在"
        )
    
    return AssistantConfigResponse(
        id=str(assistant.id),
        user_id=str(assistant.user_id),
        name=assistant.name,
        description=assistant.description,
        llm_config_id=str(assistant.llm_config_id) if assistant.llm_config_id else None,
        system_prompt=assistant.system_prompt,
        knowledge_base_ids=[str(kid) for kid in assistant.knowledge_base_ids] if assistant.knowledge_base_ids else [],
        datasource_ids=[str(did) for did in assistant.datasource_ids] if assistant.datasource_ids else [],
        interface_ids=[str(iid) for iid in assistant.interface_ids] if assistant.interface_ids else [],
        enable_knowledge_base=assistant.enable_knowledge_base,
        enable_datasource=assistant.enable_datasource,
        enable_interface=assistant.enable_interface,
        auto_route=assistant.auto_route,
        max_history=assistant.max_history,
        config=assistant.config,
        is_default=assistant.is_default,
        is_active=assistant.is_active
    )


@router.put("/{assistant_id}", response_model=AssistantConfigResponse)
async def update_assistant(
    assistant_id: str,
    update_data: AssistantConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新助手配置"""
    result = await db.execute(
        select(AssistantConfig).where(
            AssistantConfig.id == uuid_lib.UUID(assistant_id),
            AssistantConfig.user_id == uuid_lib.UUID(current_user["user_id"])
        )
    )
    assistant = result.scalar_one_or_none()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="助手配置不存在"
        )
    
    # 如果设置为默认，先取消其他默认配置
    if update_data.is_default:
        await db.execute(
            update(AssistantConfig)
            .where(AssistantConfig.user_id == uuid_lib.UUID(current_user["user_id"]))
            .where(AssistantConfig.id != uuid_lib.UUID(assistant_id))
            .where(AssistantConfig.is_default == True)
            .values(is_default=False)
        )
    
    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    
    # 转换UUID列表
    if "knowledge_base_ids" in update_dict and update_dict["knowledge_base_ids"] is not None:
        update_dict["knowledge_base_ids"] = [UUID(kid) for kid in update_dict["knowledge_base_ids"]]
    if "datasource_ids" in update_dict and update_dict["datasource_ids"] is not None:
        update_dict["datasource_ids"] = [UUID(did) for did in update_dict["datasource_ids"]]
    if "interface_ids" in update_dict and update_dict["interface_ids"] is not None:
        update_dict["interface_ids"] = [UUID(iid) for iid in update_dict["interface_ids"]]
    if "llm_config_id" in update_dict and update_dict["llm_config_id"] is not None:
        update_dict["llm_config_id"] = UUID(update_dict["llm_config_id"])
    
    for key, value in update_dict.items():
        setattr(assistant, key, value)
    
    await db.commit()
    await db.refresh(assistant)
    
    return AssistantConfigResponse(
        id=str(assistant.id),
        user_id=str(assistant.user_id),
        name=assistant.name,
        description=assistant.description,
        llm_config_id=str(assistant.llm_config_id) if assistant.llm_config_id else None,
        system_prompt=assistant.system_prompt,
        knowledge_base_ids=[str(kid) for kid in assistant.knowledge_base_ids] if assistant.knowledge_base_ids else [],
        datasource_ids=[str(did) for did in assistant.datasource_ids] if assistant.datasource_ids else [],
        interface_ids=[str(iid) for iid in assistant.interface_ids] if assistant.interface_ids else [],
        enable_knowledge_base=assistant.enable_knowledge_base,
        enable_datasource=assistant.enable_datasource,
        enable_interface=assistant.enable_interface,
        auto_route=assistant.auto_route,
        max_history=assistant.max_history,
        config=assistant.config,
        is_default=assistant.is_default,
        is_active=assistant.is_active
    )


@router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除助手配置"""
    result = await db.execute(
        select(AssistantConfig).where(
            AssistantConfig.id == uuid_lib.UUID(assistant_id),
            AssistantConfig.user_id == uuid_lib.UUID(current_user["user_id"])
        )
    )
    assistant = result.scalar_one_or_none()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="助手配置不存在"
        )
    
    await db.delete(assistant)
    await db.commit()
    
    return {"message": "删除成功"}
