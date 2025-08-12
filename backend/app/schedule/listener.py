#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
# @Project : backend
# @File    : listener.py
# @Date    : 2025/8/3 12:40
# @Author  : Lien Gu
'''
from datetime import datetime

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.logger import get_logger


class JobListener:
    """简化的任务监听器 - 仅记录失败日志"""
    
    def __init__(self):
        """初始化监听器"""
        self.logger = get_logger(__name__)

    def listen_job_failure(self, event):
        """监听任务失败事件并记录详细日志"""
        try:
            job_id = event.job_id
            exception = event.exception
            error_msg = str(exception)
            exception_type = exception.__class__.__name__
            current_time = datetime.now()

            # 记录详细的失败日志
            self.logger.error(
                f"任务执行失败 - "
                f"任务ID: {job_id}, "
                f"时间: {current_time.isoformat()}, "
                f"错误类型: {exception_type}, "
                f"错误信息: {error_msg}, "
                f"异常详情: {repr(exception)}"
            )
            
            # 如果有traceback信息也记录
            if hasattr(event, 'traceback') and event.traceback:
                self.logger.error(f"任务 {job_id} 异常堆栈: {event.traceback}")
                
        except Exception as e:
            # 记录失败监听器本身的错误，但不影响任务执行
            self.logger.error(f"任务失败监听器处理异常: {e}")
            self.logger.error(f"原始失败事件: 任务ID={getattr(event, 'job_id', 'unknown')}")
