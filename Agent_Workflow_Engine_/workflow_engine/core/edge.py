"""
节点边定义，用于描述节点之间的跳转关系。

设计原因：
- 显式定义节点之间的关系，而不是隐式依赖
- 支持条件跳转，让 Workflow 更灵活
- 简单的数据结构，易于理解和使用
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from workflow_engine.models.context import NodeContext
from workflow_engine.models.result import NodeResult


@dataclass
class Edge:
    """节点之间的边，定义节点跳转关系。

    设计原因：
    - 使用 dataclass 定义简单明了
    - 支持可选的条件函数，实现条件跳转
    - 包含元数据，便于扩展
    """
    from_node_id: str
    to_node_id: str
    condition: Optional[Callable[[NodeContext, NodeResult], bool]] = None
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def evaluate(self, ctx: NodeContext, result: NodeResult) -> bool:
        """评估条件是否满足。

        Args:
            ctx: Node 上下文
            result: Node 执行结果

        Returns:
            True 表示条件满足，可以跳转；False 表示不满足
        """
        if self.condition is None:
            return True
        return self.condition(ctx, result)
