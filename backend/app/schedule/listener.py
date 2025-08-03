#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
# @Project : backend
# @File    : listener.py
# @Date    : 2025/8/3 12:40
# @Author  : Lien Gu
'''
from datetime import datetime

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED, EVENT_JOB_SUBMITTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.logger import get_logger
from app.models.schedule import (JobStatus)


class JobListener:
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.logger = get_logger(__name__)

    def listen_jobs(self, event):
        """任务事件监听器 - 分发到具体的事件处理函数"""
        job_id = event.job_id
        job = self.scheduler.get_job(job_id)
        if not job or not job.metadata:
            self.logger.error(f"任务 {job_id} 不存在或无metadata")
            return

        if event.code == EVENT_JOB_SUBMITTED:
            self._handle_job_submitted(job, event)
        elif event.code == EVENT_JOB_EXECUTED:
            self._handle_job_executed(job, event)
        elif event.code == EVENT_JOB_ERROR:
            self._handle_job_error(job, event)
        elif event.code == EVENT_JOB_MISSED:
            self._handle_job_missed(job, event)

    def _handle_job_submitted(self, job, event):
        """处理任务提交事件"""
        update_dict = job.metadata.copy()
        update_dict["status"] = JobStatus.RUNNING
        update_dict['execution_count'] = update_dict.get('execution_count', 0) + 1

        job.modify(metadata=update_dict)
        self.logger.info(f"任务 {job.id} 正在执行或者排队 (第{update_dict['execution_count']}次)")

    def _handle_job_executed(self, job, event):
        """处理任务执行成功事件"""
        update_dict = job.metadata.copy()
        current_time = datetime.now()

        update_dict["status"] = JobStatus.SUCCESS
        update_dict['success_count'] = update_dict.get('success_count', 0) + 1
        update_dict['last_execution_time'] = current_time.isoformat()

        # 存储任务执行结果
        execution_result = {
            'timestamp': current_time.isoformat(),
            'status': 'success',
            'result': getattr(event, 'retval', None),
            'duration': None  # 可以后续添加执行时间计算
        }

        # 更新执行结果历史(保留最近10次)
        execution_results = update_dict.get('execution_results', [])
        execution_results.append(execution_result)
        update_dict['execution_results'] = execution_results[-10:]
        update_dict['last_result'] = execution_result

        job.modify(metadata=update_dict)
        self.logger.info(f"任务 {job.id} 执行成功 (成功{update_dict['success_count']}次)")

    def _handle_job_error(self, job, event):
        """处理任务执行失败事件"""
        update_dict = job.metadata.copy()
        current_time = datetime.now()
        exception = event.exception
        error_msg = str(exception)

        update_dict["status"] = JobStatus.FAILED
        update_dict['last_execution_time'] = current_time.isoformat()

        # 存储失败信息
        failure_result = {
            'timestamp': current_time.isoformat(),
            'status': 'failed',
            'error': error_msg,
            'exception_type': exception.__class__.__name__
        }

        execution_results = update_dict.get('execution_results', [])
        execution_results.append(failure_result)
        update_dict['execution_results'] = execution_results[-10:]
        update_dict['last_result'] = failure_result

        # 计算失败次数: execution_count - success_count
        failure_count = update_dict.get('execution_count', 0) - update_dict.get('success_count', 0)

        job.modify(metadata=update_dict)
        self.logger.error(f"任务 {job.id} 执行失败 (失败{failure_count}次): {error_msg}")

    def _handle_job_missed(self, job, event):
        """处理任务错过执行事件"""
        update_dict = job.metadata.copy()
        current_time = datetime.now()

        update_dict["status"] = JobStatus.FAILED
        update_dict['last_execution_time'] = current_time.isoformat()

        # 存储错过执行的信息
        missed_result = {
            'timestamp': current_time.isoformat(),
            'status': 'missed',
            'error': '任务错过执行时间',
            'exception_type': 'MissedExecution'
        }

        execution_results = update_dict.get('execution_results', [])
        execution_results.append(missed_result)
        update_dict['execution_results'] = execution_results[-10:]
        update_dict['last_result'] = missed_result

        job.modify(metadata=update_dict)
        self.logger.warning(f"任务 {job.id} 错过执行时间")
