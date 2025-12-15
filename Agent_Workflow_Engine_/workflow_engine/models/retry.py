"""
RetryPolicy 模型定义。

设计原因：
- 封装重试策略，便于配置和使用
- 支持 Max Retry、Retry Delay、Retry Condition
- 使用状态记录，不阻塞线程
- 简单易用，符合 KISS 原则
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Tuple, Type


@dataclass
class RetryPolicy:
    """重试策略。

    设计原因：
    - 配置重试参数
    - 职责单一
    - 简单易懂
    """
    max_retries: int = 3
    delay_seconds: float = 1.0
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    retry_condition: Optional[Callable[[Exception, int], bool]] = None

    def should_retry(self, exception: Exception, retry_count: int) -> bool:
        """判断是否应该重试。

        Args:
            exception: 发生的异常
            retry_count: 已重试的次数

        Returns:
            bool: 是否应该重试
        """
        # 检查重试次数
        if retry_count >= self.max_retries:
            return False

        # 检查异常类型
        if not isinstance(exception, self.retryable_exceptions):
            return False

        # 检查自定义条件
        if self.retry_condition is not None:
            return self.retry_condition(exception, retry_count)

        return True

    def get_delay(self, retry_count: int) -> float:
        """获取重试延迟时间（秒）。

        设计原因：
        - 简单的线性延迟
        - 可扩展（未来可以加指数退避）

        Args:
            retry_count: 已重试的次数

        Returns:
            float: 延迟时间
        """
        return self.delay_seconds


@dataclass
class RetryState:
    """重试状态记录。

    设计原因：
    - 使用状态记录，不阻塞线程
    - 记录重试信息
    - 简单的数据结构
    """
    node_id: str
    retry_count: int = 0
    last_exception: Optional[Exception] = None
    last_error_message: Optional[str] = None
    scheduled_retry_time: Optional[datetime] = None
    is_retrying: bool = False

    def can_retry(self, retry_policy: RetryPolicy) -> bool:
        """检查是否可以重试。

        Args:
            retry_policy: 重试策略

        Returns:
            bool: 是否可以重试
        """
        if self.last_exception is None:
            return False

        return retry_policy.should_retry(self.last_exception, self.retry_count)

    def should_execute_now(self) -> bool:
        """检查是否应该现在执行重试。

        Returns:
            bool: 是否应该执行
        """
        if not self.is_retrying:
            return False

        if self.scheduled_retry_time is None:
            return True

        return datetime.now() >= self.scheduled_retry_time

    def mark_for_retry(self, exception: Exception, retry_policy: RetryPolicy):
        """标记需要重试。

        Args:
            exception: 发生的异常
            retry_policy: 重试策略
        """
        self.last_exception = exception
        self.last_error_message = str(exception)
        self.is_retrying = True
        self.scheduled_retry_time = datetime.now() + timedelta(
            seconds=retry_policy.get_delay(self.retry_count)
        )

    def increment_retry(self):
        """增加重试计数。"""
        self.retry_count += 1
        self.is_retrying = False
        self.scheduled_retry_time = None

    def reset(self):
        """重置状态。"""
        self.retry_count = 0
        self.last_exception = None
        self.last_error_message = None
        self.scheduled_retry_time = None
        self.is_retrying = False
