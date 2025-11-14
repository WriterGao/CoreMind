"""
CoreMind AI助手平台 - 主入口文件
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 在导入 ChromaDB 之前禁用遥测，避免错误
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import engine, init_db
from app.api import api_router

# 设置日志
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 CoreMind正在启动...")
    
    # 初始化数据库
    await init_db()
    logger.info("✅ 数据库初始化完成")
    
    # 预加载嵌入模型（避免首次使用时延迟）
    logger.info("📦 正在预加载嵌入模型...")
    try:
        import asyncio
        from app.services.knowledge.embeddings import EmbeddingService
        
        # 在后台线程中加载模型（避免阻塞）
        def preload_model():
            try:
                embedding_service = EmbeddingService()
                # 测试模型是否可用
                test_text = "测试"
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(embedding_service.embed_text(test_text))
                loop.close()
                logger.info(f"✅ 嵌入模型预加载成功（向量维度: {len(result)}）")
            except Exception as e:
                logger.warning(f"⚠️ 嵌入模型预加载失败，将在首次使用时加载: {str(e)}")
        
        # 在后台线程中执行
        import threading
        thread = threading.Thread(target=preload_model, daemon=True)
        thread.start()
        # 等待一小段时间让模型开始下载
        await asyncio.sleep(0.1)
        
    except Exception as e:
        logger.warning(f"⚠️ 预加载嵌入模型时出错，将在首次使用时加载: {str(e)}")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 CoreMind正在关闭...")
    await engine.dispose()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="可自定义数据源、接口、知识库的AI助手平台",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

