#!/usr/bin/env python3
"""
创建爬虫任务表的迁移脚本
"""
import asyncio
from sqlalchemy import text
from app.database.async_connection import get_engine
from app.database.db.base import Base
from app.database.db.crawl_task import CrawlTask


async def create_crawl_task_table():
    """创建爬虫任务表"""
    engine = get_engine()
    
    # 创建表
    async with engine.begin() as conn:
        # 检查表是否存在
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='crawl_tasks'")
        )
        if not result.fetchone():
            # 创建表
            await conn.run_sync(Base.metadata.create_all)
            print("✅ 爬虫任务表创建成功")
        else:
            print("ℹ️  爬虫任务表已存在")


if __name__ == "__main__":
    asyncio.run(create_crawl_task_table())