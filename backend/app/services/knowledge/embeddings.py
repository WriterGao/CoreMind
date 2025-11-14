"""
嵌入向量服务
"""
from typing import List, Optional
from loguru import logger
from urllib.parse import urlparse

from app.core.config import settings

# 兼容 huggingface_hub 新版本移除 cached_download 的情况
try:
    import huggingface_hub

    if not hasattr(huggingface_hub, "cached_download"):
        from huggingface_hub import hf_hub_download

        def cached_download(
            path_or_repo_id=None,
            filename=None,
            cache_dir=None,
            force_download=False,
            proxies=None,
            resume_download=False,  # 保留参数以兼容旧代码，但实际不使用
            user_agent=None,  # 保留老接口参数以兼容
            revision=None,
            token=None,
            local_files_only=False,
            legacy_cache_layout=False,
            subfolder=None,
            repo_type=None,
            repo_id=None,
            url=None,
            url_or_filename=None,
            **kwargs,
        ):
            target = (
                path_or_repo_id
                or repo_id
                or url_or_filename
                or url
            )

            if target is None:
                raise TypeError("cached_download() missing required argument 'path_or_repo_id'")

            def _download_with_hub(repo_id_value: str, file_name: str):
                # 构建参数，排除 legacy_cache_layout（新版本不再支持）
                # 注意：resume_download 在新版本中已弃用，下载会自动恢复
                download_kwargs = {
                    "repo_id": repo_id_value,
                    "filename": file_name,
                    "subfolder": subfolder,
                    "repo_type": repo_type,
                    "revision": revision,
                    "cache_dir": cache_dir,
                    "force_download": force_download,
                    "proxies": proxies,
                    "token": token,
                    "local_files_only": local_files_only,
                }
                # 移除 None 值
                download_kwargs = {k: v for k, v in download_kwargs.items() if v is not None}
                return hf_hub_download(**download_kwargs)

            # 旧接口可能传入完整URL
            if isinstance(target, str) and target.startswith(("http://", "https://")):
                parsed = urlparse(target)
                if "huggingface.co" in parsed.netloc:
                    path_parts = parsed.path.strip("/").split("/")
                    if "resolve" in path_parts:
                        idx = path_parts.index("resolve")
                        repo_id_value = "/".join(path_parts[:idx])
                        revision_value = revision or (path_parts[idx + 1] if len(path_parts) > idx + 1 else "main")
                        file_path = "/".join(path_parts[idx + 2:]) if len(path_parts) > idx + 2 else filename
                        return _download_with_hub(repo_id_value, file_path or filename or "")
                # 其他URL暂不支持，提示升级
                raise ValueError(
                    "当前环境不支持直接下载非 HuggingFace Hub 链接，请在本地手动下载后放入缓存目录。"
                )

            target_str = str(target)
            file_name = filename or kwargs.get("filename")
            if not file_name:
                raise ValueError("未提供需要下载的文件名 filename")

            return _download_with_hub(target_str, file_name)

        huggingface_hub.cached_download = cached_download  # type: ignore[attr-defined]

        # 同时兼容 huggingface_hub.file_download.cached_download
        try:
            from huggingface_hub import file_download as _hf_file_download

            _hf_file_download.cached_download = cached_download  # type: ignore[attr-defined]
        except Exception as sub_patch_err:
            logger.warning(
                "未能替换 huggingface_hub.file_download.cached_download: %s",
                sub_patch_err,
            )
except Exception as patch_err:
    logger.warning(f"未能注入huggingface_hub.cached_download: {patch_err}")


class EmbeddingService:
    """嵌入向量服务"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        初始化嵌入服务
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name or settings.OPENAI_EMBEDDING_MODEL
        self.embedding_function = None
        self._initialize_embedding_function()
    
    def _initialize_embedding_function(self):
        """初始化嵌入函数"""
        try:
            # 优先使用OpenAI
            if settings.OPENAI_API_KEY:
                from langchain_openai import OpenAIEmbeddings
                
                self.embedding_function = OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=settings.OPENAI_API_KEY
                )
                logger.info(f"使用OpenAI嵌入模型: {self.model_name}")
            
            # Azure OpenAI
            elif settings.AZURE_OPENAI_API_KEY:
                from langchain_openai import AzureOpenAIEmbeddings
                
                self.embedding_function = AzureOpenAIEmbeddings(
                    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    openai_api_key=settings.AZURE_OPENAI_API_KEY,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                )
                logger.info("使用Azure OpenAI嵌入模型")
            
            # 通义千问嵌入模型（阿里云）
            elif settings.DASHSCOPE_API_KEY:
                try:
                    from langchain_community.embeddings import DashScopeEmbeddings
                    
                    self.embedding_function = DashScopeEmbeddings(
                        model=settings.DASHSCOPE_EMBEDDING_MODEL,
                        dashscope_api_key=settings.DASHSCOPE_API_KEY
                    )
                    logger.info(f"使用通义千问嵌入模型: {settings.DASHSCOPE_EMBEDDING_MODEL}")
                except ImportError:
                    logger.warning("DashScopeEmbeddings未安装，请运行: pip install dashscope")
                    # 降级到本地模型
                    self._initialize_local_model()
            
            # 智谱AI嵌入模型
            elif settings.ZHIPU_API_KEY:
                try:
                    # 智谱AI嵌入API调用
                    import httpx
                    import json
                    
                    class ZhipuEmbeddings:
                        def __init__(self, api_key: str, model: str = "embedding-2"):
                            self.api_key = api_key
                            self.model = model
                            self.base_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
                        
                        def embed_query(self, text: str):
                            return self.embed_documents([text])[0]
                        
                        def embed_documents(self, texts: list):
                            headers = {
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            }
                            data = {
                                "model": self.model,
                                "input": texts
                            }
                            response = httpx.post(self.base_url, headers=headers, json=data, timeout=30)
                            response.raise_for_status()
                            result = response.json()
                            return [item["embedding"] for item in result["data"]]
                    
                    self.embedding_function = ZhipuEmbeddings(
                        api_key=settings.ZHIPU_API_KEY,
                        model=settings.ZHIPU_EMBEDDING_MODEL
                    )
                    logger.info(f"使用智谱AI嵌入模型: {settings.ZHIPU_EMBEDDING_MODEL}")
                except Exception as e:
                    logger.warning(f"初始化智谱AI嵌入模型失败: {str(e)}，降级到本地模型")
                    self._initialize_local_model()
            
            # 本地模型 (SentenceTransformer) - 默认选项，无需API密钥
            else:
                self._initialize_local_model()
        
        except Exception as e:
            logger.error(f"初始化嵌入函数失败: {str(e)}")
            raise
    
    def _initialize_local_model(self):
        """初始化本地嵌入模型（无需API密钥）"""
        from sentence_transformers import SentenceTransformer

        # 支持多种本地嵌入模型
        # 默认使用轻量级英文模型，也支持中文模型如 BGE、M3E 等
        local_default_model = settings.LOCAL_EMBEDDING_MODEL or "sentence-transformers/all-MiniLM-L6-v2"
        
        # 如果指定了 sentence-transformers 模型，直接使用
        # 否则根据模型名称判断是否使用中文模型
        if self.model_name and self.model_name.startswith("sentence-transformers/"):
            local_model = self.model_name
        elif self.model_name and any(keyword in self.model_name.lower() for keyword in ["bge", "m3e", "chinese", "multilingual"]):
            # 中文或多语言模型
            local_model = self.model_name
        else:
            # 使用默认模型
            local_model = local_default_model
            if self.model_name != local_default_model:
                logger.info(
                    f"使用本地嵌入模型 '{local_model}'（无需API密钥）。"
                    f"如需使用OpenAI/Azure/通义千问/智谱AI等云服务嵌入模型，请在配置中设置相应的API密钥。"
                    f"支持的本地模型包括：sentence-transformers/all-MiniLM-L6-v2（英文）、"
                    f"sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2（多语言）、"
                    f"BAAI/bge-small-zh-v1.5（中文）等"
                )
        self.model_name = local_model

        class SentenceTransformerWrapper:
            """兼容LangChain接口的SentenceTransformer封装"""

            def __init__(self, model_name: str):
                import shutil
                from pathlib import Path
                
                try:
                    self.model = SentenceTransformer(model_name)
                except Exception as e:
                    logger.error(f"加载模型 {model_name} 失败: {str(e)}")
                    
                    # 如果是因为缓存损坏导致的错误，清理缓存并重试
                    if "Unrecognized model" in str(e) or "config.json" in str(e):
                        logger.warning(f"检测到模型缓存可能损坏，尝试清理缓存...")
                        try:
                            # 获取缓存目录
                            cache_dir = Path.home() / ".cache" / "torch" / "sentence_transformers"
                            model_cache_dir = cache_dir / model_name.replace("/", "_")
                            
                            if model_cache_dir.exists():
                                logger.info(f"清理损坏的模型缓存: {model_cache_dir}")
                                shutil.rmtree(model_cache_dir, ignore_errors=True)
                            
                            # 重新加载模型（会自动重新下载）
                            logger.info(f"重新下载并加载模型: {model_name}")
                            self.model = SentenceTransformer(model_name)
                            logger.info(f"模型 {model_name} 重新加载成功")
                        except Exception as retry_error:
                            logger.error(f"清理缓存后重新加载失败: {str(retry_error)}")
                            # 如果还是失败，尝试使用默认模型
                            if model_name != local_default_model:
                                logger.warning(f"尝试使用默认模型 {local_default_model}")
                                try:
                                    # 清理默认模型的缓存
                                    default_cache_dir = cache_dir / local_default_model.replace("/", "_")
                                    if default_cache_dir.exists():
                                        shutil.rmtree(default_cache_dir, ignore_errors=True)
                                    self.model = SentenceTransformer(local_default_model)
                                except Exception:
                                    raise retry_error
                            else:
                                raise retry_error
                    else:
                        # 其他错误，尝试使用默认模型
                        if model_name != local_default_model:
                            logger.warning(f"尝试使用默认模型 {local_default_model}")
                            self.model = SentenceTransformer(local_default_model)
                        else:
                            raise

            def embed_query(self, text: str):
                vector = self.model.encode([text], convert_to_numpy=True)[0]
                return vector.tolist()

            def embed_documents(self, texts: List[str]):
                vectors = self.model.encode(texts, convert_to_numpy=True)
                return vectors.tolist()

        self.embedding_function = SentenceTransformerWrapper(local_model)
        logger.info(f"使用本地SentenceTransformer嵌入模型: {local_model}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        将文本转换为嵌入向量
        
        Args:
            text: 文本内容
            
        Returns:
            嵌入向量
        """
        try:
            # LangChain的embed_query是同步的，需要在异步环境中运行
            import asyncio
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embedding_function.embed_query,
                text
            )
            return embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.embedding_function.embed_documents,
                texts
            )
            return embeddings
        except Exception as e:
            logger.error(f"批量生成嵌入向量失败: {str(e)}")
            raise

