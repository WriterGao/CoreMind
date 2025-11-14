"""
应用配置管理
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "CoreMind"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://coremind:password@localhost:5432/coremind",
        description="数据库连接URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    
    # JWT配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT密钥"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: str = Field(
        default="XeyI6G5m1-Q0Ds9NVgWyVlWXIIJIpvq8XxexxSNo5Ls=",
        description="用于敏感信息加密的Fernet密钥"
    )
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Azure OpenAI配置
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
    
    # 通义千问嵌入模型配置
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v2"
    
    # 智谱AI嵌入模型配置
    ZHIPU_API_KEY: Optional[str] = None
    ZHIPU_EMBEDDING_MODEL: str = "embedding-2"
    
    # 本地嵌入模型配置（默认使用，无需API密钥）
    # 使用中文优化模型 BAAI/bge-small-zh-v1.5 获得更好的中文支持
    # 其他可选模型：
    # - sentence-transformers/all-MiniLM-L6-v2（英文，轻量级）
    # - moka-ai/m3e-base（中文，M3E模型）
    # - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2（多语言）
    LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    
    # Ollama配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # ChromaDB配置
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 100  # MB
    UPLOAD_DIR: str = "./data/uploads"
    
    # 数据源配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    
    # 爬虫配置
    USER_AGENT: str = "CoreMind Bot 1.0"
    CRAWL_DELAY: int = 1  # 秒
    MAX_DEPTH: int = 3
    
    # 监控配置
    ENABLE_METRICS: bool = True
    SENTRY_DSN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

