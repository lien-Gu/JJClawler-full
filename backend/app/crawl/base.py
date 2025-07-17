"""
爬虫基础组件 - 简化版本
"""
import json
import asyncio
from typing import Dict, List, Optional
import httpx
from pathlib import Path


class CrawlConfig:
    """爬取配置类"""

    def __init__(self):
        self.urls_file = Path(__file__).parent.parent.parent / "data" / "urls.json"
        self._config = None
        self.params = None
        self.templates = None
        self._load_config()

    def _load_config(self):
        """加载URL配置文件"""
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            self.params = self._config.get("global", {}).get("base_params", {})
            self.templates = self._config.get("global", {}).get("templates", {})
        except Exception as e:
            raise Exception(f"配置文件加载失败: {e}")

    def get_task_config(self, task_id: str) -> Optional[Dict]:
        """获取特定任务的配置"""
        for task in self._config.get("crawl_tasks", []):
            if task["id"] == task_id:
                return task
        return None

    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务配置"""
        return self._config.get("crawl_tasks", [])
    
    def determine_page_ids(self, page_ids: List[str]) -> List[str]:
        """
        根据任务数据确定需要爬取的页面ID列表
        
        Args:
            page_ids: 任务数据
            
        Returns:
            List[str]: 页面ID列表
        """
        # 特殊字符任务类型
        if len(page_ids) == 1 and page_ids[0] in ["all", "jiazi", "category"]:
            special_word = page_ids[0]
            if special_word == "jiazi":
                # 夹子榜任务
                return ["jiazi"]
            elif special_word == "category":
                # 所有分类任务
                return self.get_category_page_ids()
            else:
                return self.get_all_page_ids()
        return [pid for pid in page_ids if self.validate_page_id(pid)]
    
    def get_category_page_ids(self) -> List[str]:
        """获取所有分类页面ID列表（排除夹子榜）"""
        all_tasks = self.get_all_tasks()
        category_ids = []
        
        for task in all_tasks:
            task_id = task.get('id', '')
            if not ('jiazi' in task_id.lower() or task.get('category') == 'jiazi'):
                category_ids.append(task_id)
        
        return category_ids
    
    def get_all_page_ids(self) -> List[str]:
        """获取所有页面ID"""
        all_tasks = self.get_all_tasks()
        return [task.get("id") for task in all_tasks if task.get("id")]
    
    def validate_page_id(self, page_id: str) -> bool:
        """验证页面ID是否在配置中"""
        all_tasks = self.get_all_tasks()
        available_ids = {task.get('id', '') for task in all_tasks}
        return page_id in available_ids

    def build_url(self, task_config: Dict) -> str:
        """根据任务配置构建URL"""
        template_name = task_config["template"]
        template = self.templates.get(template_name)
        
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        # 合并参数
        params = {**self.params, **task_config.get("params", {})}
        
        # 格式化URL
        return template.format(**params)


class HttpClient:
    """HTTP客户端"""
    
    def __init__(self, request_delay: float = 1.0):
        self.request_delay = request_delay
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
    
    async def get(self, url: str) -> Dict:
        """发送GET请求"""
        try:
            # 请求限速
            await asyncio.sleep(self.request_delay)
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise Exception(f"请求失败 {url}: {e}")
    
    async def close(self):
        """关闭连接"""
        await self.session.aclose()