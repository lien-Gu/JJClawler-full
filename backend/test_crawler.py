#!/usr/bin/env python3
"""
测试修改后的爬虫功能
"""

import asyncio
import logging
from app.modules.crawler.jiazi_crawler import JiaziCrawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_jiazi_crawler():
    """测试夹子榜爬虫"""
    logger.info("开始测试夹子榜爬虫...")
    
    crawler = JiaziCrawler()
    
    try:
        # 只测试前3本书，避免请求过多
        books, snapshots = await crawler.crawl()
        
        if books and snapshots:
            logger.info(f"获取到 {len(books)} 本书籍和 {len(snapshots)} 个快照")
            
            # 查看前3个快照的数据
            for i, snapshot in enumerate(snapshots[:3]):
                logger.info(f"书籍 {i+1}: {snapshot.book_id}")
                logger.info(f"  点击量: {snapshot.total_clicks}")
                logger.info(f"  收藏量: {snapshot.total_favorites}")
                logger.info(f"  评论数: {snapshot.comment_count}")
                logger.info(f"  章节数: {snapshot.chapter_count}")
                logger.info(f"  字数: {snapshot.word_count}")
        else:
            logger.warning("未获取到数据")
            
    except Exception as e:
        logger.error(f"测试失败: {e}")
    finally:
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(test_jiazi_crawler())