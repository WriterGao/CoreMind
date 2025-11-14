"""
数据库初始化脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models import (
    user, datasource, knowledge, interface, conversation, llm_config, assistant_config
)
from loguru import logger


async def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        
        logger.success("✅ 数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise


async def drop_all_tables():
    """删除所有表（谨慎使用！）"""
    logger.warning("准备删除所有表...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.success("✅ 所有表已删除")
        
    except Exception as e:
        logger.error(f"❌ 删除表失败: {str(e)}")
        raise


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库初始化工具")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="删除所有表后重新创建（警告：会丢失所有数据！）"
    )
    
    args = parser.parse_args()
    
    if args.drop:
        confirm = input("⚠️  警告：此操作将删除所有数据！确认继续？(yes/no): ")
        if confirm.lower() == "yes":
            await drop_all_tables()
            await init_database()
        else:
            logger.info("操作已取消")
    else:
        await init_database()


if __name__ == "__main__":
    asyncio.run(main())

