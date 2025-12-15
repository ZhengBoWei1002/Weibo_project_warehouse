"""
Action 类定义。

设计原因：
- 明确节点执行后的行为指令
- 支持多种动作类型：继续、结束、跳转等
- 使用枚举确保类型安全
- 使用数据类简化实现
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ActionType(Enum):
    """Action 类型枚举。

    设计原因：
    - 限制合法的动作类型
    - 类型安全，避免拼写错误
    - 清晰的语义
    """

    CONTINUE = "continue"
    """继续执行下一个节点。"""

    END = "end"
    """结束 Workflow。"""

    JUMP = "jump"
    """跳转到指定节点。"""

    PAUSE = "pause"
    """暂停 Workflow。"""

    FAIL = "fail"
    """标记为失败并结束。"""


@dataclass
class Action:
    """Node 执行后的动作指令。

    设计原因：
    - 使用数据类存储动作信息
    - 提供工厂方法简化创建
    - 类型安全的枚举
    - 支持可选的消息和元数据
    """

    type: ActionType
    """动作类型。"""

    target_node_id: Optional[str] = None
    """目标节点 ID（仅用于 JUMP）。"""

    message: Optional[str] = None
    """可选的消息。"""

    metadata: Optional[dict[str, Any]] = field(default_factory=dict)
    """可选的元数据。"""

    @classmethod
    def continue_(cls, message: Optional[str] = None) -> "Action":
        """创建 CONTINUE 动作。

        Args:
            message: 可选的消息

        Returns:
            CONTINUE Action
        """
        return cls(type=ActionType.CONTINUE, message=message)

    @classmethod
    def end(cls, message: Optional[str] = None) -> "Action":
        """创建 END 动作。

        Args:
            message: 可选的消息

        Returns:
            END Action
        """
        return cls(type=ActionType.END, message=message)

    @classmethod
    def jump(
        cls,
        target_node_id: str,
        message: Optional[str] = None
    ) -> "Action":
        """创建 JUMP 动作。

        Args:
            target_node_id: 目标节点 ID
            message: 可选的消息

        Returns:
            JUMP Action
        """
        return cls(
            type=ActionType.JUMP,
            target_node_id=target_node_id,
            message=message
        )

    @classmethod
    def pause(cls, message: Optional[str] = None) -> "Action":
        """创建 PAUSE 动作。

        Args:
            message: 可选的消息

        Returns:
            PAUSE Action
        """
        return cls(type=ActionType.PAUSE, message=message)

    @classmethod
    def fail(cls, message: Optional[str] = None) -> "Action":
        """创建 FAIL 动作。

        Args:
            message: 可选的消息

        Returns:
            FAIL Action
        """
        return cls(type=ActionType.FAIL, message=message)
