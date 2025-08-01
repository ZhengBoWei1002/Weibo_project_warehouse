"""
Workflow 运行器，负责执行 Workflow。

设计原因：
- 分离关注点：Workflow 负责管理，Runner 负责执行
- 职责单一：只负责执行逻辑
- Router 完全负责决定下一步，符合 SRP
- 支持暂停和取消，功能完整
- 支持重试逻辑，使用状态记录，不阻塞线程
- 支持 Checkpoint 自动保存和恢复
- 易于测试和扩展
"""

from datetime import datetime
from typing import Any, Dict, Optional, Set

from workflow_engine.core.router import Router, RouterDecision
from workflow_engine.core.workflow import Workflow
from workflow_engine.models.context import NodeContext, WorkflowContext
from workflow_engine.models.result import NodeResult, WorkflowResult
from workflow_engine.models.retry import RetryPolicy, RetryState
from workflow_engine.models.state import WorkflowState
from workflow_engine.models.checkpoint import (
    Checkpoint,
    CheckpointStorage,
    MemoryCheckpointStorage,
)


class WorkflowRunner:
    """Workflow 运行器。

    设计原因：
    - 将执行逻辑与 Workflow 分离
    - 职责单一：只负责执行
    - Router 完全负责路由决策
    - 支持暂停和取消
    - 支持重试
    - 支持 Checkpoint
    - 易于测试和扩展
    """

    def __init__(
        self,
        workflow: Workflow,
        checkpoint_storage: Optional[CheckpointStorage] = None,
        auto_save_checkpoint: bool = True,
    ):
        """初始化运行器。

        Args:
            workflow: Workflow 实例
            checkpoint_storage: Checkpoint 存储（可选，默认使用内存存储）
            auto_save_checkpoint: 是否每执行一个 Node 后自动保存（默认 True）
        """
        self.workflow = workflow
        self.checkpoint_storage = checkpoint_storage or MemoryCheckpointStorage()
        self.auto_save_checkpoint = auto_save_checkpoint
        self.retry_states: Dict[str, RetryState] = {}
        self.is_resuming = False  # 标记是否是从 checkpoint 恢复

    def run(self, input_data: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """运行 Workflow。

        Args:
            input_data: 初始输入数据

        Returns:
            Workflow 执行结果
        """
        self.is_resuming = False
        
        # 验证 Workflow 配置
        self.workflow.validate()

        # 重置状态
        self.workflow.reset()
        self.retry_states.clear()

        # 初始化 Context
        if input_data:
            self.workflow.context.update(input_data)

        # 执行
        return self._execute()

    def run_from_checkpoint(self, workflow_id: str) -> WorkflowResult:
        """从 Checkpoint 恢复并运行 Workflow。

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow 执行结果
        """
        self.is_resuming = True
        
        checkpoint = self.checkpoint_storage.load(workflow_id)
        if checkpoint is None:
            from workflow_engine.exceptions import WorkflowError
            raise WorkflowError(f"No checkpoint found for workflow {workflow_id}")

        # 验证 Workflow 配置
        self.workflow.validate()

        # 从 checkpoint 恢复状态
        self._restore_from_checkpoint(checkpoint)

        # 如果已经是结束状态，直接返回
        if checkpoint.state in (WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED):
            return self._result_from_checkpoint(checkpoint)

        # 继续执行
        return self._execute(resume_from=checkpoint.current_node_id)

    def _create_checkpoint(self, next_node_id: Optional[str] = None) -> Checkpoint:
        """创建当前状态的 Checkpoint。

        Args:
            next_node_id: 下一个应该执行的节点 ID（可选）
        """
        # 转换 node_results 为可序列化格式
        node_results_list = []
        for node_id, result in self.workflow.node_results.items():
            result_dict = {
                "node_id": result.node_id,
                "node_name": result.node_name,
                "status": result.status.value,
                "output": result.output,
                "error_message": result.error_message,
                "execution_time_seconds": result.execution_time_seconds,
                "started_at": result.started_at.isoformat() if result.started_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            }
            node_results_list.append(result_dict)

        # 转换 retry_states
        retry_states_dict = {}
        for node_id, state in self.retry_states.items():
            retry_states_dict[node_id] = {
                "node_id": state.node_id,
                "retry_count": state.retry_count,
                "last_error_message": state.last_error_message,
                "is_retrying": state.is_retrying,
            }

        # 确定保存的 current_node_id
        saved_node_id = next_node_id if next_node_id is not None else self.workflow.current_node_id

        return Checkpoint(
            workflow_id=self.workflow.workflow_id,
            workflow_name=self.workflow.name,
            state=self.workflow.state,
            current_node_id=saved_node_id,
            context_data=self.workflow.context.data,
            node_results=node_results_list,
            retry_states=retry_states_dict,
            started_at=self.workflow.started_at.isoformat() if self.workflow.started_at else None,
        )

    def _save_checkpoint(self, next_node_id: Optional[str] = None) -> None:
        """保存当前状态到 Checkpoint。

        Args:
            next_node_id: 下一个应该执行的节点 ID（可选）
        """
        checkpoint = self._create_checkpoint(next_node_id)
        self.checkpoint_storage.save(checkpoint)

    def _restore_from_checkpoint(self, checkpoint: Checkpoint) -> None:
        """从 Checkpoint 恢复状态。"""
        self.workflow.state = checkpoint.state
        self.workflow.current_node_id = checkpoint.current_node_id
        self.workflow.context.data = checkpoint.context_data

        if checkpoint.started_at:
            self.workflow.started_at = datetime.fromisoformat(checkpoint.started_at)

        # 简单恢复 node_results 记录（只恢复基本信息，完整对象无法完全从 JSON 恢复）
        # 恢复 retry_states
        self.retry_states.clear()
        for node_id, state_dict in checkpoint.retry_states.items():
            retry_state = RetryState(node_id=node_id)
            retry_state.retry_count = state_dict.get("retry_count", 0)
            retry_state.last_error_message = state_dict.get("last_error_message")
            retry_state.is_retrying = state_dict.get("is_retrying", False)
            self.retry_states[node_id] = retry_state

    def _result_from_checkpoint(self, checkpoint: Checkpoint) -> WorkflowResult:
        """从 Checkpoint 创建 WorkflowResult（对于已结束的 Workflow）。"""
        if checkpoint.state == WorkflowState.COMPLETED:
            final_output = checkpoint.node_results[-1]["output"] if checkpoint.node_results else None
            return WorkflowResult.success(
                workflow_id=checkpoint.workflow_id,
                workflow_name=checkpoint.workflow_name,
                node_results=self.workflow.node_results,
                final_output=final_output,
                started_at=datetime.fromisoformat(checkpoint.started_at) if checkpoint.started_at else None,
            )
        elif checkpoint.state == WorkflowState.FAILED:
            from workflow_engine.exceptions import WorkflowError
            return WorkflowResult.failure(
                workflow_id=checkpoint.workflow_id,
                workflow_name=checkpoint.workflow_name,
                node_results=self.workflow.node_results,
                error=WorkflowError("Workflow failed as per checkpoint"),
                started_at=datetime.fromisoformat(checkpoint.started_at) if checkpoint.started_at else None,
            )
        else:
            from workflow_engine.exceptions import WorkflowError
            return WorkflowResult.failure(
                workflow_id=checkpoint.workflow_id,
                workflow_name=checkpoint.workflow_name,
                node_results=self.workflow.node_results,
                error=WorkflowError(f"Workflow is in state {checkpoint.state}"),
                started_at=datetime.fromisoformat(checkpoint.started_at) if checkpoint.started_at else None,
            )

    def _execute(self, resume_from: Optional[str] = None) -> WorkflowResult:
        """执行 Workflow。

        Args:
            resume_from: 如果是恢复执行，则从指定节点开始

        Returns:
            Workflow 执行结果
        """
        from workflow_engine.exceptions import WorkflowError

        if resume_from is None:
            # 新的执行
            self.workflow.state = WorkflowState.RUNNING
            self.workflow.started_at = datetime.now()
            self.workflow.on_start()
            current_node_id = self.workflow.start_node_id
        else:
            # 恢复执行
            self.workflow.state = WorkflowState.RUNNING
            current_node_id = resume_from

        self.workflow.current_node_id = current_node_id
        final_output = None

        try:
            while current_node_id:
                # 检查是否取消
                if self.workflow.is_cancelled():
                    return self._handle_cancelled()

                # 检查是否暂停
                if self.workflow.is_paused():
                    self.workflow.state = WorkflowState.PAUSED
                    self.workflow.on_pause()

                    # 等待恢复
                    while self.workflow.is_paused() and not self.workflow.is_cancelled():
                        import time
                        time.sleep(0.1)

                    if self.workflow.is_cancelled():
                        return self._handle_cancelled()

                    self.workflow.state = WorkflowState.RUNNING
                    self.workflow.on_resume()

                # 检查是否有等待的重试
                retry_state = self.retry_states.get(current_node_id)
                if retry_state and retry_state.is_retrying:
                    if not retry_state.should_execute_now():
                        # 还没到重试时间，继续循环（不阻塞）
                        import time
                        time.sleep(0.01)
                        continue
                    # 执行重试
                    retry_state.increment_retry()

                # 如果是从 checkpoint 恢复且这个节点已经执行过了，直接跳到下一步
                if self.is_resuming and current_node_id in self.workflow.node_results:
                    existing_result = self.workflow.node_results[current_node_id]
                    final_output = existing_result.output
                    
                    # 让 Router 决策下一步
                    node = self.workflow.nodes[current_node_id]
                    node_ctx = NodeContext(
                        workflow_ctx=self.workflow.context,
                        node_id=current_node_id,
                        node_name=node.name
                    )
                    decision = self._get_router_decision(current_node_id, node_ctx, existing_result)
                    
                    if decision.should_end or decision.next_node_id is None:
                        break
                    
                    current_node_id = decision.next_node_id
                    self.workflow.current_node_id = current_node_id
                    continue

                # 获取节点
                node = self.workflow.nodes[current_node_id]

                # 调用节点开始钩子
                self.workflow.on_node_start(current_node_id)

                # 准备节点
                node.prepare(self.workflow.context)

                # 创建节点 Context
                node_ctx = NodeContext(
                    workflow_ctx=self.workflow.context,
                    node_id=current_node_id,
                    node_name=node.name
                )

                # 执行节点
                result = node.execute(node_ctx)

                # 清理节点
                node.cleanup(self.workflow.context)

                # 保存结果
                self.workflow.node_results[current_node_id] = result

                # 调用节点完成钩子
                self.workflow.on_node_complete(current_node_id, result)

                # 自动保存 Checkpoint
                if self.auto_save_checkpoint:
                    self._save_checkpoint()

                # 检查是否失败，尝试重试
                if result.is_failure:
                    if node.retry_policy and self._try_retry(current_node_id, result.error, node.retry_policy):
                        # 标记重试后继续当前循环
                        continue

                    # 无法重试，失败
                    self.workflow.on_node_error(current_node_id, result.error)
                    return self._handle_failure(result.error)

                # 成功，清除重试状态
                if current_node_id in self.retry_states:
                    self.retry_states[current_node_id].reset()

                # 更新最终输出
                final_output = result.output

                # 让 Router 完全负责决策下一步
                decision = self._get_router_decision(current_node_id, node_ctx, result)

                # 处理 Router 的决策
                if decision.should_fail:
                    from workflow_engine.exceptions import WorkflowError
                    error_msg = result.action.message if result.action else "Workflow failed as requested by router"
                    error = WorkflowError(error_msg)
                    return self._handle_failure(error)
                elif decision.should_pause:
                    self.workflow.pause()
                    continue  # 暂停后下一轮循环会处理
                elif decision.should_end:
                    break

                # 继续执行下一个节点
                current_node_id = decision.next_node_id
                self.workflow.current_node_id = current_node_id

            # 成功完成
            return self._handle_success(final_output)

        except Exception as e:
            self.workflow.on_error(e)
            return self._handle_failure(e)

    def _try_retry(
        self,
        node_id: str,
        exception: Exception,
        retry_policy: RetryPolicy
    ) -> bool:
        """尝试重试。

        设计原因：
        - 检查是否可以重试
        - 标记需要重试
        - 使用状态记录，不阻塞线程

        Args:
            node_id: 节点 ID
            exception: 发生的异常
            retry_policy: 重试策略

        Returns:
            bool: 是否标记为重试
        """
        retry_state = self.retry_states.get(node_id)
        if retry_state is None:
            retry_state = RetryState(node_id=node_id)
            self.retry_states[node_id] = retry_state
            retry_state.last_exception = exception
            retry_state.last_error_message = str(exception)

        if retry_state.can_retry(retry_policy):
            retry_state.mark_for_retry(exception, retry_policy)
            return True

        return False

    def _get_router_decision(
        self,
        current_node_id: str,
        node_ctx: NodeContext,
        node_result: NodeResult
    ) -> RouterDecision:
        """获取 Router 的决策。

        设计原因：
        - 将路由决策完全委托给 Router
        - Router 拥有所有所需的信息
        - 遵循职责单一原则 (SRP)

        Args:
            current_node_id: 当前节点 ID
            node_ctx: Node 上下文
            node_result: Node 执行结果

        Returns:
            RouterDecision 决策结果
        """
        return self.workflow.router.decide(
            current_node_id=current_node_id,
            workflow_ctx=self.workflow.context,
            node_ctx=node_ctx,
            node_result=node_result,
            all_edges=self.workflow.edges,
            end_node_ids=set(self.workflow.end_node_ids),
            current_workflow_state=self.workflow.state
        )

    def _handle_success(self, final_output: Any) -> WorkflowResult:
        """处理成功情况。

        Args:
            final_output: 最终输出

        Returns:
            Workflow 执行结果
        """
        self.workflow.state = WorkflowState.COMPLETED
        self.workflow.completed_at = datetime.now()

        result = WorkflowResult.success(
            workflow_id=self.workflow.workflow_id,
            workflow_name=self.workflow.name,
            node_results=self.workflow.node_results,
            final_output=final_output,
            started_at=self.workflow.started_at,
            completed_at=self.workflow.completed_at,
            metadata=self.workflow.metadata
        )

        self.workflow.on_complete(result)
        return result

    def _handle_failure(self, error: Exception) -> WorkflowResult:
        """处理失败情况。

        Args:
            error: 异常对象

        Returns:
            Workflow 执行结果
        """
        self.workflow.state = WorkflowState.FAILED
        self.workflow.completed_at = datetime.now()

        result = WorkflowResult.failure(
            workflow_id=self.workflow.workflow_id,
            workflow_name=self.workflow.name,
            node_results=self.workflow.node_results,
            error=error,
            started_at=self.workflow.started_at,
            completed_at=self.workflow.completed_at,
            metadata=self.workflow.metadata
        )

        self.workflow.on_complete(result)
        return result

    def _handle_cancelled(self) -> WorkflowResult:
        """处理取消情况。

        Returns:
            Workflow 执行结果
        """
        from workflow_engine.exceptions import WorkflowError

        self.workflow.state = WorkflowState.CANCELLED
        self.workflow.completed_at = datetime.now()
        self.workflow.on_cancel()

        error = WorkflowError("Workflow was cancelled")
        return WorkflowResult.failure(
            workflow_id=self.workflow.workflow_id,
            workflow_name=self.workflow.name,
            node_results=self.workflow.node_results,
            error=error,
            started_at=self.workflow.started_at,
            completed_at=self.workflow.completed_at,
            metadata=self.workflow.metadata
        )
