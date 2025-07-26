#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库表结构更新工具
基于SQLAlchemy DDL操作的数据库结构管理
针对SQLite数据库的特殊限制进行优化
"""

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Tuple, List, Any, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import (
    text, inspect
)
from sqlalchemy.exc import SQLAlchemyError

# 导入项目的数据库连接
from app.database.connection import engine, SessionLocal
from app.logger import get_logger, setup_logging


class DatabaseUpdater:
    """数据库更新工具类"""

    # 常用类型映射
    TYPE_MAPPING = {
        'Integer': 'INTEGER',
        'String': 'VARCHAR(255)',
        'Text': 'TEXT',
        'DateTime': 'DATETIME',
        'Boolean': 'BOOLEAN'
    }

    def __init__(self):
        """初始化数据库更新工具"""
        self.logger = get_logger(__name__)
        self.engine = engine
        self.inspector = inspect(self.engine)

    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        session = SessionLocal()
        try:
            yield session
            session.commit()
            self.logger.debug("数据库事务提交成功")
        except Exception as e:
            session.rollback()
            self.logger.error(f"数据库事务回滚: {e}")
            raise
        finally:
            session.close()

    def _get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息"""
        try:
            if table_name not in self.inspector.get_table_names():
                self.logger.error(f"表 {table_name} 不存在")
                return {}

            columns = self.inspector.get_columns(table_name)
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            indexes = self.inspector.get_indexes(table_name)

            return {
                'columns': columns,
                'primary_key': pk_constraint,
                'foreign_keys': foreign_keys,
                'indexes': indexes
            }
        except SQLAlchemyError as e:
            self.logger.error(f"获取表 {table_name} 结构失败: {e}")
            return {}

    def _get_referencing_foreign_keys(self, table_name: str, column_names: List[str]) -> List[Dict[str, Any]]:
        """获取引用指定表列的外键约束"""
        referencing_fks = []

        try:
            # 检查所有表的外键
            for table in self.inspector.get_table_names():
                fks = self.inspector.get_foreign_keys(table)
                for fk in fks:
                    if (fk['referred_table'] == table_name and
                            any(col in column_names for col in fk['referred_columns'])):
                        referencing_fks.append({
                            'table': table,
                            'constraint_name': fk.get('name', ''),
                            'constrained_columns': fk['constrained_columns'],
                            'referred_table': fk['referred_table'],
                            'referred_columns': fk['referred_columns']
                        })

            return referencing_fks
        except SQLAlchemyError as e:
            self.logger.error(f"获取外键引用失败: {e}")
            return []

    def _validate_columns_exist(self, table: str, column_names: List[str], table_info: Dict[str, Any]) -> bool:
        """验证列是否存在于表中"""
        existing_columns = {col['name']: col for col in table_info['columns']}
        for col_name in column_names:
            if col_name not in existing_columns:
                self.logger.error(f"列 {col_name} 在表 {table} 中不存在")
                return False
        return True

    def _map_column_type(self, col_type: str) -> str:
        """映射列类型为SQL类型"""
        return self.TYPE_MAPPING.get(col_type, col_type.upper())

    def _generate_column_def(self, column_info: Dict[str, Any]) -> str:
        """根据列信息生成列定义SQL"""
        name = column_info['name']
        type_str = str(column_info['type'])

        # 处理常见的SQLAlchemy类型映射
        if 'VARCHAR' in type_str:
            col_def = f"{name} {type_str}"
        elif 'INTEGER' in type_str:
            col_def = f"{name} INTEGER"
        elif 'TEXT' in type_str:
            col_def = f"{name} TEXT"
        elif 'DATETIME' in type_str:
            col_def = f"{name} DATETIME"
        elif 'BOOLEAN' in type_str:
            col_def = f"{name} BOOLEAN"
        else:
            col_def = f"{name} {type_str}"

        # 添加约束
        if not column_info.get('nullable', True):
            col_def += " NOT NULL"

        if column_info.get('default') is not None:
            default_val = column_info['default']
            if isinstance(default_val, str):
                col_def += f" DEFAULT '{default_val}'"
            else:
                col_def += f" DEFAULT {default_val}"

        if column_info.get('primary_key', False):
            col_def += " PRIMARY KEY"

        if column_info.get('autoincrement', False):
            col_def += " AUTOINCREMENT"

        return col_def

    def _create_temp_table_sql(self, table_name: str, columns: List[Dict[str, Any]],
                               temp_name: str) -> str:
        """生成创建临时表的SQL"""
        column_defs = []
        for col in columns:
            column_defs.append(self._generate_column_def(col))

        return f"CREATE TABLE {temp_name} ({', '.join(column_defs)})"

    def _rebuild_table_with_structure(self, table: str, new_columns: List[Dict[str, Any]],
                                      operation_suffix: str, data_mapping: Optional[Dict[str, str]] = None) -> None:
        """通用的表重建逻辑"""
        temp_table_name = f"{table}_temp_{operation_suffix}"

        with self.get_session() as session:
            # 1. 创建临时表
            create_temp_sql = self._create_temp_table_sql(table, new_columns, temp_table_name)
            session.execute(text(create_temp_sql))
            self.logger.info(f"创建临时表 {temp_table_name}")

            # 2. 复制数据
            if data_mapping:
                # 有列映射的情况
                old_cols = list(data_mapping.keys())
                new_cols = list(data_mapping.values())
            else:
                # 使用新表结构的列名
                old_cols = new_cols = [col['name'] for col in new_columns]

            old_cols_str = ', '.join(old_cols)
            new_cols_str = ', '.join(new_cols)

            copy_sql = f"INSERT INTO {temp_table_name} ({new_cols_str}) SELECT {old_cols_str} FROM {table}"
            session.execute(text(copy_sql))
            self.logger.info(f"数据复制完成")

            # 3. 删除原表
            session.execute(text(f"DROP TABLE {table}"))
            self.logger.info(f"删除原表 {table}")

            # 4. 重命名临时表
            session.execute(text(f"ALTER TABLE {temp_table_name} RENAME TO {table}"))
            self.logger.info(f"重命名临时表为 {table}")


# 创建全局更新器实例
_updater = DatabaseUpdater()


def change_columns_name(table: str, change_columns: Dict[str, str]):
    """
    改变表格列名
    :param table: 表格名称
    :param change_columns: 字典中的键值分别对应旧名与新名，{"old_name":"new_name"}
    :return:
    """
    logger = _updater.logger
    logger.info(f"开始修改表 {table} 的列名: {change_columns}")

    try:
        # 获取表结构
        table_info = _updater._get_table_structure(table)
        if not table_info:
            return

        # 检查要重命名的列是否存在
        if not _updater._validate_columns_exist(table, list(change_columns.keys()), table_info):
            return

        # 创建包含新列名的表结构
        updated_columns = []
        old_to_new_mapping = {}

        for col in table_info['columns']:
            col_copy = col.copy()
            if col['name'] in change_columns:
                new_name = change_columns[col['name']]
                old_to_new_mapping[col['name']] = new_name
                col_copy['name'] = new_name
            updated_columns.append(col_copy)

        # 构建数据映射
        data_mapping = {col['name']: change_columns.get(col['name'], col['name'])
                        for col in table_info['columns']}

        # 使用通用重建方法
        _updater._rebuild_table_with_structure(table, updated_columns, "rename", data_mapping)
        logger.info(f"表 {table} 列名修改完成: {change_columns}")

    except SQLAlchemyError as e:
        logger.error(f"修改表 {table} 列名失败: {e}")
        raise


def change_columns_type(table: str, change_columns: Dict[str, str]):
    """
    改变表格中列的数据类型
    :param table: 表格名称
    :param change_columns: 字典中的键值分别对应列名与类型 {"column_name":"column_type"}
    :return:
    """
    logger = _updater.logger
    logger.info(f"开始修改表 {table} 的列类型: {change_columns}")

    try:
        # 获取表结构
        table_info = _updater._get_table_structure(table)
        if not table_info:
            return

        # 检查要修改的列是否存在
        if not _updater._validate_columns_exist(table, list(change_columns.keys()), table_info):
            return

        # 创建包含新列类型的表结构
        updated_columns = []

        for col in table_info['columns']:
            col_copy = col.copy()
            if col['name'] in change_columns:
                # 更新列类型
                new_type = change_columns[col['name']]
                col_copy['type'] = _updater._map_column_type(new_type)
            updated_columns.append(col_copy)

        # 使用通用重建方法
        _updater._rebuild_table_with_structure(table, updated_columns, "type")
        logger.info(f"表 {table} 列类型修改完成: {change_columns}")

    except SQLAlchemyError as e:
        logger.error(f"修改表 {table} 列类型失败: {e}")
        raise


def add_columns(table: str, new_columns: Dict[str, str]):
    """
    表格中添加多个列
    :param table: 表格名称
    :param new_columns: 字典中的键值分别对应列名与类型 {"column_name":"column_type"}
    :return:
    """
    logger = _updater.logger
    logger.info(f"开始为表 {table} 添加列: {new_columns}")

    try:
        # 检查表是否存在
        if table not in _updater.inspector.get_table_names():
            logger.error(f"表 {table} 不存在")
            return

        with _updater.get_session() as session:
            for col_name, col_type in new_columns.items():
                # 映射类型
                sql_type = _updater._map_column_type(col_type)

                # SQLite支持ALTER TABLE ADD COLUMN
                alter_sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {sql_type}"
                session.execute(text(alter_sql))
                logger.info(f"添加列 {col_name} ({sql_type}) 到表 {table}")

            logger.info(f"表 {table} 添加列完成: {new_columns}")

    except SQLAlchemyError as e:
        logger.error(f"为表 {table} 添加列失败: {e}")
        raise


def delete_columns(table: str, cols_to_delete: List[str]):
    """
    删除多个列，同时如果这个列是其它列的外键，需要列出然后一并删除这些外键
    :param table: 表格名称
    :param cols_to_delete: 列表中的元素为待删除列的列名
    :return:
    """
    logger = _updater.logger
    logger.info(f"开始删除表 {table} 的列: {cols_to_delete}")

    try:
        # 获取表结构
        table_info = _updater._get_table_structure(table)
        if not table_info:
            return

        # 检查要删除的列是否存在
        if not _updater._validate_columns_exist(table, cols_to_delete, table_info):
            return

        # 检查引用这些列的外键
        referencing_fks = _updater._get_referencing_foreign_keys(table, cols_to_delete)
        if referencing_fks:
            logger.warning(f"发现引用待删除列的外键约束: {referencing_fks}")
            for fk in referencing_fks:
                logger.warning(
                    f"表 {fk['table']} 的外键 {fk['constraint_name']} 引用了 {table}.{fk['referred_columns']}")

        # 创建不包含待删除列的表结构
        remaining_columns = [
            col for col in table_info['columns']
            if col['name'] not in cols_to_delete
        ]

        if not remaining_columns:
            logger.error(f"不能删除表 {table} 的所有列")
            return

        # 使用通用重建方法
        _updater._rebuild_table_with_structure(table, remaining_columns, "delete")
        logger.info(f"表 {table} 删除列完成: {cols_to_delete}")

        # 提示需要手动处理的外键
        if referencing_fks:
            logger.warning("注意: 以下外键约束可能需要手动处理:")
            for fk in referencing_fks:
                logger.warning(f"  - 表 {fk['table']} 的外键约束可能已失效")

    except SQLAlchemyError as e:
        logger.error(f"删除表 {table} 的列失败: {e}")
        raise


def migrate_table(table_index: Tuple[str, str], cols_index: Dict[str, str]):
    """
    迁移旧表到新表中。
    如果新表不存在，则创建新表。迁移后需要删除旧表。
    :param table_index: 包含旧表和新表名称，("old_table", "new_table")
    :param cols_index: 列映射字典，{"old_cols1":"new_cols1","old_cols2":"new_cols2"}
    :return:
    """
    old_table, new_table = table_index
    logger = _updater.logger
    logger.info(f"开始迁移表: {old_table} -> {new_table}, 列映射: {cols_index}")

    try:
        # 检查旧表是否存在
        if old_table not in _updater.inspector.get_table_names():
            logger.error(f"源表 {old_table} 不存在")
            return

        # 获取旧表结构
        old_table_info = _updater._get_table_structure(old_table)
        if not old_table_info:
            return

        # 检查列映射
        if not _updater._validate_columns_exist(old_table, list(cols_index.keys()), old_table_info):
            return

        with _updater.get_session() as session:
            # 1. 检查新表是否存在，如果不存在则创建
            if new_table not in _updater.inspector.get_table_names():
                logger.info(f"新表 {new_table} 不存在，开始创建")

                # 创建新表结构（基于旧表结构和列映射）
                new_columns = []
                for col in old_table_info['columns']:
                    if col['name'] in cols_index:
                        col_copy = col.copy()
                        col_copy['name'] = cols_index[col['name']]
                        new_columns.append(col_copy)

                create_new_sql = _updater._create_temp_table_sql(old_table, new_columns, new_table)
                session.execute(text(create_new_sql))
                logger.info(f"创建新表 {new_table}")

            # 2. 迁移数据
            old_column_list = list(cols_index.keys())
            new_column_list = [cols_index[col] for col in old_column_list]

            old_cols_str = ', '.join(old_column_list)
            new_cols_str = ', '.join(new_column_list)

            migrate_sql = f"INSERT INTO {new_table} ({new_cols_str}) SELECT {old_cols_str} FROM {old_table}"
            session.execute(text(migrate_sql))
            logger.info(f"数据迁移完成: {len(old_column_list)} 列")

            # 3. 删除旧表
            session.execute(text(f"DROP TABLE {old_table}"))
            logger.info(f"删除旧表 {old_table}")

            logger.info(f"表迁移完成: {old_table} -> {new_table}")

    except SQLAlchemyError as e:
        logger.error(f"表迁移失赅: {e}")
        raise


def delete_tables(table_names: List[str]):
    """
    删除表格
    :param table_names: 被删除的表格名称列表
    :return:
    """
    logger = _updater.logger
    logger.info(f"开始删除表: {table_names}")

    try:
        existing_tables = _updater.inspector.get_table_names()

        with _updater.get_session() as session:
            for table_name in table_names:
                if table_name not in existing_tables:
                    logger.warning(f"表 {table_name} 不存在，跳过删除")
                    continue

                # 检查是否有其他表引用此表
                referencing_fks = []
                for table in existing_tables:
                    if table == table_name:
                        continue
                    fks = _updater.inspector.get_foreign_keys(table)
                    for fk in fks:
                        if fk['referred_table'] == table_name:
                            referencing_fks.append({
                                'table': table,
                                'constraint_name': fk.get('name', ''),
                                'referred_table': fk['referred_table']
                            })

                if referencing_fks:
                    logger.warning(f"表 {table_name} 被以下外键引用:")
                    for fk in referencing_fks:
                        logger.warning(f"  - 表 {fk['table']} 的外键约束 {fk['constraint_name']}")
                    logger.warning("删除此表可能会导致外键约束失效")

                # 删除表
                session.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                logger.info(f"删除表 {table_name}")

            logger.info(f"删除表操作完成: {table_names}")

    except SQLAlchemyError as e:
        logger.error(f"删除表失败: {e}")
        raise


if __name__ == '__main__':
    # 示例运行：删除book表格的running、age列
    try:
        delete_columns("books", ["running", "age"])
        print("删除列操作完成")
    except Exception as e:
        print(f"操作失败: {e}")

    # 其他示例用法
    # change_columns_name("books", {"old_title": "title", "old_author": "author"})
    # change_columns_type("books", {"rating": "Integer", "description": "Text"})
    # add_columns("books", {"isbn": "String", "published_date": "DateTime"})
    # migrate_table(("old_books", "books"), {"old_title": "title", "old_content": "content"})
    # delete_tables(["temp_table", "backup_table"])
