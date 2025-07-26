#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
# @Project : backend
# @File    : migrate.py
# @Date    : 2025/7/26 12:04
# @Author  : Lien Gu
'''

from sqlalchemy import text

from ..logger import get_logger
from ..utils import get_model_fields


def backup_existing_data(engine):
    """
    备份现有数据到临时表
    """
    logger = get_logger(__name__)
    backup_data = {}

    try:
        with engine.connect() as conn:
            # 检查现有表并备份数据
            tables_to_backup = ['rankings', 'books', 'book_snapshots', 'ranking_snapshots']

            for table_name in tables_to_backup:
                try:
                    # 检查表是否存在
                    result = conn.execute(
                        text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
                    if result.fetchone():
                        # 备份表数据
                        data_result = conn.execute(text(f"SELECT * FROM {table_name}"))
                        backup_data[table_name] = data_result.fetchall()
                        logger.info(f"备份表 {table_name}: {len(backup_data[table_name])} 条记录")
                except Exception as e:
                    logger.warning(f"备份表 {table_name} 失败: {e}")

    except Exception as e:
        logger.error(f"数据备份失败: {e}")

    return backup_data


def restore_data_with_mapping(backup_data):
    """
    将备份数据恢复到新表结构中，处理字段变化
    """
    logger = get_logger(__name__)

    if not backup_data:
        logger.info("没有数据需要恢复")
        return

    try:
        # 字段映射配置：旧字段名 -> 新字段名
        field_mappings = {
            'rankings': {
                # 如果有字段名变化，在这里配置映射
                # 'old_field_name': 'new_field_name'
            },
            'books': {
                # 例如：'old_author_name': 'author_name'
            },
            'book_snapshots': {},
            'ranking_snapshots': {}
        }

        with SessionLocal() as session:
            # 恢复 rankings 表
            if 'rankings' in backup_data and backup_data['rankings']:
                from .db.ranking import Ranking
                for row in backup_data['rankings']:
                    try:
                        # 构建新记录数据，处理字段映射
                        row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)

                        # 应用字段映射
                        mapped_data = {}
                        for old_field, value in row_dict.items():
                            new_field = field_mappings['rankings'].get(old_field, old_field)
                            mapped_data[new_field] = value

                        # 过滤掉不存在的字段
                        valid_fields = get_model_fields(Ranking)
                        filtered_data = {k: v for k, v in mapped_data.items() if k in valid_fields and k != 'id'}

                        ranking = Ranking(**filtered_data)
                        session.merge(ranking)  # 使用merge避免主键冲突
                    except Exception as e:
                        logger.warning(f"恢复ranking记录失败: {e}")

                session.commit()
                logger.info(f"恢复 rankings 表: {len(backup_data['rankings'])} 条记录")

            # 恢复 books 表
            if 'books' in backup_data and backup_data['books']:
                from .db.book import Book
                for row in backup_data['books']:
                    try:
                        row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)

                        # 应用字段映射
                        mapped_data = {}
                        for old_field, value in row_dict.items():
                            new_field = field_mappings['books'].get(old_field, old_field)
                            mapped_data[new_field] = value

                        # 过滤字段
                        valid_fields = get_model_fields(Book)
                        filtered_data = {k: v for k, v in mapped_data.items() if k in valid_fields and k != 'id'}

                        book = Book(**filtered_data)
                        session.merge(book)
                    except Exception as e:
                        logger.warning(f"恢复book记录失败: {e}")

                session.commit()
                logger.info(f"恢复 books 表: {len(backup_data['books'])} 条记录")

            # 恢复快照表（需要重新建立外键关系）
            if 'book_snapshots' in backup_data and backup_data['book_snapshots']:
                from .db.book import BookSnapshot
                for row in backup_data['book_snapshots']:
                    try:
                        row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)

                        # 过滤字段
                        valid_fields = get_model_fields(BookSnapshot)
                        filtered_data = {k: v for k, v in row_dict.items() if k in valid_fields and k != 'id'}

                        snapshot = BookSnapshot(**filtered_data)
                        session.add(snapshot)
                    except Exception as e:
                        logger.warning(f"恢复book_snapshot记录失败: {e}")

                session.commit()
                logger.info(f"恢复 book_snapshots 表: {len(backup_data['book_snapshots'])} 条记录")

            if 'ranking_snapshots' in backup_data and backup_data['ranking_snapshots']:
                from .db.ranking import RankingSnapshot
                for row in backup_data['ranking_snapshots']:
                    try:
                        row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)

                        # 过滤字段
                        valid_fields = get_model_fields(RankingSnapshot)
                        filtered_data = {k: v for k, v in row_dict.items() if k in valid_fields and k != 'id'}

                        snapshot = RankingSnapshot(**filtered_data)
                        session.add(snapshot)
                    except Exception as e:
                        logger.warning(f"恢复ranking_snapshot记录失败: {e}")

                session.commit()
                logger.info(f"恢复 ranking_snapshots 表: {len(backup_data['ranking_snapshots'])} 条记录")

    except Exception as e:
        logger.error(f"数据恢复失败: {e}")


def migrate_database(preserve_data: bool = True):
    """
    数据库迁移功能
    检查数据库结构是否发生变化，如果有变化则进行迁移

    Args:
        preserve_data: 是否保留现有数据，默认为True
    """
    logger = get_logger(__name__)

    try:
        # 尝试检查现有表结构
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            existing_tables = [row[0] for row in result.fetchall()]
            logger.info(f"发现现有表: {existing_tables}")

        # 检查表结构是否匹配当前模型
        from .db.base import Base
        expected_tables = list(Base.metadata.tables.keys())
        logger.info(f"期望的表: {expected_tables}")

        # 如果表结构不匹配，进行迁移
        if set(existing_tables) != set(expected_tables):
            logger.warning("数据库表结构不匹配，开始数据库迁移...")

            backup_data = {}
            if preserve_data and existing_tables:
                logger.info("备份现有数据...")
                backup_data = backup_existing_data()

            # 重建数据库结构
            logger.info("重建数据库结构...")
            drop_tables()
            create_tables()

            # 恢复数据
            if preserve_data and backup_data:
                logger.info("恢复数据...")
                restore_data_with_mapping(backup_data)

            logger.info("数据库迁移完成")
        else:
            logger.info("数据库表结构匹配，无需迁移")

    except Exception as e:
        logger.warning(f"数据库检查失败，重建数据库: {e}")
        # 如果检查失败，直接重建（不保留数据）
        try:
            drop_tables()
        except:
            pass  # 忽略删除表失败的错误
        create_tables()
        logger.info("数据库重建完成")


def ensure_database():
    """
    确保数据库存在且结构正确
    在应用启动时调用
    """
    logger = get_logger(__name__)
    logger.info("检查数据库状态...")

    try:
        migrate_database()
        logger.info("数据库准备就绪")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
