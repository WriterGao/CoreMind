"""
数据源管理服务
"""
from app.services.datasource.base import BaseDataSource
from app.services.datasource.local_file import LocalFileDataSource
from app.services.datasource.database import DatabaseDataSource
from app.services.datasource.api import APIDataSource
from app.services.datasource.crawler import WebCrawlerDataSource

__all__ = [
    "BaseDataSource",
    "LocalFileDataSource",
    "DatabaseDataSource",
    "APIDataSource",
    "WebCrawlerDataSource",
]

