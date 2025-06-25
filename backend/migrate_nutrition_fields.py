#!/usr/bin/env python3
"""
数据库迁移脚本：添加营养液和VIP章节字段

在book_snapshots表中添加：
- vip_chapter_count: VIP章节数
- nutrition_count: 营养液数量
"""

import sqlite3
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_path():
    """获取数据库路径"""
    try:
        from app.config import get_settings
        settings = get_settings()
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        return db_path
    except Exception:
        # 如果无法导入配置，使用默认路径
        return './data/jjcrawler.db'


def check_columns_exist(cursor, table_name, column_names):
    """检查列是否已存在"""
    cursor.execute(f'PRAGMA table_info({table_name})')
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    missing_columns = []
    for col_name in column_names:
        if col_name not in existing_columns:
            missing_columns.append(col_name)
    
    return missing_columns, existing_columns


def migrate_database():
    """执行数据库迁移"""
    db_path = get_database_path()
    
    if not Path(db_path).exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    logger.info(f"开始迁移数据库: {db_path}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查需要添加的列
        columns_to_add = ['vip_chapter_count', 'nutrition_count']
        missing_columns, existing_columns = check_columns_exist(cursor, 'book_snapshots', columns_to_add)
        
        logger.info(f"当前book_snapshots表的列: {existing_columns}")
        logger.info(f"需要添加的列: {missing_columns}")
        
        if not missing_columns:
            logger.info("所有必要的列都已存在，无需迁移")
            conn.close()
            return True
        
        # 添加缺失的列
        for column_name in missing_columns:
            if column_name == 'vip_chapter_count':
                sql = "ALTER TABLE book_snapshots ADD COLUMN vip_chapter_count INTEGER DEFAULT NULL"
                description = "VIP章节数"
            elif column_name == 'nutrition_count':
                sql = "ALTER TABLE book_snapshots ADD COLUMN nutrition_count INTEGER DEFAULT NULL"
                description = "营养液数量"
            else:
                continue
            
            logger.info(f"添加列: {column_name} ({description})")
            cursor.execute(sql)
        
        # 提交更改
        conn.commit()
        
        # 验证迁移结果
        missing_columns_after, existing_columns_after = check_columns_exist(cursor, 'book_snapshots', columns_to_add)
        
        if not missing_columns_after:
            logger.info("✅ 数据库迁移成功完成")
            logger.info(f"最终book_snapshots表的列: {existing_columns_after}")
        else:
            logger.error(f"❌ 迁移后仍有缺失列: {missing_columns_after}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def main():
    """主函数"""
    logger.info("开始执行book_snapshots表字段迁移...")
    
    success = migrate_database()
    
    if success:
        logger.info("🎉 迁移完成！现在book_snapshots表包含所有必要字段")
    else:
        logger.error("💥 迁移失败，请检查错误信息")
        exit(1)


if __name__ == "__main__":
    main()