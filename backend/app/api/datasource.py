"""
数据源管理API
"""
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.datasource import DataSource, DataSourceType
from app.services.datasource import (
    LocalFileDataSource,
    DatabaseDataSource,
    APIDataSource,
    WebCrawlerDataSource,
)

router = APIRouter()


class DataSourceCreate(BaseModel):
    """数据源创建模型"""
    name: str
    description: str = ""
    type: DataSourceType
    config: dict
    usage_doc: str = ""
    schema_info: dict = None
    examples: list = None
    sync_frequency: int = 0


class DataSourceResponse(BaseModel):
    """数据源响应模型"""
    id: str
    name: str
    description: str
    type: DataSourceType
    config: dict
    usage_doc: str = ""
    schema_info: dict = None
    examples: list = None
    is_active: bool
    sync_status: str
    total_documents: int


@router.post("", response_model=DataSourceResponse)
async def create_datasource(
    datasource_data: DataSourceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建数据源"""
    
    # 验证配置
    if not await _validate_datasource_config(datasource_data.type, datasource_data.config):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="数据源配置验证失败"
        )
    
    # 创建数据源
    datasource = DataSource(
        user_id=uuid.UUID(current_user["user_id"]),
        name=datasource_data.name,
        description=datasource_data.description,
        type=datasource_data.type,
        config=datasource_data.config,
        usage_doc=datasource_data.usage_doc,
        schema_info=datasource_data.schema_info,
        examples=datasource_data.examples,
        sync_frequency=datasource_data.sync_frequency,
    )
    
    db.add(datasource)
    await db.commit()
    await db.refresh(datasource)
    
    return datasource


@router.get("", response_model=List[DataSourceResponse])
async def list_datasources(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取数据源列表"""
    
    result = await db.execute(
        select(DataSource).where(DataSource.user_id == uuid.UUID(current_user["user_id"]))
    )
    datasources = result.scalars().all()
    
    return datasources


@router.get("/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource(
    datasource_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取数据源详情"""
    
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == uuid.UUID(datasource_id),
            DataSource.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据源不存在"
        )
    
    return datasource


@router.delete("/{datasource_id}")
async def delete_datasource(
    datasource_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除数据源"""
    
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == uuid.UUID(datasource_id),
            DataSource.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据源不存在"
        )
    
    await db.delete(datasource)
    await db.commit()
    
    return {"message": "数据源已删除"}


@router.post("/{datasource_id}/sync")
async def sync_datasource(
    datasource_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """同步数据源"""
    
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == uuid.UUID(datasource_id),
            DataSource.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据源不存在"
        )
    
    # 执行同步（这里应该使用异步任务队列）
    try:
        # 根据类型创建数据源实例
        ds_instance = _create_datasource_instance(datasource.type, datasource.config)
        
        # 获取数据
        documents = await ds_instance.fetch_data()
        
        # 更新状态
        datasource.sync_status = "success"
        datasource.total_documents = len(documents)
        
        await db.commit()
        
        return {
            "message": "数据源同步成功",
            "total_documents": len(documents)
        }
        
    except Exception as e:
        datasource.sync_status = "failed"
        datasource.sync_error = str(e)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据源同步失败: {str(e)}"
        )


async def _validate_datasource_config(ds_type: DataSourceType, config: dict) -> bool:
    """验证数据源配置"""
    try:
        ds_instance = _create_datasource_instance(ds_type, config)
        result = await ds_instance.validate_config()
        return result.get("valid", False)
    except:
        return False


def _create_datasource_instance(ds_type: DataSourceType, config: dict):
    """创建数据源实例"""
    if ds_type == DataSourceType.LOCAL_FILE:
        return LocalFileDataSource(config)
    elif ds_type == DataSourceType.DATABASE:
        return DatabaseDataSource(config)
    elif ds_type == DataSourceType.API:
        return APIDataSource(config)
    elif ds_type == DataSourceType.WEB_CRAWLER:
        return WebCrawlerDataSource(config)
    else:
        raise ValueError(f"不支持的数据源类型: {ds_type}")

