"""
状态枚举定义。

设计原因：
- 使用 Enum 确保状态安全，避免非法状态值
- 清晰的状态定义便于理解和调试
"""

from enum import Enum


class WorkflowState(Enum):
    """Workflow 的状态枚举。

    状态转移：
    IDLE -> RUNNING -> [COMPLETED | FAILED | CANCELLED | PAUSED]
    PAUSED -> RUNNING
    """
    IDLE = "idle"  # 初始状态，尚未运行
    RUNNING = "running"  # 正在执行
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 成功完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消


class NodeStatus(Enum):
    """Node 的状态枚举。

    状态转移：
    PENDING -> RUNNING -> [COMPLETED | FAILED | RETRYING | SKIPPED]
    RETRYING -> RUNNING
    """
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    COMPLETED = "completed"  # 成功完成
    FAILED = "failed"  # 执行失败
    RETRYING = "retrying"  # 重试中
    SKIPPED = "skipped"  # 已跳过
