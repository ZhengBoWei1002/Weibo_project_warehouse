"""
Node 抽象基类。

设计原因：
- 使用 ABC 定义 Node 接口，确保所有 Node 有一致的行为
- 模板方法模式：execute() 定义执行流程，_run() 由子类实现
- 生命周期钩子：prepare() 和 cleanup()，便于扩展
- 支持 Action 来决定下一步行为
- 支持 RetryPolicy 配置
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from workflow_engine.models.action import Action
from workflow_engine.models.context import NodeContext, WorkflowContext
from workflow_engine.models.result import NodeResult
from workflow_engine.models.retry import RetryPolicy
from workflow_engine.models.state import NodeStatus


@dataclass
class BaseNode(ABC):
    """Node 抽象基类。

    设计原因：
    - 使用 dataclass 简化属性定义
    - 职责单一：只负责执行自己的逻辑
    - 提供生命周期钩子，便于扩展
    - 支持 RetryPolicy 配置
    """
    node_id: str
    name: str
    metadata: Optional[Dict[str, Any]] = None
    retry_policy: Optional[RetryPolicy] = None

    def prepare(self, ctx: WorkflowContext) -> None:
        """执行前的准备工作。

        子类可以重写此方法来执行准备工作。

        Args:
            ctx: Workflow 上下文
        """
        pass

    @abstractmethod
    def _run(self, ctx: NodeContext) -> Any:
        """实际业务逻辑，子类必须实现。

        Args:
            ctx: Node 上下文

        Returns:
            执行结果
        """
        pass

    def cleanup(self, ctx: WorkflowContext) -> None:
        """执行后的清理工作。

        子类可以重写此方法来执行清理工作。

        Args:
            ctx: Workflow 上下文
        """
        pass

    def get_next_action(self, ctx: NodeContext, output: Any) -> Action:
        """获取下一步动作指令。

        设计原因：
        - 子类可以重写此方法来自定义行为
        - 默认返回 CONTINUE

        Args:
            ctx: Node 上下文
            output: _run 方法的输出

        Returns:
            动作指令
        """
        return Action.continue_()

    def execute(self, ctx: NodeContext) -> NodeResult:
        """执行节点（模板方法）。

        设计原因：
        - 模板方法模式，定义固定的执行流程
        - 统一处理异常和状态管理
        - 子类只需关注 _run() 方法
        - 支持 Action 来决定下一步行为

        Args:
            ctx: Node 上下文

        Returns:
            Node 执行结果
        """
        from datetime import datetime

        started_at = datetime.now()
        ctx.started_at = started_at

        try:
            # 调用子类的 _run 方法
            output = self._run(ctx)
            ctx.completed_at = datetime.now()
            execution_time = (ctx.completed_at - started_at).total_seconds()

            # 获取动作指令
            action = self.get_next_action(ctx, output)

            # 创建成功结果
            return NodeResult.success(
                node_id=self.node_id,
                node_name=self.name,
                output=output,
                execution_time_seconds=execution_time,
                started_at=started_at,
                completed_at=ctx.completed_at,
                outputs=ctx.outputs,
                metadata=self.metadata,
                action=action
            )
        except Exception as e:
            ctx.completed_at = datetime.now()
            execution_time = (ctx.completed_at - started_at).total_seconds()

            # 创建失败结果
            return NodeResult.failure(
                node_id=self.node_id,
                node_name=self.name,
                error=e,
                execution_time_seconds=execution_time,
                started_at=started_at,
                completed_at=ctx.completed_at,
                metadata=self.metadata
            )
