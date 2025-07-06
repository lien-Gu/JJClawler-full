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
            self.params = self._config.get("global", {}).get("params", {})
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