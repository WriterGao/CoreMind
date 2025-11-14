"""
对话API
"""
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeBase
from app.services.assistant import ChatEngine
from app.services.knowledge import VectorStore

router = APIRouter()


class ConversationCreate(BaseModel):
    """对话创建模型"""
    title: str = "新对话"
    knowledge_base_id: str = None
    system_prompt: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000


class ConversationResponse(BaseModel):
    """对话响应模型"""
    id: str
    title: str
    knowledge_base_id: str = None
    model: str
    message_count: int


class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    stream: bool = False
    use_knowledge_base: bool = True


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    role: str
    content: str


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conv_data: ConversationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建对话"""
    
    # 如果指定了知识库，验证其存在性
    if conv_data.knowledge_base_id:
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == uuid.UUID(conv_data.knowledge_base_id),
                KnowledgeBase.user_id == uuid.UUID(current_user["user_id"])
            )
        )
        kb = result.scalar_one_or_none()
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识库不存在"
            )
    
    # 创建对话
    conversation = Conversation(
        user_id=uuid.UUID(current_user["user_id"]),
        knowledge_base_id=uuid.UUID(conv_data.knowledge_base_id) if conv_data.knowledge_base_id else None,
        title=conv_data.title,
        system_prompt=conv_data.system_prompt,
        model=conv_data.model,
        temperature=conv_data.temperature,
        max_tokens=conv_data.max_tokens,
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取对话列表"""
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        ).order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    
    # 转换为响应模型，确保 UUID 转换为字符串
    conv_list = []
    for conv in conversations:
        conv_list.append(ConversationResponse(
            id=str(conv.id),
            title=conv.title,
            knowledge_base_id=str(conv.knowledge_base_id) if conv.knowledge_base_id else None,
            model=conv.model,
            message_count=conv.message_count or 0
        ))
    
    return conv_list


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取对话详情"""
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 转换为响应模型，确保 UUID 转换为字符串
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        knowledge_base_id=str(conversation.knowledge_base_id) if conversation.knowledge_base_id else None,
        model=conversation.model,
        message_count=conversation.message_count or 0
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除对话"""
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    await db.delete(conversation)
    await db.commit()
    
    return {"message": "对话已删除"}


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取对话消息"""
    
    # 验证对话存在
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取消息
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == uuid.UUID(conversation_id)
        ).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return messages


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    chat_data: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """发送消息"""
    
    # 获取对话
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建对话引擎
    chat_engine = ChatEngine(
        model=conversation.model,
        temperature=conversation.temperature,
        max_tokens=conversation.max_tokens,
        system_prompt=conversation.system_prompt,
    )
    
    # 加载对话历史
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == uuid.UUID(conversation_id)
        ).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    for msg in messages:
        chat_engine.memory.add_message(msg.role, msg.content)
    
    # 设置知识库
    if conversation.knowledge_base_id and chat_data.use_knowledge_base:
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == conversation.knowledge_base_id
            )
        )
        kb = result.scalar_one_or_none()
        
        if kb:
            vectorstore = VectorStore(kb.collection_name, kb.embedding_model)
            chat_engine.set_knowledge_base(vectorstore)
    
    # 保存用户消息
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_data.message,
    )
    db.add(user_message)
    
    # 如果是流式响应
    if chat_data.stream:
        async def generate():
            full_response = ""
            async for chunk in chat_engine.stream_chat(
                chat_data.message,
                use_knowledge_base=chat_data.use_knowledge_base
            ):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # 保存助手消息
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_message)
            
            # 更新统计
            conversation.message_count += 2
            await db.commit()
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # 非流式响应
    else:
        reply = await chat_engine.chat(
            chat_data.message,
            use_knowledge_base=chat_data.use_knowledge_base
        )
        
        # 保存助手消息
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply,
        )
        db.add(assistant_message)
        
        # 更新统计
        conversation.message_count += 2
        await db.commit()
        
        return {
            "role": "assistant",
            "content": reply
        }

