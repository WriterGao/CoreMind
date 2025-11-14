"""
数据库数据源
"""
from typing import List, Dict, Any
import asyncio
from loguru import logger

from app.services.datasource.base import BaseDataSource


class DatabaseDataSource(BaseDataSource):
    """数据库数据源"""
    
    async def connect(self) -> bool:
        """连接到数据库"""
        try:
            db_type = self.config.get("db_type")
            
            if db_type == "mysql":
                return await self._connect_mysql()
            elif db_type == "postgresql":
                return await self._connect_postgresql()
            elif db_type == "mongodb":
                return await self._connect_mongodb()
            else:
                raise ValueError(f"不支持的数据库类型: {db_type}")
                
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False
    
    async def _connect_mysql(self) -> bool:
        """连接MySQL"""
        try:
            import aiomysql
            
            self.connection = await aiomysql.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
                db=self.config.get("database"),
            )
            
            self.connected = True
            logger.info("成功连接到MySQL数据库")
            return True
            
        except Exception as e:
            logger.error(f"连接MySQL失败: {str(e)}")
            return False
    
    async def _connect_postgresql(self) -> bool:
        """连接PostgreSQL"""
        try:
            import asyncpg
            
            self.connection = await asyncpg.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                user=self.config.get("user", "postgres"),
                password=self.config.get("password", ""),
                database=self.config.get("database"),
            )
            
            self.connected = True
            logger.info("成功连接到PostgreSQL数据库")
            return True
            
        except Exception as e:
            logger.error(f"连接PostgreSQL失败: {str(e)}")
            return False
    
    async def _connect_mongodb(self) -> bool:
        """连接MongoDB"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            connection_string = self.config.get(
                "connection_string",
                f"mongodb://{self.config.get('host', 'localhost')}:{self.config.get('port', 27017)}"
            )
            
            self.client = AsyncIOMotorClient(connection_string)
            self.connection = self.client[self.config.get("database")]
            
            # 测试连接
            await self.client.server_info()
            
            self.connected = True
            logger.info("成功连接到MongoDB数据库")
            return True
            
        except Exception as e:
            logger.error(f"连接MongoDB失败: {str(e)}")
            return False
    
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """获取数据库数据"""
        if not self.connected:
            await self.connect()
        
        try:
            db_type = self.config.get("db_type")
            
            if db_type == "mysql":
                return await self._fetch_mysql_data()
            elif db_type == "postgresql":
                return await self._fetch_postgresql_data()
            elif db_type == "mongodb":
                return await self._fetch_mongodb_data()
            else:
                return []
                
        except Exception as e:
            logger.error(f"获取数据库数据失败: {str(e)}")
            return []
    
    async def _fetch_mysql_data(self) -> List[Dict[str, Any]]:
        """获取MySQL数据"""
        results = []
        query = self.config.get("query")
        title_column = self.config.get("title_column")
        content_columns = self.config.get("content_columns", [])
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # 构建内容
                content_parts = []
                for col in content_columns:
                    if col in row_dict:
                        content_parts.append(str(row_dict[col]))
                
                content = " ".join(content_parts)
                
                results.append({
                    "title": str(row_dict.get(title_column, "未命名")),
                    "content": self.preprocess_content(content),
                    "metadata": row_dict
                })
        
        logger.info(f"从MySQL获取了 {len(results)} 条数据")
        return results
    
    async def _fetch_postgresql_data(self) -> List[Dict[str, Any]]:
        """获取PostgreSQL数据"""
        results = []
        query = self.config.get("query")
        title_column = self.config.get("title_column")
        content_columns = self.config.get("content_columns", [])
        
        rows = await self.connection.fetch(query)
        
        for row in rows:
            row_dict = dict(row)
            
            # 构建内容
            content_parts = []
            for col in content_columns:
                if col in row_dict:
                    content_parts.append(str(row_dict[col]))
            
            content = " ".join(content_parts)
            
            results.append({
                "title": str(row_dict.get(title_column, "未命名")),
                "content": self.preprocess_content(content),
                "metadata": row_dict
            })
        
        logger.info(f"从PostgreSQL获取了 {len(results)} 条数据")
        return results
    
    async def _fetch_mongodb_data(self) -> List[Dict[str, Any]]:
        """获取MongoDB数据"""
        results = []
        collection_name = self.config.get("collection")
        query = self.config.get("query", {})
        title_field = self.config.get("title_field")
        content_fields = self.config.get("content_fields", [])
        
        collection = self.connection[collection_name]
        cursor = collection.find(query)
        
        async for doc in cursor:
            # 构建内容
            content_parts = []
            for field in content_fields:
                if field in doc:
                    content_parts.append(str(doc[field]))
            
            content = " ".join(content_parts)
            
            # 移除_id（不可序列化）
            doc.pop("_id", None)
            
            results.append({
                "title": str(doc.get(title_field, "未命名")),
                "content": self.preprocess_content(content),
                "metadata": doc
            })
        
        logger.info(f"从MongoDB获取了 {len(results)} 条数据")
        return results
    
    async def disconnect(self) -> bool:
        """断开数据库连接"""
        try:
            db_type = self.config.get("db_type")
            
            if db_type in ["mysql", "postgresql"]:
                if hasattr(self, "connection"):
                    self.connection.close()
                    if db_type == "mysql":
                        await self.connection.wait_closed()
            elif db_type == "mongodb":
                if hasattr(self, "client"):
                    self.client.close()
            
            self.connected = False
            logger.info("数据库连接已断开")
            return True
            
        except Exception as e:
            logger.error(f"断开数据库连接失败: {str(e)}")
            return False

