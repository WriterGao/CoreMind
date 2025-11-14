"""
LLM配置管理API
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.llm_config import LLMConfig, LLMProvider
from app.utils.crypto import encrypt_text, decrypt_text

router = APIRouter()


class LLMConfigCreate(BaseModel):
    """创建LLM配置"""
    name: str
    provider: str
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    config: Optional[dict] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    is_default: Optional[bool] = False
    
    class Config:
        protected_namespaces = ()


class LLMConfigUpdate(BaseModel):
    """更新LLM配置"""
    name: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    config: Optional[dict] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    
    class Config:
        protected_namespaces = ()


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    id: str
    user_id: str
    name: str
    provider: str
    model_name: str
    api_base: Optional[str] = None
    config: Optional[dict] = None
    temperature: float
    max_tokens: int
    is_default: bool
    is_active: bool
    has_api_key: bool  # 不返回实际密钥，只返回是否配置
    
    class Config:
        from_attributes = True
        protected_namespaces = ()


@router.post("", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    config_data: LLMConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建LLM配置"""
    # 验证provider
    try:
        provider_enum = LLMProvider(config_data.provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的提供商: {config_data.provider}"
        )
    
    # 如果设置为默认，先取消其他默认配置
    if config_data.is_default:
        await db.execute(
            update(LLMConfig)
            .where(LLMConfig.user_id == uuid.UUID(current_user["user_id"]))
            .where(LLMConfig.is_default == True)
            .values(is_default=False)
        )
    
    # 加密API密钥
    encrypted_key = encrypt_text(config_data.api_key) if config_data.api_key else None
    
    # 创建配置
    llm_config = LLMConfig(
        user_id=uuid.UUID(current_user["user_id"]),
        name=config_data.name,
        provider=provider_enum,
        model_name=config_data.model_name,
        api_key=encrypted_key,
        api_base=config_data.api_base,
        config=config_data.config,
        temperature=config_data.temperature,
        max_tokens=config_data.max_tokens,
        is_default=config_data.is_default
    )
    
    db.add(llm_config)
    await db.commit()
    await db.refresh(llm_config)
    
    return LLMConfigResponse(
        id=str(llm_config.id),
        user_id=str(llm_config.user_id),
        name=llm_config.name,
        provider=llm_config.provider.value,
        model_name=llm_config.model_name,
        api_base=llm_config.api_base,
        config=llm_config.config,
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
        is_default=llm_config.is_default,
        is_active=llm_config.is_active,
        has_api_key=bool(llm_config.api_key)
    )


@router.get("", response_model=List[LLMConfigResponse])
async def get_llm_configs(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取当前用户的所有LLM配置"""
    result = await db.execute(
        select(LLMConfig)
        .where(LLMConfig.user_id == uuid.UUID(current_user["user_id"]))
        .order_by(LLMConfig.is_default.desc(), LLMConfig.created_at.desc())
    )
    configs = result.scalars().all()
    
    return [
        LLMConfigResponse(
            id=str(config.id),
            user_id=str(config.user_id),
            name=config.name,
            provider=config.provider.value,
            model_name=config.model_name,
            api_base=config.api_base,
            config=config.config,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            is_default=config.is_default,
            is_active=config.is_active,
            has_api_key=bool(config.api_key)
        )
        for config in configs
    ]


@router.get("/{config_id}", response_model=LLMConfigResponse)
async def get_llm_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取指定LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(
            LLMConfig.id == uuid.UUID(config_id),
            LLMConfig.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    return LLMConfigResponse(
        id=str(config.id),
        user_id=str(config.user_id),
        name=config.name,
        provider=config.provider.value,
        model_name=config.model_name,
        api_base=config.api_base,
        config=config.config,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_default=config.is_default,
        is_active=config.is_active,
        has_api_key=bool(config.api_key)
    )


@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: str,
    update_data: LLMConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(
            LLMConfig.id == uuid.UUID(config_id),
            LLMConfig.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 如果设置为默认，先取消其他默认配置
    if update_data.is_default:
        await db.execute(
            update(LLMConfig)
            .where(LLMConfig.user_id == uuid.UUID(current_user["user_id"]))
            .where(LLMConfig.id != uuid.UUID(config_id))
            .where(LLMConfig.is_default == True)
            .values(is_default=False)
        )
    
    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    
    # 如果更新API密钥，需要加密
    if "api_key" in update_dict and update_dict["api_key"]:
        update_dict["api_key"] = encrypt_text(update_dict["api_key"])
    
    for key, value in update_dict.items():
        setattr(config, key, value)
    
    await db.commit()
    await db.refresh(config)
    
    return LLMConfigResponse(
        id=str(config.id),
        user_id=str(config.user_id),
        name=config.name,
        provider=config.provider.value,
        model_name=config.model_name,
        api_base=config.api_base,
        config=config.config,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_default=config.is_default,
        is_active=config.is_active,
        has_api_key=bool(config.api_key)
    )


@router.delete("/{config_id}")
async def delete_llm_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(
            LLMConfig.id == uuid.UUID(config_id),
            LLMConfig.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    await db.delete(config)
    await db.commit()
    
    return {"message": "删除成功"}


@router.get("/providers/list")
async def get_providers():
    """获取支持的LLM提供商列表"""
    providers = [
        {
            "value": "openai",
            "label": "OpenAI (GPT-3.5/4)",
            "models": [
                "gpt-4o",
                "gpt-4o-mini", 
                "gpt-4-turbo",
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-4-32k",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "o1-preview",
                "o1-mini"
            ],
            "default_base": "https://api.openai.com/v1"
        },
        {
            "value": "azure_openai",
            "label": "Azure OpenAI",
            "models": ["gpt-35-turbo", "gpt-4", "gpt-4-32k"],
            "default_base": ""
        },
        {
            "value": "deepseek",
            "label": "DeepSeek",
            "models": [
                "deepseek-chat",
                "deepseek-coder",
                "deepseek-reasoner"
            ],
            "default_base": "https://api.deepseek.com/v1"
        },
        {
            "value": "alibaba_qwen",
            "label": "阿里云通义千问",
            "models": [
                "qwen-max",
                "qwen-max-longcontext",
                "qwen-plus",
                "qwen-turbo",
                "qwen-vl-plus",
                "qwen-vl-max"
            ],
            "default_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
        {
            "value": "zhipu_ai",
            "label": "智谱AI (ChatGLM)",
            "models": [
                "glm-4-plus",
                "glm-4-0520", 
                "glm-4",
                "glm-4-air",
                "glm-4-airx",
                "glm-4-flash",
                "glm-3-turbo"
            ],
            "default_base": "https://open.bigmodel.cn/api/paas/v4"
        },
        {
            "value": "baidu_wenxin",
            "label": "百度文心一言",
            "models": ["ernie-bot", "ernie-bot-turbo", "ernie-bot-4"],
            "default_base": "https://aip.baidubce.com"
        },
        {
            "value": "moonshot",
            "label": "月之暗面 (Kimi)",
            "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
            "default_base": "https://api.moonshot.cn/v1"
        },
        {
            "value": "anthropic",
            "label": "Anthropic (Claude)",
            "models": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "default_base": "https://api.anthropic.com"
        },
        {
            "value": "google_gemini",
            "label": "Google Gemini",
            "models": [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.5-flash-8b",
                "gemini-pro",
                "gemini-pro-vision"
            ],
            "default_base": "https://generativelanguage.googleapis.com/v1"
        },
        {
            "value": "ollama",
            "label": "Ollama (本地部署)",
            "models": [
                "llama3.3",
                "llama3.2",
                "llama3.1",
                "llama2",
                "mistral",
                "mixtral",
                "qwen2.5",
                "qwen",
                "codellama",
                "deepseek-coder-v2",
                "phi3",
                "gemma2"
            ],
            "default_base": "http://localhost:11434"
        },
        {
            "value": "custom",
            "label": "自定义",
            "models": [],
            "default_base": ""
        }
    ]
    
    return {"providers": providers}
