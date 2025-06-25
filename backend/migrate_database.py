#!/usr/bin/env python3
"""
数据库迁移脚本

用于更新数据库结构：
1. 在book_snapshots表中添加word_count字段
2. 修改ranking_snapshots表的ranking_id字段类型
3. 保留现有数据
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """执行数据库迁移"""
    db_path = Path("data/jjcrawler.db")
    
    if not db_path.exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = Path(f"data/jjcrawler_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    logger.info(f"创建数据库备份: {backup_path}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 检查当前表结构
            logger.info("检查当前数据库结构...")
            
            # 检查book_snapshots表是否有word_count字段
            cursor.execute("PRAGMA table_info(book_snapshots)")
            book_snapshots_columns = {row[1] for row in cursor.fetchall()}
            
            if 'word_count' not in book_snapshots_columns:
                logger.info("为book_snapshots表添加word_count字段...")
                cursor.execute("ALTER TABLE book_snapshots ADD COLUMN word_count INTEGER")
                logger.info("✅ word_count字段添加成功")
            else:
                logger.info("✅ book_snapshots表已有word_count字段")
            
            # 检查ranking_snapshots表的ranking_id字段类型
            cursor.execute("PRAGMA table_info(ranking_snapshots)")
            ranking_columns = cursor.fetchall()
            ranking_id_type = None
            
            for column in ranking_columns:
                if column[1] == 'ranking_id':
                    ranking_id_type = column[2]
                    break
            
            logger.info(f"ranking_snapshots.ranking_id当前类型: {ranking_id_type}")
            
            # 如果ranking_id是VARCHAR类型，需要迁移
            if ranking_id_type and ranking_id_type.upper() == 'VARCHAR':
                logger.info("需要迁移ranking_snapshots表的ranking_id字段...")
                
                # 创建新表
                cursor.execute("""
                CREATE TABLE ranking_snapshots_new (
                    id INTEGER PRIMARY KEY,
                    ranking_id INTEGER NOT NULL,
                    book_id VARCHAR NOT NULL,
                    position INTEGER NOT NULL,
                    snapshot_time TIMESTAMP NOT NULL
                )
                """)
                
                # 获取rankings表的映射关系
                cursor.execute("SELECT id, ranking_id FROM rankings")
                ranking_mapping = {row[1]: row[0] for row in cursor.fetchall()}
                
                logger.info(f"榜单映射关系: {ranking_mapping}")
                
                # 迁移数据
                cursor.execute("SELECT id, ranking_id, book_id, position, snapshot_time FROM ranking_snapshots")
                old_data = cursor.fetchall()
                
                migrated_count = 0
                for row in old_data:
                    old_ranking_id = row[1]
                    new_ranking_id = ranking_mapping.get(old_ranking_id)
                    
                    if new_ranking_id is not None:
                        cursor.execute("""
                        INSERT INTO ranking_snapshots_new (id, ranking_id, book_id, position, snapshot_time)
                        VALUES (?, ?, ?, ?, ?)
                        """, (row[0], new_ranking_id, row[2], row[3], row[4]))
                        migrated_count += 1
                    else:
                        logger.warning(f"未找到榜单ID映射: {old_ranking_id}")
                
                # 删除旧表，重命名新表
                cursor.execute("DROP TABLE ranking_snapshots")
                cursor.execute("ALTER TABLE ranking_snapshots_new RENAME TO ranking_snapshots")
                
                # 重建索引
                cursor.execute("CREATE INDEX idx_ranking_time ON ranking_snapshots(ranking_id, snapshot_time)")
                cursor.execute("CREATE INDEX idx_book_ranking_time ON ranking_snapshots(book_id, snapshot_time)")
                cursor.execute("CREATE INDEX idx_ranking_position ON ranking_snapshots(ranking_id, position, snapshot_time)")
                
                logger.info(f"✅ ranking_snapshots表迁移完成，迁移了 {migrated_count} 条记录")
            else:
                logger.info("✅ ranking_snapshots表的ranking_id字段类型正确")
            
            # 提交事务
            conn.commit()
            logger.info("✅ 数据库迁移完成")
            
            # 验证迁移结果
            cursor.execute("PRAGMA table_info(book_snapshots)")
            book_columns = [row[1] for row in cursor.fetchall()]
            logger.info(f"book_snapshots表字段: {book_columns}")
            
            cursor.execute("PRAGMA table_info(ranking_snapshots)")
            ranking_columns = cursor.fetchall()
            logger.info(f"ranking_snapshots表结构: {[(row[1], row[2]) for row in ranking_columns]}")
            
            return True
            
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        logger.info(f"可以从备份恢复: {backup_path}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("✅ 数据库迁移成功完成")
    else:
        print("❌ 数据库迁移失败")
        exit(1)