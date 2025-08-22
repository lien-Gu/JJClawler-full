#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
熔断器模块 - 全局503错误熔断机制

提供全局状态管理，当检测到503错误时触发熔断，
影响所有爬取任务的行为，实现智能的反压保护。

Author: Claude
Date: 2025/8/20
"""

import asyncio
import time
from enum import Enum
from typing import Optional
from dataclasses import dataclass

from app.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常状态，允许请求
    OPEN = "open"  # 熔断状态，拒绝请求
    HALF_OPEN = "half_open"  # 半开状态，部分允许请求


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    # 熔断触发配置
    failure_threshold: int = 1  # 失败次数阈值（503错误1次即触发）
    base_recovery_timeout: float = 10.0  # 基础熔断恢复时间（秒）
    max_recovery_timeout: float = 300.0  # 最大恢复时间（秒）
    backoff_multiplier: float = 2.0  # 指数退避倍数

    # 半开状态配置
    half_open_max_calls: int = 3  # 半开状态最大测试请求数
    half_open_success_threshold: int = 2  # 半开状态成功次数阈值

    # 监控配置
    window_size: int = 60  # 监控窗口大小（秒）
    reset_timeout: float = 300.0  # 完全重置超时时间（秒）


class CircuitBreaker:
    """
    全局熔断器 - 503错误检测和反压保护
    
    特性：
    - 全局状态管理，一个任务的503失败影响所有任务
    - 自动恢复机制，通过半开状态逐步恢复
    - 详细的状态转换日志记录
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """初始化熔断器"""
        self.config = config or CircuitBreakerConfig()

        # 状态管理
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state_changed_time = time.time()

        # 半开状态统计
        self._half_open_attempts = 0
        self._half_open_successes = 0

        # 全局锁保证状态更新的原子性
        self._lock = asyncio.Lock()

        logger.info(f"熔断器初始化完成 - 状态: {self._state.value}, 配置: {self.config}")

    def _get_current_recovery_timeout(self) -> float:
        """计算当前恢复超时时间（指数退避）"""
        if self._failure_count <= 1:
            return self.config.base_recovery_timeout

        # 指数退避：base_timeout * (multiplier ^ (failure_count - 1))
        timeout = self.config.base_recovery_timeout * (
                self.config.backoff_multiplier ** (self._failure_count - 1)
        )

        # 限制最大超时时间
        return min(timeout, self.config.max_recovery_timeout)

    async def ensure_ready_for_request(self):
        """
        确保熔断器准备好处理请求
        
        检查熔断器状态，如果开启则等待恢复，如果半开状态则检查请求限制
        """
        await self._update_state_if_needed()

        if self.is_open:
            await self._wait_for_open_state_recovery()
        elif self._state == CircuitState.HALF_OPEN:
            await self._check_half_open_request_limit()

    async def _wait_for_open_state_recovery(self):
        """等待开启状态的熔断器恢复"""
        stats = self.get_stats()
        remaining_time = stats.get('remaining_recovery_time', 0)

        if remaining_time > 0.1:  # 如果剩余时间很少，直接跳过等待
            logger.warning(f"熔断器开启中，等待 {remaining_time:.1f} 秒后恢复...")
            await asyncio.sleep(remaining_time)
            await self._update_state_if_needed()

        # 检查等待后的状态
        if self.is_open:
            remaining = self.get_stats().get('remaining_recovery_time', 0)
            logger.error(f"熔断器等待后仍未恢复，剩余时间: {remaining:.1f}秒")
            raise CircuitBreakerOpenException(f"熔断器开启中，剩余恢复时间: {remaining:.1f}秒")
        else:
            logger.info("熔断器已恢复，继续执行HTTP请求")

    async def _check_half_open_request_limit(self):
        """检查半开状态下的请求数量限制"""
        async with self._lock:
            if self._half_open_attempts >= self.config.half_open_max_calls:
                logger.warning(f"半开状态已达到最大请求数量限制({self.config.half_open_max_calls})")
                raise CircuitBreakerOpenException("半开状态请求数量已达上限，等待状态转换")
            self._half_open_attempts += 1
            logger.info(f"半开状态请求计数: {self._half_open_attempts}/{self.config.half_open_max_calls}")

    async def _update_state_if_needed(self):
        """根据时间条件更新熔断器状态"""
        async with self._lock:
            await self._check_state_transition()

    async def record_service_error(self):
        """
        记录服务错误（如503错误）并评估是否需要触发熔断
        """
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            logger.error(f"记录服务错误 - 失败计数: {self._failure_count}/{self.config.failure_threshold}")

            # 检查是否需要触发熔断
            if self._should_trip_circuit():
                await self._transition_to_open()

    def _should_trip_circuit(self) -> bool:
        """判断是否应该触发熔断"""
        if self._state == CircuitState.CLOSED:
            return self._failure_count >= self.config.failure_threshold
        elif self._state == CircuitState.HALF_OPEN:
            return True  # 半开状态下任何错误都触发熔断
        return False

    async def record_success(self):
        """记录成功调用并评估是否可以关闭熔断器"""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                await self._handle_half_open_success()
            elif self._state == CircuitState.CLOSED:
                await self._handle_closed_success()

    async def _handle_half_open_success(self):
        """处理半开状态下的成功请求"""
        self._half_open_successes += 1
        logger.info(f"半开状态成功请求: {self._half_open_successes}/{self.config.half_open_success_threshold}")

        if self._half_open_successes >= self.config.half_open_success_threshold:
            await self._transition_to_closed()

    async def _handle_closed_success(self):
        """处理正常状态下的成功请求"""
        if self._failure_count > 0:
            logger.info(f"请求成功，重置失败计数 {self._failure_count} -> 0")
            self._failure_count = 0
            self._last_failure_time = None

    async def _check_state_transition(self):
        """检查状态转换"""
        current_time = time.time()

        if self._state == CircuitState.OPEN:
            # 检查是否可以转换到半开状态（使用指数退避时间）
            time_since_open = current_time - self._state_changed_time
            recovery_timeout = self._get_current_recovery_timeout()
            if time_since_open >= recovery_timeout:
                await self._transition_to_half_open()

        elif self._state == CircuitState.CLOSED:
            # 检查失败计数是否需要重置（超时重置）
            if (self._last_failure_time and
                    current_time - self._last_failure_time >= self.config.reset_timeout):
                if self._failure_count > 0:
                    logger.info(f"失败计数超时重置: {self._failure_count} -> 0")
                    self._failure_count = 0
                    self._last_failure_time = None

    async def _transition_to_open(self):
        """转换到熔断状态"""
        if self._state != CircuitState.OPEN:
            self._state = CircuitState.OPEN
            self._state_changed_time = time.time()

            # 使用指数退避计算恢复时间
            recovery_timeout = self._get_current_recovery_timeout()
            recovery_time = time.strftime(
                '%H:%M:%S',
                time.localtime(self._state_changed_time + recovery_timeout)
            )

            logger.error(
                f"熔断器开启! 失败次数: {self._failure_count}, "
                f"将在 {recovery_timeout} 秒后尝试恢复 (预计 {recovery_time})"
            )

    async def _transition_to_half_open(self):
        """转换到半开状态"""
        self._state = CircuitState.HALF_OPEN
        self._state_changed_time = time.time()
        self._half_open_attempts = 0
        self._half_open_successes = 0

        logger.warning(
            f"熔断器进入半开状态 - 将尝试 {self.config.half_open_max_calls} 次请求测试恢复"
            f" (失败次数: {self._failure_count})"
        )

    async def _transition_to_closed(self):
        """转换到关闭状态（正常状态）"""
        self._state = CircuitState.CLOSED
        self._state_changed_time = time.time()
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_attempts = 0
        self._half_open_successes = 0

        logger.info("熔断器恢复正常状态 - 所有请求已允许")

    @staticmethod
    def _is_503_error(exception: Exception) -> bool:
        """检查是否是服务器错误"""
        # 检查httpx的HTTPStatusError
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            return 500 <= exception.response.status_code < 600

        # 检查错误消息中是否包含503
        error_msg = str(exception).lower()
        return '503' in error_msg or 'service unavailable' in error_msg

    def _get_remaining_recovery_time(self) -> float:
        """获取剩余恢复时间（使用指数退避）"""
        if self._state != CircuitState.OPEN:
            return 0.0

        elapsed = time.time() - self._state_changed_time
        recovery_timeout = self._get_current_recovery_timeout()
        remaining = max(0, recovery_timeout - elapsed)
        return remaining

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        return self._state

    @property
    def is_open(self) -> bool:
        """熔断器是否开启"""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """熔断器是否关闭（正常状态）"""
        return self._state == CircuitState.CLOSED

    def get_stats(self) -> dict:
        """获取熔断器统计信息"""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "state_changed_time": self._state_changed_time,
            "last_failure_time": self._last_failure_time,
            "remaining_recovery_time": self._get_remaining_recovery_time(),
            "half_open_attempts": self._half_open_attempts,
            "half_open_successes": self._half_open_successes,
        }


class CircuitBreakerOpenException(Exception):
    """熔断器开启异常"""
    pass


# 全局熔断器实例
_global_circuit_breaker: Optional[CircuitBreaker] = None
_circuit_breaker_lock = asyncio.Lock()


async def get_global_circuit_breaker() -> CircuitBreaker:
    """获取全局熔断器实例"""
    global _global_circuit_breaker

    if _global_circuit_breaker is None:
        async with _circuit_breaker_lock:
            if _global_circuit_breaker is None:
                _global_circuit_breaker = CircuitBreaker()

    return _global_circuit_breaker


# 全局熔断器接口 - 提供统一的外部访问点
async def is_circuit_breaker_open() -> bool:
    """检查全局熔断器是否开启"""
    circuit_breaker = await get_global_circuit_breaker()
    return circuit_breaker.is_open


async def report_service_error():
    """向全局熔断器报告服务错误（如503错误）"""
    circuit_breaker = await get_global_circuit_breaker()
    await circuit_breaker.record_service_error()


async def report_request_success():
    """向全局熔断器报告请求成功"""
    circuit_breaker = await get_global_circuit_breaker()
    await circuit_breaker.record_success()


async def get_circuit_breaker_stats() -> dict:
    """获取全局熔断器统计信息"""
    circuit_breaker = await get_global_circuit_breaker()
    return circuit_breaker.get_stats()


async def prepare_for_request():
    """准备执行HTTP请求（检查熔断器状态，等待恢复如有需要）"""
    circuit_breaker = await get_global_circuit_breaker()
    await circuit_breaker.ensure_ready_for_request()
