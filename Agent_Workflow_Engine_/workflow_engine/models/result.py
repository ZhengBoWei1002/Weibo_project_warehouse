"""
执行结果数据模型定义。

设计原因：
- 使用 dataclass 简化数据类定义
- 提供 success() 和 failure() 工厂方法，便于创建结果对象
- 包含完整的执行信息，便于调试和监控
- 支持 Action 以决定下一步行为
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from workflow_engine.models.action import Action
from workflow_engine.models.state import NodeStatus, WorkflowState


@dataclass
class NodeResult:
    """Node 执行结果。

    设计原因：
    - 包含完整的执行信息（状态、输出、错误、执行时间等）
    - 提供 is_success 和 is_failure 属性，方便判断执行结果
    - 使用工厂方法创建常用场景的结果
    - 支持 Action 以决定下一步行为（新增，保持向后兼容）
    """
    node_id: str
    node_name: str
    status: NodeStatus
    output: Optional[Any] = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    action: Optional[Action] = None
    """下一步动作指令（可选，保持向后兼容）。"""

    @classmethod
    def success(
        cls,
        node_id: str,
        node_name: str,
        output: Optional[Any] = None,
        execution_time_seconds: float = 0.0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        outputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        action: Optional[Action] = None
    ) -> "NodeResult":
        """创建成功的 NodeResult。

        Args:
            node_id: 节点 ID
            node_name: 节点名称
            output: 输出数据
            execution_time_seconds: 执行时间（秒）
            started_at: 开始时间
            completed_at: 完成时间
            outputs: 输出字典
            metadata: 元数据
            action: 下一步动作指令（可选）

        Returns:
            成功的 NodeResult 实例
        """
        return cls(
            node_id=node_id,
            node_name=node_name,
            status=NodeStatus.COMPLETED,
            output=output,
            execution_time_seconds=execution_time_seconds,
            started_at=started_at,
            completed_at=completed_at,
            outputs=outputs or {},
            metadata=metadata,
            action=action
        )

    @classmethod
    def failure(
        cls,
        node_id: str,
        node_name: str,
        error: Exception,
        execution_time_seconds: float = 0.0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        action: Optional[Action] = None
    ) -> "NodeResult":
        """创建失败的 NodeResult。

        Args:
            node_id: 节点 ID
            node_name: 节点名称
            error: 异常对象
            execution_time_seconds: 执行时间（秒）
            started_at: 开始时间
            completed_at: 完成时间
            retry_count: 重试次数
            metadata: 元数据
            action: 下一步动作指令（可选）

        Returns:
            失败的 NodeResult 实例
        """
        return cls(
            node_id=node_id,
            node_name=node_name,
            status=NodeStatus.FAILED,
            error=error,
            error_message=str(error),
            execution_time_seconds=execution_time_seconds,
            started_at=started_at,
            completed_at=completed_at,
            retry_count=retry_count,
            metadata=metadata,
            action=action
        )

    @property
    def is_success(self) -> bool:
        """是否成功。"""
        return self.status == NodeStatus.COMPLETED

    @property
    def is_failure(self) -> bool:
        """是否失败。"""
        return self.status == NodeStatus.FAILED


@dataclass
class WorkflowResult:
    """Workflow 执行结果。

    设计原因：
    - 包含完整的 Workflow 执行信息
    - 包含所有 Node 的执行结果
    - 提供便捷的属性和方法，便于使用
    """
    workflow_id: str
    workflow_name: str
    state: WorkflowState
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    final_output: Optional[Any] = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def success(
        cls,
        workflow_id: str,
        workflow_name: str,
        node_results: Dict[str, NodeResult],
        final_output: Optional[Any] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "WorkflowResult":
        """创建成功的 WorkflowResult。

        Args:
            workflow_id: Workflow ID
            workflow_name: Workflow 名称
            node_results: Node 执行结果字典
            final_output: 最终输出
            started_at: 开始时间
            completed_at: 完成时间
            metadata: 元数据

        Returns:
            成功的 WorkflowResult 实例
        """
        duration = 0.0
        if started_at and completed_at:
            duration = (completed_at - started_at).total_seconds()

        return cls(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            state=WorkflowState.COMPLETED,
            node_results=node_results,
            final_output=final_output,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            metadata=metadata
        )

    @classmethod
    def failure(
        cls,
        workflow_id: str,
        workflow_name: str,
        node_results: Dict[str, NodeResult],
        error: Exception,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "WorkflowResult":
        """创建失败的 WorkflowResult。

        Args:
            workflow_id: Workflow ID
            workflow_name: Workflow 名称
            node_results: Node 执行结果字典
            error: 异常对象
            started_at: 开始时间
            completed_at: 完成时间
            metadata: 元数据

        Returns:
            失败的 WorkflowResult 实例
        """
        duration = 0.0
        if started_at and completed_at:
            duration = (completed_at - started_at).total_seconds()

        return cls(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            state=WorkflowState.FAILED,
            node_results=node_results,
            error=error,
            error_message=str(error),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            metadata=metadata
        )

    @property
    def is_success(self) -> bool:
        """是否成功。"""
        return self.state == WorkflowState.COMPLETED

    @property
    def is_failure(self) -> bool:
        """是否失败。"""
        return self.state == WorkflowState.FAILED

    def get_node_result(self, node_id: str) -> Optional[NodeResult]:
        """获取指定 Node 的结果。

        Args:
            node_id: 节点 ID

        Returns:
            NodeResult 实例或 None
        """
        return self.node_results.get(node_id)
