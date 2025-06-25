#!/usr/bin/env python3
"""
数据库迁移脚本：修改字段名称和结构

修改内容：
1. book_snapshots表：total_clicks -> novip_clicks, total_favorites -> favorites
2. book_snapshots表：移除vip_chapter_count字段
3. books表：添加vip_chapter_count字段
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


def backup_database(db_path):
    """备份数据库"""
    backup_path = db_path + '.backup_field_migration'
    import shutil
    shutil.copy2(db_path, backup_path)
    logger.info(f"数据库已备份到: {backup_path}")
    return backup_path


def migrate_database():
    """执行数据库迁移"""
    db_path = get_database_path()
    
    if not Path(db_path).exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    logger.info(f"开始迁移数据库: {db_path}")
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 开始事务
        cursor.execute("BEGIN TRANSACTION")
        
        logger.info("=== 第一步：修改books表，添加vip_chapter_count字段 ===")
        
        # 检查books表是否已有vip_chapter_count字段
        cursor.execute("PRAGMA table_info(books)")
        books_columns = [col[1] for col in cursor.fetchall()]
        
        if 'vip_chapter_count' not in books_columns:
            cursor.execute("ALTER TABLE books ADD COLUMN vip_chapter_count INTEGER DEFAULT NULL")
            logger.info("✅ books表添加vip_chapter_count字段成功")
        else:
            logger.info("ℹ️ books表已有vip_chapter_count字段")
        
        logger.info("=== 第二步：重构book_snapshots表 ===")
        
        # 获取当前book_snapshots表结构
        cursor.execute("PRAGMA table_info(book_snapshots)")
        current_columns = cursor.fetchall()
        logger.info(f"当前book_snapshots表结构: {[col[1] for col in current_columns]}")
        
        # 创建新的book_snapshots表
        logger.info("创建新的book_snapshots表...")
        cursor.execute("""
            CREATE TABLE book_snapshots_new (
                id INTEGER PRIMARY KEY,
                book_id VARCHAR NOT NULL,
                novip_clicks INTEGER DEFAULT NULL,
                favorites INTEGER DEFAULT NULL,
                comment_count INTEGER DEFAULT NULL,
                chapter_count INTEGER DEFAULT NULL,
                word_count INTEGER DEFAULT NULL,
                nutrition_count INTEGER DEFAULT NULL,
                snapshot_time DATETIME NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books (book_id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX idx_book_snapshot_time_new ON book_snapshots_new (book_id, snapshot_time)")
        
        # 迁移数据（字段重命名）
        logger.info("迁移数据并重命名字段...")
        cursor.execute("""
            INSERT INTO book_snapshots_new (
                id, book_id, novip_clicks, favorites, comment_count, 
                chapter_count, word_count, nutrition_count, snapshot_time
            )
            SELECT 
                id, book_id, 
                COALESCE(total_clicks, 0) as novip_clicks,
                COALESCE(total_favorites, 0) as favorites,
                comment_count, chapter_count, word_count, nutrition_count, snapshot_time
            FROM book_snapshots
        """)
        
        # 检查迁移的数据量
        cursor.execute("SELECT COUNT(*) FROM book_snapshots")
        old_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM book_snapshots_new")
        new_count = cursor.fetchone()[0]
        
        if old_count != new_count:
            raise Exception(f"数据迁移失败：原表 {old_count} 条记录，新表 {new_count} 条记录")
        
        logger.info(f"✅ 数据迁移成功：{new_count} 条记录")
        
        # 如果有vip_chapter_count数据，迁移到books表
        logger.info("=== 第三步：迁移VIP章节数到books表 ===")
        cursor.execute("""
            SELECT DISTINCT book_id, vip_chapter_count 
            FROM book_snapshots 
            WHERE vip_chapter_count IS NOT NULL AND vip_chapter_count > 0
        """)
        vip_data = cursor.fetchall()
        
        if vip_data:
            logger.info(f"发现 {len(vip_data)} 本书籍有VIP章节数据，迁移到books表...")
            for book_id, vip_count in vip_data:
                cursor.execute("""
                    UPDATE books 
                    SET vip_chapter_count = ? 
                    WHERE book_id = ? AND (vip_chapter_count IS NULL OR vip_chapter_count = 0)
                """, (vip_count, book_id))
            logger.info("✅ VIP章节数据迁移完成")
        else:
            logger.info("ℹ️ 没有VIP章节数据需要迁移")
        
        # 删除旧表，重命名新表
        logger.info("=== 第四步：替换表结构 ===")
        cursor.execute("DROP TABLE book_snapshots")
        cursor.execute("ALTER TABLE book_snapshots_new RENAME TO book_snapshots")
        
        # 提交事务
        cursor.execute("COMMIT")
        
        # 验证最终结果
        logger.info("=== 验证迁移结果 ===")
        cursor.execute("PRAGMA table_info(books)")
        books_final = [col[1] for col in cursor.fetchall()]
        logger.info(f"✅ books表最终字段: {books_final}")
        
        cursor.execute("PRAGMA table_info(book_snapshots)")
        snapshots_final = [col[1] for col in cursor.fetchall()]
        logger.info(f"✅ book_snapshots表最终字段: {snapshots_final}")
        
        cursor.execute("SELECT COUNT(*) FROM book_snapshots")
        final_count = cursor.fetchone()[0]
        logger.info(f"✅ book_snapshots表最终记录数: {final_count}")
        
        conn.close()
        
        logger.info("🎉 数据库迁移成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        
        # 恢复备份
        logger.info("正在恢复数据库备份...")
        import shutil
        shutil.copy2(backup_path, db_path)
        logger.info("✅ 数据库已恢复到迁移前状态")
        return False


def main():
    """主函数"""
    logger.info("开始执行字段名称和结构迁移...")
    
    success = migrate_database()
    
    if success:
        logger.info("🎉 迁移完成！字段名称已更新，VIP章节数已移至books表")
    else:
        logger.error("💥 迁移失败，数据库已恢复到原始状态")
        exit(1)


if __name__ == "__main__":
    main()