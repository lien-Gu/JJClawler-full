#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调度器管理工具脚本

提供调度器的启动、停止、状态查询等管理功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.logger import get_logger
from app.schedule import get_scheduler, start_scheduler, stop_scheduler


logger = get_logger(__name__)


async def start_scheduler_service():
    """启动调度器服务"""
    try:
        logger.info("正在启动调度器服务...")
        await start_scheduler()
        logger.info("调度器服务启动成功")
        return True
    except Exception as e:
        logger.error(f"启动调度器服务失败: {e}")
        return False


async def stop_scheduler_service():
    """停止调度器服务"""
    try:
        logger.info("正在停止调度器服务...")
        await stop_scheduler()
        logger.info("调度器服务停止成功")
        return True
    except Exception as e:
        logger.error(f"停止调度器服务失败: {e}")
        return False


async def get_scheduler_status():
    """获取调度器状态"""
    try:
        scheduler = get_scheduler()
        if scheduler.scheduler is None:
            logger.info("调度器状态: 未启动")
            return {"status": "stopped", "message": "调度器未启动"}
        
        status_info = await scheduler.get_scheduler_info()
        logger.info(f"调度器状态: {status_info['status']}")
        logger.info(f"运行时间: {status_info['run_time']}")
        logger.info(f"等待任务数: {len(status_info['job_wait'])}")
        logger.info(f"运行任务数: {len(status_info['job_running'])}")
        
        return status_info
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        return {"status": "error", "message": str(e)}


async def list_jobs():
    """列出所有任务"""
    try:
        scheduler = get_scheduler()
        if scheduler.scheduler is None:
            logger.info("调度器未启动")
            return
        
        logger.info("=== 任务列表 ===")
        for job_id, job_info in scheduler._job_store.items():
            status_str = f"{job_info.status[0].value}: {job_info.status[1]}" if job_info.status else "未知状态"
            logger.info(f"任务ID: {job_id}")
            logger.info(f"  类型: {job_info.handler}")
            logger.info(f"  状态: {status_str}")
            logger.info(f"  描述: {job_info.desc or '无描述'}")
            if job_info.page_ids:
                logger.info(f"  页面: {', '.join(job_info.page_ids)}")
            logger.info("")
            
    except Exception as e:
        logger.error(f"列出任务失败: {e}")


def print_usage():
    """打印使用说明"""
    print("""
调度器管理工具

使用方法:
    python scripts/tools.py <command>

命令:
    start       启动调度器服务
    stop        停止调度器服务
    status      查看调度器状态
    jobs        列出所有任务
    help        显示此帮助信息

示例:
    python scripts/tools.py start
    python scripts/tools.py status
    python scripts/tools.py jobs
    python scripts/tools.py stop
    """)


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        success = await start_scheduler_service()
        sys.exit(0 if success else 1)
        
    elif command == "stop":
        success = await stop_scheduler_service()
        sys.exit(0 if success else 1)
        
    elif command == "status":
        status = await get_scheduler_status()
        sys.exit(0 if status.get("status") != "error" else 1)
        
    elif command == "jobs":
        await list_jobs()
        sys.exit(0)
        
    elif command in ["help", "-h", "--help"]:
        print_usage()
        sys.exit(0)
        
    else:
        print(f"未知命令: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())