"""
路由器，决定从当前节点跳转到哪个节点。

设计原因：
- 将路由逻辑完全分离出来，职责单一 (SRP)
- 支持自定义路由器，易于扩展
- Router 全权负责根据 Action、State、Context 决定下一步
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Set

from workflow_engine.core.edge import Edge
from workflow_engine.models.action import Action, ActionType
from workflow_engine.models.context import NodeContext, WorkflowContext
from workflow_engine.models.result import NodeResult
from workflow_engine.models.state import WorkflowState


class RouterDecision:
    """路由器的决策结果。

    设计原因：
    - 明确路由器的输出，不只是返回 next_node_id
    - 可以包含更多信息，比如是否暂停、是否结束等
    """

    def __init__(
        self,
        next_node_id: Optional[str] = None,
        should_pause: bool = False,
        should_end: bool = False,
        should_fail: bool = False
    ):
        self.next_node_id = next_node_id
        self.should_pause = should_pause
        self.should_end = should_end
        self.should_fail = should_fail

    @classmethod
    def continue_to(cls, node_id: str) -> "RouterDecision":
        """继续到指定节点。"""
        return cls(next_node_id=node_id)

    @classmethod
    def end(cls) -> "RouterDecision":
        """结束。"""
        return cls(should_end=True)

    @classmethod
    def fail(cls) -> "RouterDecision":
        """失败。"""
        return cls(should_fail=True)

    @classmethod
    def pause(cls) -> "RouterDecision":
        """暂停。"""
        return cls(should_pause=True)


class Router(ABC):
    """路由器基类。

    设计原因：
    - 使用 ABC 定义接口，确保子类实现 decide 方法
    - 职责单一：只负责做出路由决策
    - Router 拥有所有决策信息：Action、State、Context、Edges
    """

    @abstractmethod
    def decide(
        self,
        current_node_id: str,
        workflow_ctx: WorkflowContext,
        node_ctx: NodeContext,
        node_result: NodeResult,
        all_edges: List[Edge],
        end_node_ids: Set[str],
        current_workflow_state: WorkflowState
    ) -> RouterDecision:
        """做出路由决策。

        Args:
            current_node_id: 当前节点 ID
            workflow_ctx: Workflow 上下文
            node_ctx: Node 上下文
            node_result: Node 执行结果
            all_edges: 所有可用的边列表
            end_node_ids: 结束节点 ID 集合
            current_workflow_state: 当前 Workflow 状态

        Returns:
            RouterDecision 决策结果
        """
        pass


class DefaultRouter(Router):
    """默认路由器。

    设计原因：
    - 完整实现路由逻辑
    - 处理优先级：Action > End Node > Edge Conditions
    - 简单明了，易于理解和维护
    """

    def decide(
        self,
        current_node_id: str,
        workflow_ctx: WorkflowContext,
        node_ctx: NodeContext,
        node_result: NodeResult,
        all_edges: List[Edge],
        end_node_ids: Set[str],
        current_workflow_state: WorkflowState
    ) -> RouterDecision:
        """做出路由决策。

        优先级：
        1. Action 最高优先级
        2. 检查是否是结束节点
        3. 检查边条件

        Args:
            current_node_id: 当前节点 ID
            workflow_ctx: Workflow 上下文
            node_ctx: Node 上下文
            node_result: Node 执行结果
            all_edges: 所有可用的边列表
            end_node_ids: 结束节点 ID 集合
            current_workflow_state: 当前 Workflow 状态

        Returns:
            RouterDecision 决策结果
        """
        # 1. 首先检查 Action（最高优先级）
        if node_result.action is not None:
            decision = self._handle_action(node_result.action)
            if decision is not None:
                return decision

        # 2. 检查是否是结束节点
        if current_node_id in end_node_ids:
            return RouterDecision.end()

        # 3. 检查边条件
        outgoing_edges = [edge for edge in all_edges if edge.from_node_id == current_node_id]
        for edge in outgoing_edges:
            if edge.evaluate(node_ctx, node_result):
                return RouterDecision.continue_to(edge.to_node_id)

        # 没有找到下一步，结束
        return RouterDecision.end()

    def _handle_action(self, action: Action) -> Optional[RouterDecision]:
        """处理 Action。

        Args:
            action: Node 返回的 Action

        Returns:
            RouterDecision 或 None（表示继续处理）
        """
        if action.type == ActionType.END:
            return RouterDecision.end()
        elif action.type == ActionType.FAIL:
            return RouterDecision.fail()
        elif action.type == ActionType.PAUSE:
            return RouterDecision.pause()
        elif action.type == ActionType.JUMP and action.target_node_id is not None:
            return RouterDecision.continue_to(action.target_node_id)
        elif action.type == ActionType.CONTINUE:
            return None  # 继续处理边

        return None
