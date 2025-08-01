"""
Workflow 类定义，负责编排和管理节点执行。

设计原因：
- 职责单一：只负责管理节点和状态，不负责具体执行逻辑
- 提供链式 API，使用方便
- 包含生命周期钩子，便于扩展
- 支持暂停和取消，功能完整
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from workflow_engine.core.edge import Edge
from workflow_engine.core.router import DefaultRouter, Router
from workflow_engine.exceptions import WorkflowConfigurationError
from workflow_engine.models.context import WorkflowContext
from workflow_engine.models.result import NodeResult, WorkflowResult
from workflow_engine.models.state import WorkflowState
from workflow_engine.nodes.base import BaseNode


@dataclass
class Workflow:
    """工作流主类。

    设计原因：
    - 使用 dataclass 简化属性定义
    - 分离构建逻辑和执行逻辑（执行逻辑在 WorkflowRunner）
    - 提供生命周期钩子，便于扩展
    - 支持暂停和取消，功能完整
    """
    workflow_id: str
    name: str
    nodes: Dict[str, BaseNode] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    start_node_id: Optional[str] = None
    end_node_ids: List[str] = field(default_factory=list)
    router: Router = field(default_factory=DefaultRouter)
    state: WorkflowState = WorkflowState.IDLE
    context: WorkflowContext = field(default_factory=WorkflowContext)
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    _paused: bool = field(default=False, repr=False)
    _cancelled: bool = field(default=False, repr=False)

    def add_node(self, node: BaseNode) -> "Workflow":
        """添加节点。

        Args:
            node: Node 实例

        Returns:
            self，支持链式调用
        """
        self.nodes[node.node_id] = node
        return self

    def add_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        condition: Optional[callable] = None,
        name: Optional[str] = None
    ) -> "Workflow":
        """添加边。

        Args:
            from_node_id: 源节点 ID
            to_node_id: 目标节点 ID
            condition: 条件函数
            name: 边名称

        Returns:
            self，支持链式调用
        """
        edge = Edge(
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            condition=condition,
            name=name
        )
        self.edges.append(edge)
        return self

    def set_start(self, node_id: str) -> "Workflow":
        """设置起始节点。

        Args:
            node_id: 起始节点 ID

        Returns:
            self，支持链式调用

        Raises:
            WorkflowConfigurationError: 节点不存在
        """
        if node_id not in self.nodes:
            raise WorkflowConfigurationError(f"Start node '{node_id}' not found")
        self.start_node_id = node_id
        return self

    def set_end(self, node_id: str) -> "Workflow":
        """设置结束节点（支持多个）。

        Args:
            node_id: 结束节点 ID

        Returns:
            self，支持链式调用

        Raises:
            WorkflowConfigurationError: 节点不存在
        """
        if node_id not in self.nodes:
            raise WorkflowConfigurationError(f"End node '{node_id}' not found")
        if node_id not in self.end_node_ids:
            self.end_node_ids.append(node_id)
        return self

    def set_router(self, router: Router) -> "Workflow":
        """设置路由器。

        Args:
            router: Router 实例

        Returns:
            self，支持链式调用
        """
        self.router = router
        return self

    def validate(self) -> None:
        """验证 Workflow 配置。

        Raises:
            WorkflowConfigurationError: 配置无效
        """
        # 检查是否有节点
        if not self.nodes:
            raise WorkflowConfigurationError("Workflow has no nodes")

        # 检查是否设置了起始节点
        if not self.start_node_id:
            raise WorkflowConfigurationError("Start node not set")

        # 检查起始节点是否存在
        if self.start_node_id not in self.nodes:
            raise WorkflowConfigurationError(f"Start node '{self.start_node_id}' not found")

        # 检查所有边的节点是否存在
        for edge in self.edges:
            if edge.from_node_id not in self.nodes:
                raise WorkflowConfigurationError(f"Edge from node '{edge.from_node_id}' not found")
            if edge.to_node_id not in self.nodes:
                raise WorkflowConfigurationError(f"Edge to node '{edge.to_node_id}' not found")

    def reset(self) -> None:
        """重置 Workflow 状态（清除执行结果）。"""
        self.state = WorkflowState.IDLE
        self.context = WorkflowContext()
        self.node_results = {}
        self.current_node_id = None
        self.started_at = None
        self.completed_at = None
        self._paused = False
        self._cancelled = False

    # 生命周期钩子
    def on_start(self) -> None:
        """Workflow 开始前调用。"""
        pass

    def on_node_start(self, node_id: str) -> None:
        """Node 开始前调用。

        Args:
            node_id: 节点 ID
        """
        pass

    def on_node_complete(self, node_id: str, result: NodeResult) -> None:
        """Node 完成后调用。

        Args:
            node_id: 节点 ID
            result: Node 执行结果
        """
        pass

    def on_node_error(self, node_id: str, error: Exception) -> None:
        """Node 出错时调用。

        Args:
            node_id: 节点 ID
            error: 异常对象
        """
        pass

    def on_complete(self, result: WorkflowResult) -> None:
        """Workflow 完成后调用。

        Args:
            result: Workflow 执行结果
        """
        pass

    def on_error(self, error: Exception) -> None:
        """Workflow 出错时调用。

        Args:
            error: 异常对象
        """
        pass

    def on_pause(self) -> None:
        """Workflow 暂停时调用。"""
        pass

    def on_resume(self) -> None:
        """Workflow 恢复时调用。"""
        pass

    def on_cancel(self) -> None:
        """Workflow 取消时调用。"""
        pass

    # 暂停/取消相关（实际执行在 WorkflowRunner）
    def pause(self) -> None:
        """请求暂停 Workflow。"""
        self._paused = True

    def resume(self) -> None:
        """请求恢复 Workflow。"""
        self._paused = False

    def cancel(self) -> None:
        """请求取消 Workflow。"""
        self._cancelled = True

    def is_paused(self) -> bool:
        """检查是否暂停。"""
        return self._paused

    def is_cancelled(self) -> bool:
        """检查是否取消。"""
        return self._cancelled

    def is_end_node(self, node_id: str) -> bool:
        """检查是否是结束节点。

        Args:
            node_id: 节点 ID

        Returns:
            True 表示是结束节点
        """
        return node_id in self.end_node_ids
