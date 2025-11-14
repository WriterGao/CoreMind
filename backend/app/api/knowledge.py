"""
知识库管理API
"""
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.knowledge import KnowledgeBase, Document, DocumentChunk
from app.models.assistant_config import AssistantConfig
from app.services.knowledge import VectorStore, TextSplitterService
from app.utils.file_parser import FileParser

router = APIRouter()


class KnowledgeBaseCreate(BaseModel):
    """知识库创建模型"""
    name: str
    description: str = ""
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 1000
    chunk_overlap: int = 200


class KnowledgeBaseResponse(BaseModel):
    """知识库响应模型"""
    id: str
    name: str
    description: str
    embedding_model: str
    total_documents: int
    total_chunks: int
    is_active: bool


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    """搜索结果"""
    content: str
    metadata: dict
    distance: float


@router.post("", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建知识库"""
    
    # 生成集合名称
    collection_name = f"kb_{uuid.uuid4().hex[:16]}"
    
    # 创建知识库
    kb = KnowledgeBase(
        user_id=uuid.UUID(current_user["user_id"]),
        name=kb_data.name,
        description=kb_data.description,
        embedding_model=kb_data.embedding_model,
        collection_name=collection_name,
        chunk_size=kb_data.chunk_size,
        chunk_overlap=kb_data.chunk_overlap,
    )
    
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    
    # 初始化向量存储
    vectorstore = VectorStore(collection_name, kb_data.embedding_model)
    
    return KnowledgeBaseResponse(
        id=str(kb.id),
        name=kb.name,
        description=kb.description or "",
        embedding_model=kb.embedding_model,
        total_documents=kb.total_documents,
        total_chunks=kb.total_chunks,
        is_active=kb.is_active,
    )


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取知识库列表"""
    
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    knowledge_bases = result.scalars().all()
    
    return [
        KnowledgeBaseResponse(
            id=str(kb.id),
            name=kb.name,
            description=kb.description or "",
            embedding_model=kb.embedding_model,
            total_documents=kb.total_documents,
            total_chunks=kb.total_chunks,
            is_active=kb.is_active,
        )
        for kb in knowledge_bases
    ]


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取知识库详情"""
    
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == uuid.UUID(kb_id),
            KnowledgeBase.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    return KnowledgeBaseResponse(
        id=str(kb.id),
        name=kb.name,
        description=kb.description or "",
        embedding_model=kb.embedding_model,
        total_documents=kb.total_documents,
        total_chunks=kb.total_chunks,
        is_active=kb.is_active,
    )


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除知识库"""
    
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == uuid.UUID(kb_id),
            KnowledgeBase.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 检查是否有助手正在引用该知识库
    ref_result = await db.execute(
        select(AssistantConfig).where(
            AssistantConfig.knowledge_base_ids.any(kb.id)
        )
    )
    referencing_assistants = ref_result.scalars().all()
    if referencing_assistants:
        assistant_names = [assistant.name for assistant in referencing_assistants]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"知识库仍被以下助手引用：{', '.join(assistant_names)}。请先在助手配置中移除该知识库。"
        )
    
    # 删除向量存储
    vectorstore = VectorStore(kb.collection_name, kb.embedding_model)
    await vectorstore.delete_collection()
    
    # 删除数据库记录
    await db.delete(kb)
    await db.commit()
    
    return {"message": "知识库已删除"}


@router.post("/{kb_id}/upload")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """上传文档到知识库"""
    
    # 获取知识库
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == uuid.UUID(kb_id),
            KnowledgeBase.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    try:
        # 保存文件
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 解析文件
        parser = FileParser()
        text_content = await parser.parse_file(file_path)
        
        if not text_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法解析文件内容"
            )
        
        # 创建文档记录
        doc = Document(
            knowledge_base_id=kb.id,
            title=file.filename,
            content=text_content,
            file_path=file_path,
            file_type=os.path.splitext(file.filename)[1],
            file_size=len(content),
        )
        
        db.add(doc)
        await db.flush()
        
        # 文本切分
        splitter = TextSplitterService(kb.chunk_size, kb.chunk_overlap)
        chunks = splitter.split_text(text_content)
        
        # 构建文档列表用于向量化
        documents = []
        for i, chunk_content in enumerate(chunks):
            documents.append({
                "content": chunk_content,
                "metadata": {
                    "document_id": str(doc.id),
                    "title": file.filename,
                    "chunk_index": i,
                }
            })
        
        # 添加到向量存储
        vectorstore = VectorStore(kb.collection_name, kb.embedding_model)
        vector_ids = await vectorstore.add_documents(documents)
        
        # 创建切片记录
        for i, vector_id in enumerate(vector_ids):
            chunk = DocumentChunk(
                document_id=doc.id,
                knowledge_base_id=kb.id,
                content=chunks[i],
                chunk_index=i,
                vector_id=vector_id,
            )
            db.add(chunk)
        
        # 更新统计
        doc.chunk_count = len(chunks)
        doc.is_processed = True
        kb.total_documents += 1
        kb.total_chunks += len(chunks)
        
        await db.commit()
        
        return {
            "message": "文档上传成功",
            "document_id": str(doc.id),
            "chunks": len(chunks)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文档失败: {str(e)}"
        )


@router.post("/{kb_id}/search", response_model=List[SearchResult])
async def search_knowledge_base(
    kb_id: str,
    search_data: SearchRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """搜索知识库"""
    
    # 获取知识库
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == uuid.UUID(kb_id),
            KnowledgeBase.user_id == uuid.UUID(current_user["user_id"])
        )
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 搜索
    vectorstore = VectorStore(kb.collection_name, kb.embedding_model)
    results = await vectorstore.search(search_data.query, search_data.top_k)
    
    return results

