"""
失败存储工具

负责存储和管理爬取失败的数据：
- 失败任务存储（7天保留期）
- 爬取成功但解析失败的原始数据存储
- 自动清理过期数据
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FailureRecord:
    """失败记录"""
    task_id: str
    task_type: str  # 'jiazi', 'page', etc.
    failure_type: str  # 'task_failure', 'parse_failure'
    error_message: str
    raw_data: Optional[Dict[str, Any]]  # 原始响应数据（如果有的话）
    url: Optional[str]
    channel: Optional[str]  # 对于page类型任务
    created_at: str  # ISO格式时间
    expires_at: str  # ISO格式时间


class FailureStorage:
    """
    失败存储管理器
    
    负责存储各种类型的失败数据：
    - 任务执行失败
    - 爬取成功但解析失败
    - 自动清理过期数据
    """
    
    def __init__(self, storage_dir: str = None):
        """
        初始化失败存储管理器
        
        Args:
            storage_dir: 存储目录，默认为项目根目录下的data/failures
        """
        if storage_dir is None:
            # 默认存储路径
            project_root = Path(__file__).parent.parent.parent
            storage_dir = project_root / "data" / "failures"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 失败记录文件
        self.failures_file = self.storage_dir / "failures.json"
        self.raw_data_dir = self.storage_dir / "raw_data"
        self.raw_data_dir.mkdir(exist_ok=True)
        
        logger.debug(f"失败存储初始化完成: {self.storage_dir}")
    
    def store_task_failure(
        self, 
        task_id: str, 
        task_type: str, 
        error_message: str,
        url: Optional[str] = None,
        channel: Optional[str] = None
    ) -> str:
        """
        存储任务执行失败记录
        
        Args:
            task_id: 任务ID
            task_type: 任务类型 ('jiazi', 'page')
            error_message: 错误信息
            url: 请求URL
            channel: 频道（对于page类型）
            
        Returns:
            存储的记录ID
        """
        record = FailureRecord(
            task_id=task_id,
            task_type=task_type,
            failure_type="task_failure",
            error_message=error_message,
            raw_data=None,
            url=url,
            channel=channel,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=7)).isoformat()
        )
        
        return self._save_record(record)
    
    def store_parse_failure(
        self,
        task_id: str,
        task_type: str,
        error_message: str,
        raw_data: Dict[str, Any],
        url: Optional[str] = None,
        channel: Optional[str] = None
    ) -> str:
        """
        存储解析失败记录（爬取成功但解析失败）
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            error_message: 解析错误信息
            raw_data: 原始响应数据
            url: 请求URL
            channel: 频道
            
        Returns:
            存储的记录ID
        """
        # 生成原始数据文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_data_filename = f"{task_type}_{timestamp}_{task_id[:8]}.json"
        
        # 保存原始数据到单独文件
        raw_data_path = self.raw_data_dir / raw_data_filename
        try:
            with open(raw_data_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            logger.info(f"原始数据已保存: {raw_data_path}")
        except Exception as e:
            logger.error(f"保存原始数据失败: {e}")
            raw_data_filename = None
        
        record = FailureRecord(
            task_id=task_id,
            task_type=task_type,
            failure_type="parse_failure",
            error_message=error_message,
            raw_data={"file": raw_data_filename} if raw_data_filename else None,
            url=url,
            channel=channel,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=7)).isoformat()
        )
        
        return self._save_record(record)
    
    def _save_record(self, record: FailureRecord) -> str:
        """
        保存失败记录到JSON文件
        
        Args:
            record: 失败记录
            
        Returns:
            记录ID
        """
        try:
            # 读取现有记录
            records = []
            if self.failures_file.exists():
                try:
                    with open(self.failures_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    logger.warning("失败记录文件损坏或不存在，创建新文件")
                    records = []
            
            # 添加新记录
            records.append(asdict(record))
            
            # 保存记录
            with open(self.failures_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            logger.info(f"失败记录已保存: {record.task_id} ({record.failure_type})")
            return record.task_id
            
        except Exception as e:
            logger.error(f"保存失败记录失败: {e}")
            raise
    
    def get_failures(
        self, 
        task_type: Optional[str] = None,
        failure_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取失败记录
        
        Args:
            task_type: 任务类型过滤
            failure_type: 失败类型过滤
            limit: 限制返回数量
            
        Returns:
            失败记录列表
        """
        try:
            if not self.failures_file.exists():
                return []
            
            with open(self.failures_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            # 过滤记录
            filtered_records = []
            for record in records:
                # 检查是否过期
                expires_at = datetime.fromisoformat(record['expires_at'])
                if expires_at < datetime.now():
                    continue
                
                # 应用过滤条件
                if task_type and record.get('task_type') != task_type:
                    continue
                if failure_type and record.get('failure_type') != failure_type:
                    continue
                
                filtered_records.append(record)
            
            # 按创建时间排序（最新的在前）
            filtered_records.sort(key=lambda x: x['created_at'], reverse=True)
            
            # 应用数量限制
            if limit:
                filtered_records = filtered_records[:limit]
            
            return filtered_records
            
        except Exception as e:
            logger.error(f"获取失败记录失败: {e}")
            return []
    
    def get_raw_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取原始数据
        
        Args:
            task_id: 任务ID
            
        Returns:
            原始数据或None
        """
        try:
            records = self.get_failures()
            
            # 查找对应记录
            target_record = None
            for record in records:
                if record['task_id'] == task_id and record.get('raw_data'):
                    target_record = record
                    break
            
            if not target_record or not target_record.get('raw_data'):
                return None
            
            raw_data_info = target_record['raw_data']
            if not raw_data_info.get('file'):
                return None
            
            # 读取原始数据文件
            raw_data_path = self.raw_data_dir / raw_data_info['file']
            if not raw_data_path.exists():
                logger.warning(f"原始数据文件不存在: {raw_data_path}")
                return None
            
            with open(raw_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"获取原始数据失败: {e}")
            return None
    
    def cleanup_expired_records(self) -> int:
        """
        清理过期记录
        
        Returns:
            清理的记录数量
        """
        try:
            if not self.failures_file.exists():
                return 0
            
            with open(self.failures_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            current_time = datetime.now()
            valid_records = []
            expired_count = 0
            expired_files = []
            
            for record in records:
                expires_at = datetime.fromisoformat(record['expires_at'])
                if expires_at >= current_time:
                    valid_records.append(record)
                else:
                    expired_count += 1
                    # 收集需要删除的原始数据文件
                    if record.get('raw_data', {}).get('file'):
                        expired_files.append(record['raw_data']['file'])
            
            if expired_count > 0:
                # 保存有效记录
                with open(self.failures_file, 'w', encoding='utf-8') as f:
                    json.dump(valid_records, f, ensure_ascii=False, indent=2)
                
                # 删除过期的原始数据文件
                for filename in expired_files:
                    raw_data_path = self.raw_data_dir / filename
                    try:
                        if raw_data_path.exists():
                            raw_data_path.unlink()
                            logger.debug(f"已删除过期原始数据文件: {filename}")
                    except Exception as e:
                        logger.warning(f"删除原始数据文件失败 {filename}: {e}")
                
                logger.info(f"清理完成: 删除 {expired_count} 条过期记录")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"清理过期记录失败: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取失败统计信息
        
        Returns:
            统计信息字典
        """
        try:
            records = self.get_failures()
            
            stats = {
                "total_failures": len(records),
                "task_failures": len([r for r in records if r['failure_type'] == 'task_failure']),
                "parse_failures": len([r for r in records if r['failure_type'] == 'parse_failure']),
                "by_task_type": {},
                "recent_failures": len([
                    r for r in records 
                    if datetime.fromisoformat(r['created_at']) > datetime.now() - timedelta(hours=24)
                ])
            }
            
            # 按任务类型统计
            for record in records:
                task_type = record.get('task_type', 'unknown')
                if task_type not in stats["by_task_type"]:
                    stats["by_task_type"][task_type] = 0
                stats["by_task_type"][task_type] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_failures": 0,
                "task_failures": 0,
                "parse_failures": 0,
                "by_task_type": {},
                "recent_failures": 0
            }


# 全局失败存储实例
_failure_storage = None


def get_failure_storage() -> FailureStorage:
    """获取全局失败存储实例"""
    global _failure_storage
    if _failure_storage is None:
        _failure_storage = FailureStorage()
    return _failure_storage