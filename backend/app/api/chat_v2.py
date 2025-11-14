"""
对话API V2 (支持助手配置和智能路由)
"""
from typing import List, Any, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
import uuid
import json
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Conversation, Message, AssistantConfig, LLMConfig, KnowledgeBase
from app.services.llm_service import LLMService
from app.services.knowledge import VectorStore
from app.core.logging import setup_logging

logger = setup_logging()
router = APIRouter()


class ConversationCreateV2(BaseModel):
    """对话创建模型 V2"""
    title: str = "新对话"
    assistant_id: str
    system_prompt: Optional[str] = None


class ConversationResponse(BaseModel):
    """对话响应模型"""
    id: str
    title: str
    assistant_id: Optional[str] = None
    assistant_name: Optional[str] = None  # 助手名称
    knowledge_base_id: Optional[str] = None  # 知识库ID（兼容旧数据）
    system_prompt: Optional[str] = None
    model: str
    temperature: float
    max_tokens: int
    message_count: int
    created_at: str
    
    class Config:
        from_attributes = True


class ChatRequestV2(BaseModel):
    """对话请求 V2"""
    message: str
    stream: bool = False


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: str
    role: str
    content: str
    tokens: int
    created_at: str
    
    class Config:
        from_attributes = True


# ========== 对话管理端点 ==========

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations_v2(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取对话列表 V2"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        ).order_by(Conversation.created_at.desc())
    )
    conversations = result.scalars().all()
    
    conv_list = []
    for conv in conversations:
        # 获取消息数量
        count_result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conv.id
            )
        )
        message_count = count_result.scalar() or 0
        
        # 获取助手名称
        assistant_name = None
        if conv.assistant_id:
            assistant_result = await db.execute(
                select(AssistantConfig).where(
                    AssistantConfig.id == conv.assistant_id
                )
            )
            assistant = assistant_result.scalar_one_or_none()
            if assistant:
                assistant_name = assistant.name
        
        conv_list.append(ConversationResponse(
            id=str(conv.id),
            title=conv.title,
            assistant_id=str(conv.assistant_id) if conv.assistant_id else None,
            assistant_name=assistant_name,
            knowledge_base_id=str(conv.knowledge_base_id) if conv.knowledge_base_id else None,
            system_prompt=conv.system_prompt,
            model=conv.model,
            temperature=conv.temperature,
            max_tokens=conv.max_tokens,
            message_count=message_count,
            created_at=conv.created_at.isoformat()
        ))
    
    return conv_list


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation_v2(
    conv_data: ConversationCreateV2,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建对话 V2"""
    # 验证助手配置
    result = await db.execute(
        select(AssistantConfig).where(
            AssistantConfig.id == uuid.UUID(conv_data.assistant_id),
            AssistantConfig.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    assistant_config = result.scalar_one_or_none()
    if not assistant_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="助手配置不存在"
        )
    
    # 获取LLM配置
    llm_config = None
    if assistant_config.llm_config_id:
        result = await db.execute(
            select(LLMConfig).where(
                LLMConfig.id == assistant_config.llm_config_id,
                LLMConfig.user_id == uuid.UUID(current_user["user_id"])
            )
        )
        llm_config = result.scalar_one_or_none()
        if not llm_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM配置不存在或已删除"
            )

    # 创建对话
    conversation = Conversation(
        user_id=uuid.UUID(current_user["user_id"]),
        assistant_id=uuid.UUID(conv_data.assistant_id),
        title=conv_data.title,
        system_prompt=conv_data.system_prompt or assistant_config.system_prompt or "你是一个有帮助的AI助手。",
        model=llm_config.model_name if llm_config else "default-model",
        temperature=llm_config.temperature if llm_config else 0.7,
        max_tokens=llm_config.max_tokens if llm_config else 2000,
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        assistant_id=str(conversation.assistant_id) if conversation.assistant_id else None,
        assistant_name=assistant_config.name,
        knowledge_base_id=str(conversation.knowledge_base_id) if conversation.knowledge_base_id else None,
        system_prompt=conversation.system_prompt,
        model=conversation.model,
        temperature=conversation.temperature,
        max_tokens=conversation.max_tokens,
        message_count=0,
        created_at=conversation.created_at.isoformat()
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_v2(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取对话详情 V2"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    # 获取消息数量
    count_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id
        )
    )
    message_count = count_result.scalar() or 0
    
    # 获取助手名称
    assistant_name = None
    if conversation.assistant_id:
        assistant_result = await db.execute(
            select(AssistantConfig).where(
                AssistantConfig.id == conversation.assistant_id
            )
        )
        assistant = assistant_result.scalar_one_or_none()
        if assistant:
            assistant_name = assistant.name
    
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        assistant_id=str(conversation.assistant_id) if conversation.assistant_id else None,
        assistant_name=assistant_name,
        knowledge_base_id=str(conversation.knowledge_base_id) if conversation.knowledge_base_id else None,
        system_prompt=conversation.system_prompt,
        model=conversation.model,
        temperature=conversation.temperature,
        max_tokens=conversation.max_tokens,
        message_count=message_count,
        created_at=conversation.created_at.isoformat()
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_v2(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除对话 V2"""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    
    await db.delete(conversation)
    await db.commit()
    return {"message": "删除成功"}


# ========== 消息管理端点 ==========

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages_v2(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取对话消息 V2"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return [
        MessageResponse(
            id=str(msg.id),
            role=msg.role,
            content=msg.content,
            tokens=msg.tokens or 0,
            created_at=msg.created_at.isoformat()
        )
        for msg in messages
    ]


@router.post("/conversations/{conversation_id}/messages")
async def chat_with_assistant(
    conversation_id: str,
    chat_request: ChatRequestV2,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """与助手对话"""
    conv_uuid = uuid.UUID(conversation_id)
    user_uuid = uuid.UUID(current_user["user_id"])

    # 1. 获取对话和助手配置
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_uuid,
            Conversation.user_id == user_uuid
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")

    result = await db.execute(
        select(AssistantConfig).where(
            AssistantConfig.id == conversation.assistant_id,
            AssistantConfig.user_id == user_uuid
        )
    )
    assistant_config = result.scalar_one_or_none()
    if not assistant_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="助手配置不存在")

    # 2. 保存用户消息
    user_message = Message(
        conversation_id=conv_uuid,
        role="user",
        content=chat_request.message,
        tokens=len(chat_request.message)  # 简化计算
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    # 3. 获取LLM配置并调用LLM服务
    llm_config = None
    if assistant_config.llm_config_id:
        result = await db.execute(
            select(LLMConfig).where(
                LLMConfig.id == assistant_config.llm_config_id,
                LLMConfig.user_id == user_uuid,
                LLMConfig.is_active == True
            )
        )
        llm_config = result.scalar_one_or_none()
    
    if not llm_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="助手未配置LLM模型或LLM配置已禁用"
        )
    
    # 4. 获取历史消息（最近10条作为上下文）
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_uuid)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history_messages = history_result.scalars().all()
    history_messages.reverse()  # 按时间正序
    
    # 构建消息列表
    llm_messages = []
    for msg in history_messages:
        if msg.role in ["user", "assistant"]:
            llm_messages.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # 5. 知识库检索
    knowledge_hits: List[Dict[str, Any]] = []
    knowledge_context = ""
    if assistant_config.enable_knowledge_base and assistant_config.knowledge_base_ids:
        kb_ids = [
            kb_id if isinstance(kb_id, uuid.UUID) else uuid.UUID(str(kb_id))
            for kb_id in (assistant_config.knowledge_base_ids or [])
        ]
        if kb_ids:
            kb_result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.id.in_(kb_ids)
                )
            )
            knowledge_bases = kb_result.scalars().all()
            for kb in knowledge_bases:
                try:
                    vectorstore = VectorStore(kb.collection_name, kb.embedding_model)
                    search_results = await vectorstore.search(chat_request.message, top_k=3)
                    for item in search_results:
                        hit = {
                            "knowledge_base_id": str(kb.id),
                            "knowledge_base_name": kb.name,
                            "content": item.get("content", ""),
                            "score": float(item.get("distance", 0.0)) if item.get("distance") is not None else None,
                            "metadata": item.get("metadata", {})
                        }
                        knowledge_hits.append(hit)
                except Exception as e:
                    logger.error(f"知识库检索失败 ({kb.id}): {e}")
            if knowledge_hits:
                context_blocks = []
                for idx, hit in enumerate(knowledge_hits, start=1):
                    snippet = hit["content"]
                    kb_name = hit["knowledge_base_name"]
                    context_blocks.append(f"[来源 {idx} - {kb_name}]\n{snippet}")
                knowledge_context = "\n\n".join(context_blocks)

    # 6. 调用LLM服务生成回复
    try:
        llm_service = LLMService(llm_config)
        base_system_prompt = conversation.system_prompt or assistant_config.system_prompt or "你是一个有帮助的AI助手。"
        if knowledge_context:
            system_prompt = (
                f"{base_system_prompt}\n\n"
                f"以下是与用户问题相关的知识库内容，请优先基于这些资料回答：\n"
                f"{knowledge_context}\n\n"
                "若资料不足以回答，请明确说明。"
            )
        else:
            system_prompt = base_system_prompt
        response_content = await llm_service.chat(llm_messages, system_prompt)
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        # 如果LLM调用失败，返回错误提示
        response_content = f"抱歉，LLM调用失败：{str(e)}\n\n请检查：\n1. API密钥是否正确\n2. 网络连接是否正常\n3. LLM服务是否可用"

    # 7. 保存助手消息
    assistant_message = Message(
        conversation_id=conv_uuid,
        role="assistant",
        content=response_content,
        tokens=len(response_content),  # 简化计算
        msg_metadata={
            "knowledge_hits": knowledge_hits,
            "used_knowledge": bool(knowledge_hits)
        } if knowledge_hits else None
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)
    
    return {"role": "assistant", "content": response_content}
