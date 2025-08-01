"""
Workflow 构建器，用于构建 Workflow 实例。

设计原因：
- 使用构建器模式，提供流畅的 API
- 将复杂的构建逻辑与 Workflow 类分离
- 支持链式调用，使用方便
- 职责单一：只负责构建 Workflow
"""

from typing import Any, Callable, Optional, Union, Tuple

from workflow_engine.core.edge import Edge
from workflow_engine.core.router import Router
from workflow_engine.core.workflow import Workflow
from workflow_engine.models.context import NodeContext
from workflow_engine.models.result import NodeResult
from workflow_engine.nodes.base import BaseNode


class WorkflowBuilder:
    """Workflow 构建器。

    设计原因：
    - 提供流畅的链式 API
    - 职责单一：只负责构建 Workflow
    - 使用方便，易于使用
    - 支持便捷方法如 add_conditional_edge
    """

    def __init__(self, workflow_id: str, name: str):
        """初始化构建器。

        Args:
            workflow_id: Workflow ID
            name: Workflow 名称
        """
        self._workflow_id = workflow_id
        self._name = name
        self._nodes: dict[str, BaseNode] = {}
        self._edges: list[Edge] = []
        self._start_node_id: Optional[str] = None
        self._end_node_ids: list[str] = []
        self._router: Optional[Router] = None
        self._metadata: Optional[dict[str, Any]] = None

    def add_node(self, node: BaseNode) -> "WorkflowBuilder":
        """添加节点。

        Args:
            node: Node 实例

        Returns:
            self，支持链式调用
        """
        self._nodes[node.node_id] = node
        return self

    def add_nodes(self, *nodes: BaseNode) -> "WorkflowBuilder":
        """批量添加节点。

        Args:
            *nodes: 多个 Node 实例

        Returns:
            self，支持链式调用
        """
        for node in nodes:
            self._nodes[node.node_id] = node
        return self

    def add_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        condition: Optional[Callable[[NodeContext, NodeResult], bool]] = None,
        name: Optional[str] = None
    ) -> "WorkflowBuilder":
        """添加边。

        Args:
            from_node_id: 源节点 ID
            to_node_id: 目标节点 ID
            condition: 条件函数 (ctx, result) -> bool
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
        self._edges.append(edge)
        return self

    def add_conditional_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        condition: Callable[[NodeContext, NodeResult], bool],
        name: Optional[str] = None
    ) -> "WorkflowBuilder":
        """添加条件边。

        功能与 add_edge 相同，但语义更明确，表示这是一个条件边。

        Args:
            from_node_id: 源节点 ID
            to_node_id: 目标节点 ID
            condition: 条件函数 (ctx, result) -> bool
            name: 边名称

        Returns:
            self，支持链式调用
        """
        return self.add_edge(from_node_id, to_node_id, condition, name)

    def add_default_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        name: Optional[str] = None
    ) -> "WorkflowBuilder":
        """添加默认边（无条件）。

        语义更明确，表示这是默认情况下走的边。

        Args:
            from_node_id: 源节点 ID
            to_node_id: 目标节点 ID
            name: 边名称

        Returns:
            self，支持链式调用
        """
        return self.add_edge(from_node_id, to_node_id, name=name)

    def add_edges(self, *edges: Tuple) -> "WorkflowBuilder":
        """批量添加边。

        Args:
            *edges: 边的元组，形式为：
                - (from_id, to_id)
                - (from_id, to_id, condition)
                - (from_id, to_id, condition, name)

        Returns:
            self，支持链式调用
        """
        for edge_data in edges:
            if len(edge_data) == 2:
                from_id, to_id = edge_data
                self.add_edge(from_id, to_id)
            elif len(edge_data) == 3:
                from_id, to_id, condition = edge_data
                self.add_edge(from_id, to_id, condition)
            elif len(edge_data) == 4:
                from_id, to_id, condition, name = edge_data
                self.add_edge(from_id, to_id, condition, name)
        return self

    def set_start(self, node_id: str) -> "WorkflowBuilder":
        """设置起始节点。

        Args:
            node_id: 起始节点 ID

        Returns:
            self，支持链式调用
        """
        self._start_node_id = node_id
        return self

    def set_end(self, node_id: str) -> "WorkflowBuilder":
        """设置结束节点。

        Args:
            node_id: 结束节点 ID

        Returns:
            self，支持链式调用
        """
        if node_id not in self._end_node_ids:
            self._end_node_ids.append(node_id)
        return self

    def set_ends(self, *node_ids: str) -> "WorkflowBuilder":
        """批量设置结束节点。

        Args:
            *node_ids: 多个结束节点 ID

        Returns:
            self，支持链式调用
        """
        for node_id in node_ids:
            self.set_end(node_id)
        return self

    def set_router(self, router: Router) -> "WorkflowBuilder":
        """设置路由器。

        Args:
            router: Router 实例

        Returns:
            self，支持链式调用
        """
        self._router = router
        return self

    def set_metadata(self, metadata: dict[str, Any]) -> "WorkflowBuilder":
        """设置元数据。

        Args:
            metadata: 元数据字典

        Returns:
            self，支持链式调用
        """
        self._metadata = metadata
        return self

    def set_metadata_item(self, key: str, value: Any) -> "WorkflowBuilder":
        """设置单个元数据项。

        Args:
            key: 键
            value: 值

        Returns:
            self，支持链式调用
        """
        if self._metadata is None:
            self._metadata = {}
        self._metadata[key] = value
        return self

    def build(self) -> Workflow:
        """构建 Workflow 实例。

        Returns:
            Workflow 实例
        """
        workflow = Workflow(
            workflow_id=self._workflow_id,
            name=self._name,
            nodes=self._nodes.copy(),
            edges=self._edges.copy(),
            start_node_id=self._start_node_id,
            end_node_ids=self._end_node_ids.copy(),
            metadata=self._metadata.copy() if self._metadata else None
        )

        if self._router:
            workflow.set_router(self._router)

        return workflow
