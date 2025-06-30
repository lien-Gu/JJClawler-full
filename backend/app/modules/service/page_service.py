"""
页面服务模块 - T4.2数据服务模块

负责页面配置管理和数据服务：
- 页面配置生成和缓存
- 层级关系管理
- 分页和过滤服务
- 统一的数据访问接口

设计原则：
1. 高效缓存：静态配置数据缓存优化
2. 层级清晰：页面父子关系管理
3. 接口统一：提供标准化的数据服务
4. 易于扩展：支持新增页面类型
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.config import get_settings
from app.utils.file_utils import read_json_file
from app.utils.log_utils import get_logger

logger = get_logger(__name__)


class PageService:
    """
    页面服务类
    
    提供完整的页面配置和数据服务：
    - 配置文件管理
    - 页面层级关系
    - 数据转换和格式化
    - 缓存管理
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化页面服务
        
        Args:
            config_path: 配置文件路径
        """
        # 如果没有指定路径，从settings读取
        if config_path is None:
            settings = get_settings()
            config_path = settings.URLS_CONFIG_FILE
            
        self.config_path = Path(config_path)
        self._config_cache = None
        self._cache_timestamp = None
        self._cache_ttl = timedelta(minutes=30)  # 缓存30分钟
        
        # 确保配置文件存在
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    def _load_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            force_refresh: 强制刷新缓存
            
        Returns:
            配置数据字典
        """
        current_time = datetime.now()
        
        # 检查缓存是否有效
        if (not force_refresh and 
            self._config_cache is not None and 
            self._cache_timestamp is not None and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._config_cache
        
        # 使用utils中的文件读取函数
        config = read_json_file(self.config_path)
        
        if config is None:
            logger.error("页面配置加载失败")
            raise FileNotFoundError(f"无法读取配置文件: {self.config_path}")
        
        # 更新缓存
        self._config_cache = config
        self._cache_timestamp = current_time
        
        logger.debug("页面配置加载成功")
        return config
    
    def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        获取所有页面配置
        
        Returns:
            页面配置列表
        """
        try:
            config = self._load_config()
            pages = []
            
            # 添加夹子榜
            jiazi_config = config['content']['jiazi']
            pages.append({
                'page_id': jiazi_config['short_name'],
                'name': jiazi_config['zh_name'],
                'type': jiazi_config['type'],
                'frequency': jiazi_config['frequency'],
                'rankings': [{
                    'ranking_id': jiazi_config['short_name'],
                    'name': jiazi_config['zh_name'],
                    'update_frequency': jiazi_config['frequency']
                }],
                'parent_id': None
            })
            
            # 添加分类页面
            pages_config = config['content']['pages']
            for page_key, page_info in pages_config.items():
                if not isinstance(page_info, dict):
                    continue
                
                # 主页面
                rankings = []
                sub_pages = []
                
                # 添加子页面
                if 'sub_pages' in page_info:
                    for sub_key, sub_info in page_info['sub_pages'].items():
                        if isinstance(sub_info, dict):
                            sub_page_id = f"{page_info['short_name']}.{sub_info['short_name']}"
                            rankings.append({
                                'ranking_id': sub_page_id,
                                'name': sub_info['zh_name'],
                                'update_frequency': sub_info['frequency']
                            })
                            sub_pages.append({
                                'page_id': sub_page_id,
                                'name': sub_info['zh_name'],
                                'type': sub_info.get('type', 'daily'),
                                'frequency': sub_info['frequency'],
                                'parent_id': page_info['short_name']
                            })
                
                # 主页面配置
                pages.append({
                    'page_id': page_info['short_name'],
                    'name': page_info['zh_name'],
                    'type': page_info.get('type', 'daily'),
                    'frequency': page_info['frequency'],
                    'rankings': rankings,
                    'sub_pages': sub_pages,
                    'parent_id': None
                })
            
            logger.info(f"页面配置获取成功: {len(pages)} 个页面")
            return pages
            
        except Exception as e:
            logger.error(f"获取页面配置失败: {e}")
            return []
    
    def get_page_by_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取页面配置
        
        Args:
            page_id: 页面ID
            
        Returns:
            页面配置或None
        """
        try:
            all_pages = self.get_all_pages()
            
            for page in all_pages:
                if page['page_id'] == page_id:
                    return page
                
                # 检查子页面
                for sub_page in page.get('sub_pages', []):
                    if sub_page['page_id'] == page_id:
                        return sub_page
            
            logger.warning(f"未找到页面: {page_id}")
            return None
            
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return None
    
    def get_page_hierarchy(self) -> Dict[str, Any]:
        """
        获取页面层级结构
        
        Returns:
            层级结构字典
        """
        try:
            all_pages = self.get_all_pages()
            
            # 构建层级结构
            hierarchy = {
                'root_pages': [],
                'total_pages': len(all_pages),
                'total_rankings': 0
            }
            
            for page in all_pages:
                if page.get('parent_id') is None:
                    hierarchy['root_pages'].append(page)
                    hierarchy['total_rankings'] += len(page.get('rankings', []))
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"获取页面层级失败: {e}")
            return {'root_pages': [], 'total_pages': 0, 'total_rankings': 0}
    
    def get_ranking_channels(self) -> List[Dict[str, str]]:
        """
        获取所有可用的排行榜频道
        
        Returns:
            频道信息列表
        """
        try:
            all_pages = self.get_all_pages()
            channels = []
            
            for page in all_pages:
                for ranking in page.get('rankings', []):
                    channels.append({
                        'channel': ranking['ranking_id'],
                        'name': ranking['name'],
                        'frequency': ranking['update_frequency'],
                        'page_name': page['name']
                    })
            
            logger.info(f"频道列表获取成功: {len(channels)} 个频道")
            return channels
            
        except Exception as e:
            logger.error(f"获取频道列表失败: {e}")
            return []
    
    def refresh_config(self):
        """强制刷新配置缓存"""
        try:
            self._load_config(force_refresh=True)
            logger.info("页面配置缓存已刷新")
        except Exception as e:
            logger.error(f"刷新配置缓存失败: {e}")
            raise
    
    def get_page_statistics(self) -> Dict[str, Any]:
        """
        获取页面统计信息
        
        Returns:
            统计信息字典
        """
        try:
            hierarchy = self.get_page_hierarchy()
            
            # 计算详细统计
            root_count = len(hierarchy['root_pages'])
            sub_page_count = sum(
                len(page.get('sub_pages', [])) 
                for page in hierarchy['root_pages']
            )
            
            return {
                'total_pages': hierarchy['total_pages'],
                'root_pages': root_count,
                'sub_pages': sub_page_count,
                'total_rankings': hierarchy['total_rankings'],
                'config_path': str(self.config_path),
                'cache_valid': self._cache_timestamp is not None,
                'last_updated': self._cache_timestamp.isoformat() if self._cache_timestamp else None
            }
            
        except Exception as e:
            logger.error(f"获取页面统计失败: {e}")
            return {
                'total_pages': 0,
                'root_pages': 0,
                'sub_pages': 0,
                'total_rankings': 0,
                'error': str(e)
            }


# 全局页面服务实例
_page_service: Optional[PageService] = None


def get_page_service() -> PageService:
    """
    获取全局页面服务实例
    
    Returns:
        PageService: 页面服务实例
    """
    global _page_service
    if _page_service is None:
        _page_service = PageService()
    return _page_service


# 便捷函数
def get_all_pages() -> List[Dict[str, Any]]:
    """
    便捷函数：获取所有页面配置
    
    Returns:
        页面配置列表
    """
    return get_page_service().get_all_pages()


def get_page_by_id(page_id: str) -> Optional[Dict[str, Any]]:
    """
    便捷函数：根据ID获取页面配置
    
    Args:
        page_id: 页面ID
        
    Returns:
        页面配置或None
    """
    return get_page_service().get_page_by_id(page_id)


def get_ranking_channels() -> List[Dict[str, str]]:
    """
    便捷函数：获取所有排行榜频道
    
    Returns:
        频道信息列表
    """
    return get_page_service().get_ranking_channels()