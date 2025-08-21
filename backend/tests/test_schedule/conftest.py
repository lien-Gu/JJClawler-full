#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
# @Project : backend
# @File    : conftest.py
# @Date    : 2025/8/7 21:27
# @Author  : Lien Gu
'''
# ==================== 调度器测试数据 ====================
from datetime import datetime

import pytest


@pytest.fixture
def sample_job():
    """示例任务"""
    from app.models.schedule import Job, JobType
    from apscheduler.triggers.date import DateTrigger
    return Job(
        job_id="CRAWL_20250803_123456",
        job_type=JobType.CRAWL,
        trigger=DateTrigger(run_date=datetime.now()),
        desc="测试任务",
        page_ids=["jiazi"]
    )


@pytest.fixture
def sample_system_job():
    """示例系统任务"""
    from app.models.schedule import Job, JobType
    from apscheduler.triggers.date import DateTrigger
    return Job(
        job_id="__system_job_cleanup__",
        job_type=JobType.SYSTEM,
        trigger=DateTrigger(run_date=datetime.now()),
        desc="系统清理任务"
    )


@pytest.fixture
def sample_job_metadata():
    """示例任务元数据"""
    from app.models.schedule import JobStatus
    from datetime import timezone
    return {
        "job_id": "test_job",
        "job_type": "crawl",
        "desc": "测试任务",
        "page_ids": ["jiazi"],
        "status": JobStatus.PENDING.value,
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "is_system_job": False
    }


@pytest.fixture
def expired_job_metadata():
    """过期任务元数据"""
    from app.models.schedule import JobStatus
    from datetime import timezone, timedelta
    old_time = datetime.now(timezone.utc) - timedelta(days=10)
    return {
        "created_at": old_time.isoformat().replace('+00:00', 'Z'),
        "status": JobStatus.SUCCESS.value,
        "is_system_job": False
    }


@pytest.fixture
def system_job_metadata():
    """系统任务元数据"""
    from datetime import timezone, timedelta
    old_time = datetime.now(timezone.utc) - timedelta(days=10)
    return {
        "created_at": old_time.isoformat().replace('+00:00', 'Z'),
        "is_system_job": True
    }


@pytest.fixture
def recent_job_metadata():
    """最近任务元数据"""
    from app.models.schedule import JobStatus
    from datetime import timezone
    recent_time = datetime.now(timezone.utc)
    return {
        "created_at": recent_time.isoformat().replace('+00:00', 'Z'),
        "status": JobStatus.SUCCESS.value,
        "is_system_job": False
    }
