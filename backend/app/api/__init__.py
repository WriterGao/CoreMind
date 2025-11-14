"""
API路由
"""
from fastapi import APIRouter

from app.api import auth, datasource, knowledge, interface, chat, llm_config, assistant, chat_v2

api_router = APIRouter()

# 注册路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(datasource.router, prefix="/datasources", tags=["数据源"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(interface.router, prefix="/interfaces", tags=["接口"])
api_router.include_router(llm_config.router, prefix="/llm-configs", tags=["LLM配置"])
api_router.include_router(assistant.router, prefix="/assistants", tags=["助手配置"])
api_router.include_router(chat.router, prefix="/chat", tags=["对话"])
api_router.include_router(chat_v2.router, prefix="/chat-v2", tags=["对话V2(智能路由)"])

