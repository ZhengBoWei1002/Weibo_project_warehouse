# Agent Workflow Engine - Public API Design

## 目录
1. [State](#1-state)
2. [Action](#2-action)
3. [RetryPolicy](#3-retrypolicy)
4. [Checkpoint](#4-checkpoint)
5. [Context](#5-context)
6. [NodeResult](#6-noderesult)
7. [WorkflowResult](#7-workflowresult)
8. [Edge](#8-edge)
9. [Router](#9-router)
10. [Node](#10-node)
11. [Workflow](#11-workflow)

---

## 1. State

### 枚举定义
```python
from enum import Enum

class WorkflowState(Enum):
    """Workflow 的状态"""
    IDLE = "idle"           # 初始状态，尚未运行
    RUNNING = "running"     # 正在执行
    PAUSED = "paused"       # 已暂停
    COMPLETED = "completed" # 成功完成
    FAILED = "failed"       # 执行失败
    CANCELLED = "cancelled" # 已取消

class NodeStatus(Enum):
    """Node 的状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 成功完成
    FAILED = "failed"         # 执行失败
    RETRYING = "retrying"     # 重试中
    SKIPPED = "skipped"       # 已跳过
```

### 生命周期
- **WorkflowState**: IDLE → RUNNING → [COMPLETED | FAILED | CANCELLED | PAUSED]
  - PAUSED 可转换回 RUNNING
- **NodeStatus**: PENDING → RUNNING → [COMPLETED | FAILED | RETRYING | SKIPPED]
  - RETRYING 可转换回 RUNNING

---

## 2. Action

### 类定义
```python
from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum

class ActionType(Enum):
    """Action 的类型"""
    CONTINUE = "continue"     # 继续执行下一个节点
    END = "end"               # 结束 Workflow
    JUMP = "jump"             # 跳转到指定节点
    RETRY = "retry"           # 重试当前节点
    PAUSE = "pause"           # 暂停 Workflow
    FAIL = "fail"             # 标记为失败

@dataclass
class Action:
    """
    Node 执行结果的 Action，决定下一步行为
    """
    type: ActionType
    target_node_id: Optional[str] = None  # 仅 JUMP 时需要
    message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    # 工厂方法
    @classmethod
    def continue_(cls, message: Optional[str] = None) -> "Action":
        """创建 CONTINUE Action"""
        pass

    @classmethod
    def end(cls, message: Optional[str] = None) -> "Action":
        """创建 END Action"""
        pass

    @classmethod
    def jump(cls, target_node_id: str, message: Optional[str] = None) -> "Action":
        """创建 JUMP Action"""
        pass

    @classmethod
    def retry(cls, message: Optional[str] = None) -> "Action":
        """创建 RETRY Action"""
        pass

    @classmethod
    def pause(cls, message: Optional[str] = None) -> "Action":
        """创建 PAUSE Action"""
        pass

    @classmethod
    def fail(cls, message: Optional[str] = None) -> "Action":
        """创建 FAIL Action"""
        pass
```

### 生命周期
- 创建于 Node._run() 执行完成后
- 被 Workflow 解析以决定下一步行为
- 随 NodeResult 一起保存

---

## 3. RetryPolicy

### 类定义
```python
from dataclasses import dataclass
from typing import Callable, Optional, Type, Tuple
import time

@dataclass
class RetryPolicy:
    """
    重试策略配置
    """
    max_attempts: int = 3  # 最大重试次数（不包含首次执行）
    delay_seconds: float = 1.0  # 重试延迟（秒）
    backoff_factor: float = 2.0  # 退避因子（指数退避）
    max_delay_seconds: float = 30.0  # 最大延迟（秒）
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)  # 可重试的异常类型
    should_retry: Optional[Callable[[Exception, int], bool]] = None  # 自定义重试判断函数

    def calculate_delay(self, attempt: int) -> float:
        """
        计算第 attempt 次重试的延迟时间
        
        输入: attempt: int - 重试次数（从 0 开始）
        输出: float - 延迟秒数
        """
        pass

    def should_retry_exception(self, exception: Exception, attempt: int) -> bool:
        """
        判断是否应该重试
        
        输入:
            exception: Exception - 发生的异常
            attempt: int - 已重试次数
        输出: bool - 是否应该重试
        """
        pass
```

### 生命周期
- 在 Node 初始化时配置
- Node 执行失败时使用
- 可动态调整（可选）

---

## 4. Checkpoint

### 类定义
```python
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime

@dataclass
class Checkpoint:
    """
    检查点，用于保存和恢复 Workflow 状态
    """
    checkpoint_id: str
    workflow_id: str
    workflow_state: "WorkflowState"
    current_node_id: Optional[str]
    context_data: dict[str, Any]
    node_results: dict[str, "NodeResult"]
    created_at: datetime
    metadata: Optional[dict[str, Any]] = None

    @classmethod
    def create(
        cls,
        workflow_id: str,
        workflow_state: "WorkflowState",
        current_node_id: Optional[str],
        context_data: dict[str, Any],
        node_results: dict[str, "NodeResult"],
        metadata: Optional[dict[str, Any]] = None
    ) -> "Checkpoint":
        """
        创建检查点
        
        输入:
            workflow_id: str - Workflow ID
            workflow_state: WorkflowState - Workflow 状态
            current_node_id: Optional[str] - 当前节点 ID
            context_data: dict[str, Any] - Context 数据
            node_results: dict[str, NodeResult] - 节点执行结果
            metadata: Optional[dict[str, Any]] - 元数据
        输出: Checkpoint
        """
        pass
```

### 生命周期
- Workflow 执行过程中创建（每个关键节点后或手动触发）
- 可保存到持久化存储
- 用于从断点恢复 Workflow 执行

---

## 5. Context

### 5.1 WorkflowContext
```python
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

@dataclass
class WorkflowContext:
    """
    Workflow 级别的 Context，在所有 Node 之间共享
    """
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取数据
        
        输入:
            key: str - 键
            default: Any - 默认值
        输出: Any - 值
        """
        pass

    def set(self, key: str, value: Any) -> None:
        """
        设置数据
        
        输入:
            key: str - 键
            value: Any - 值
        输出: None
        """
        pass

    def update(self, data: dict[str, Any]) -> None:
        """
        批量更新数据
        
        输入: data: dict[str, Any] - 数据字典
        输出: None
        """
        pass

    def clear(self) -> None:
        """
        清空数据
        
        输入: 无
        输出: None
        """
        pass

    def copy(self) -> "WorkflowContext":
        """
        复制一份 Context
        
        输入: 无
        输出: WorkflowContext - 新的 Context
        """
        pass
```

### 5.2 NodeContext
```python
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

@dataclass
class NodeContext:
    """
    Node 级别的 Context
    """
    workflow_ctx: "WorkflowContext"
    node_id: str
    node_name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def workflow_data(self) -> dict[str, Any]:
        """
        快捷访问 WorkflowContext 的 data
        
        输入: 无
        输出: dict[str, Any]
        """
        pass

    def get_input(self, key: str, default: Any = None) -> Any:
        """
        获取输入
        
        输入:
            key: str - 键
            default: Any - 默认值
        输出: Any - 值
        """
        pass

    def set_output(self, key: str, value: Any) -> None:
        """
        设置输出
        
        输入:
            key: str - 键
            value: Any - 值
        输出: None
        """
        pass

    def get_workflow(self, key: str, default: Any = None) -> Any:
        """
        从 WorkflowContext 获取数据
        
        输入:
            key: str - 键
            default: Any - 默认值
        输出: Any - 值
        """
        pass

    def set_workflow(self, key: str, value: Any) -> None:
        """
        向 WorkflowContext 设置数据
        
        输入:
            key: str - 键
            value: Any - 值
        输出: None
        """
        pass
```

### Context 生命周期
- **WorkflowContext**:
  - Workflow 初始化时创建
  - 所有 Node 共享
  - Workflow 完成后可保留或销毁
- **NodeContext**:
  - 每个 Node 执行前创建
  - 包含当前 Node 的输入输出
  - Node 执行完成后随 NodeResult 保存

---

## 6. NodeResult

### 类定义
```python
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

@dataclass
class NodeResult:
    """
    Node 执行结果
    """
    node_id: str
    node_name: str
    status: "NodeStatus"
    output: Optional[Any] = None
    action: Optional["Action"] = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: Optional[dict[str, Any]] = None

    @classmethod
    def success(
        cls,
        node_id: str,
        node_name: str,
        output: Optional[Any] = None,
        action: Optional["Action"] = None,
        execution_time_seconds: float = 0.0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        outputs: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> "NodeResult":
        """
        创建成功的 NodeResult
        
        输入: 各字段
        输出: NodeResult
        """
        pass

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
        metadata: Optional[dict[str, Any]] = None
    ) -> "NodeResult":
        """
        创建失败的 NodeResult
        
        输入: 各字段
        输出: NodeResult
        """
        pass

    @property
    def is_success(self) -> bool:
        """
        是否成功
        
        输入: 无
        输出: bool
        """
        pass

    @property
    def is_failure(self) -> bool:
        """
        是否失败
        
        输入: 无
        输出: bool
        """
        pass
```

### 生命周期
- Node 开始执行时初始化
- Node 执行完成后填充
- 保存到 Workflow 的 node_results 中
- 参与 WorkflowResult 构建

---

## 7. WorkflowResult

### 类定义
```python
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

@dataclass
class WorkflowResult:
    """
    Workflow 执行结果
    """
    workflow_id: str
    workflow_name: str
    state: "WorkflowState"
    node_results: dict[str, "NodeResult"] = field(default_factory=dict)
    final_output: Optional[Any] = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    metadata: Optional[dict[str, Any]] = None

    @classmethod
    def success(
        cls,
        workflow_id: str,
        workflow_name: str,
        node_results: dict[str, "NodeResult"],
        final_output: Optional[Any] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> "WorkflowResult":
        """
        创建成功的 WorkflowResult
        
        输入: 各字段
        输出: WorkflowResult
        """
        pass

    @classmethod
    def failure(
        cls,
        workflow_id: str,
        workflow_name: str,
        node_results: dict[str, "NodeResult"],
        error: Exception,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> "WorkflowResult":
        """
        创建失败的 WorkflowResult
        
        输入: 各字段
        输出: WorkflowResult
        """
        pass

    @property
    def is_success(self) -> bool:
        """
        是否成功
        
        输入: 无
        输出: bool
        """
        pass

    @property
    def is_failure(self) -> bool:
        """
        是否失败
        
        输入: 无
        输出: bool
        """
        pass

    def get_node_result(self, node_id: str) -> Optional["NodeResult"]:
        """
        获取指定 Node 的结果
        
        输入: node_id: str
        输出: Optional[NodeResult]
        """
        pass
```

### 生命周期
- Workflow 开始时初始化
- Workflow 执行过程中更新
- Workflow 完成（或失败）时最终构建
- 返回给调用者

---

## 8. Edge

### 类定义
```python
from dataclasses import dataclass
from typing import Any, Optional, Callable

@dataclass
class Edge:
    """
    节点之间的边，定义节点跳转关系
    """
    from_node_id: str
    to_node_id: str
    condition: Optional[Callable[["NodeContext", "NodeResult"], bool]] = None
    name: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def evaluate(self, ctx: "NodeContext", result: "NodeResult") -> bool:
        """
        评估条件是否满足
        
        输入:
            ctx: NodeContext - 节点上下文
            result: NodeResult - 节点执行结果
        输出: bool - 是否满足条件
        """
        pass
```

### 生命周期
- Workflow 构建时添加
- Workflow 执行时用于路由
- 静态定义，执行过程中通常不变

---

## 9. Router

### 类定义
```python
from abc import ABC, abstractmethod
from typing import Optional

class Router(ABC):
    """
    路由器基类，决定从当前节点跳转到哪个节点
    """

    @abstractmethod
    def route(
        self,
        current_node_id: str,
        ctx: "NodeContext",
        result: "NodeResult",
        edges: list["Edge"]
    ) -> Optional[str]:
        """
        路由计算
        
        输入:
            current_node_id: str - 当前节点 ID
            ctx: NodeContext - 节点上下文
            result: NodeResult - 节点执行结果
            edges: list[Edge] - 可用的边
        输出: Optional[str] - 目标节点 ID，None 表示结束
        """
        pass

class DefaultRouter(Router):
    """
    默认路由器实现
    - 首先检查 NodeResult 中的 Action
    - 然后按顺序评估边的条件，返回第一个满足条件的
    - 否则返回 None（结束）
    """

    def route(
        self,
        current_node_id: str,
        ctx: "NodeContext",
        result: "NodeResult",
        edges: list["Edge"]
    ) -> Optional[str]:
        """
        路由计算
        
        输入: 同上
        输出: Optional[str]
        """
        pass
```

### 生命周期
- Workflow 初始化时设置（默认 DefaultRouter）
- 每次 Node 执行完成后调用
- 可自定义替换

---

## 10. Node

### 10.1 BaseNode（抽象基类）
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict
import time

@dataclass
class BaseNode(ABC):
    """
    Node 抽象基类
    """
    node_id: str
    name: str
    retry_policy: Optional["RetryPolicy"] = None
    metadata: Optional[Dict[str, Any]] = None

    # 生命周期钩子
    def prepare(self, ctx: "WorkflowContext") -> None:
        """
        执行前的准备工作
        
        输入: ctx: WorkflowContext
        输出: None
        """
        pass

    @abstractmethod
    def _run(self, ctx: "NodeContext") -> Any:
        """
        实际业务逻辑，子类必须实现
        
        输入: ctx: NodeContext
        输出: Any - 输出结果
        """
        pass

    def cleanup(self, ctx: "WorkflowContext") -> None:
        """
        执行后的清理工作
        
        输入: ctx: WorkflowContext
        输出: None
        """
        pass

    def get_next_action(self, ctx: "NodeContext", output: Any) -> "Action":
        """
        获取下一步 Action
        
        输入:
            ctx: NodeContext
            output: Any - _run 的输出
        输出: Action
        """
        pass

    def execute(self, ctx: "NodeContext") -> "NodeResult":
        """
        执行节点（模板方法）
        
        输入: ctx: NodeContext
        输出: NodeResult
        """
        pass

    # 重试相关（内部使用）
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        判断是否应该重试
        
        输入:
            exception: Exception
            attempt: int
        输出: bool
        """
        pass

    def _wait_for_retry(self, attempt: int) -> None:
        """
        等待重试
        
        输入: attempt: int
        输出: None
        """
        pass
```

### 10.2 内置 Node 类型

#### FunctionNode
```python
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class FunctionNode(BaseNode):
    """
    函数节点，包装一个函数
    """
    func: Callable[["NodeContext"], Any] = field(default_factory=lambda: lambda ctx: None)

    def _run(self, ctx: "NodeContext") -> Any:
        """
        执行函数
        
        输入: ctx: NodeContext
        输出: Any
        """
        pass
```

#### SequentialNode
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class SequentialNode(BaseNode):
    """
    顺序执行节点，依次执行多个子节点
    """
    nodes: List["BaseNode"] = field(default_factory=list)

    def _run(self, ctx: "NodeContext") -> Any:
        """
        顺序执行子节点
        
        输入: ctx: NodeContext
        输出: Any - 最后一个节点的输出
        """
        pass
```

#### ConditionalNode
```python
from dataclasses import dataclass, field
from typing import Dict, Callable, Any

@dataclass
class ConditionalNode(BaseNode):
    """
    条件节点，根据条件选择执行分支
    """
    condition_func: Callable[["NodeContext"], str]
    branches: Dict[str, "BaseNode"] = field(default_factory=dict)
    default_branch: Optional["BaseNode"] = None

    def _run(self, ctx: "NodeContext") -> Any:
        """
        根据条件选择分支执行
        
        输入: ctx: NodeContext
        输出: Any - 选中分支的输出
        """
        pass
```

#### LoopNode
```python
from dataclasses import dataclass
from typing import Callable, Any, Optional

@dataclass
class LoopNode(BaseNode):
    """
    循环节点，循环执行 body 直到条件不满足
    """
    body: "BaseNode"
    condition_func: Callable[["NodeContext", int], bool]  # (ctx, iteration) -> bool
    max_iterations: Optional[int] = None

    def _run(self, ctx: "NodeContext") -> Any:
        """
        循环执行
        
        输入: ctx: NodeContext
        输出: Any - 最后一次迭代的输出
        """
        pass
```

#### EndNode
```python
from dataclasses import dataclass
from typing import Any

@dataclass
class EndNode(BaseNode):
    """
    结束节点，结束 Workflow
    """
    output: Any = None

    def _run(self, ctx: "NodeContext") -> Any:
        """
        结束 Workflow
        
        输入: ctx: NodeContext
        输出: Any
        """
        pass

    def get_next_action(self, ctx: "NodeContext", output: Any) -> "Action":
        """
        返回 END Action
        
        输入: 同上
        输出: Action
        """
        pass
```

### Node 生命周期
1. **初始化**: 创建 Node 实例，配置参数
2. **准备**: Workflow 运行前调用 `prepare()`
3. **执行**:
   - 创建 NodeContext
   - 调用 `execute()`
   - `execute()` 内部调用 `_run()`
   - 处理异常和重试
4. **清理**: 调用 `cleanup()`
5. **完成**: 返回 NodeResult

---

## 11. Workflow

### 类定义
```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

@dataclass
class Workflow:
    """
    工作流主类
    """
    workflow_id: str
    name: str
    nodes: Dict[str, "BaseNode"] = field(default_factory=dict)
    edges: List["Edge"] = field(default_factory=list)
    start_node_id: Optional[str] = None
    end_node_ids: List[str] = field(default_factory=list)
    router: "Router" = field(default_factory=lambda: DefaultRouter())
    state: "WorkflowState" = WorkflowState.IDLE
    context: "WorkflowContext" = field(default_factory=lambda: WorkflowContext())
    node_results: Dict[str, "NodeResult"] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    # 构建方法
    def add_node(self, node: "BaseNode") -> "Workflow":
        """
        添加节点
        
        输入: node: BaseNode
        输出: Workflow - 支持链式调用
        """
        pass

    def add_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        condition: Optional[callable] = None,
        name: Optional[str] = None
    ) -> "Workflow":
        """
        添加边
        
        输入:
            from_node_id: str
            to_node_id: str
            condition: Optional[callable]
            name: Optional[str]
        输出: Workflow - 支持链式调用
        """
        pass

    def set_start(self, node_id: str) -> "Workflow":
        """
        设置起始节点
        
        输入: node_id: str
        输出: Workflow - 支持链式调用
        """
        pass

    def set_end(self, node_id: str) -> "Workflow":
        """
        设置结束节点（支持多个）
        
        输入: node_id: str
        输出: Workflow - 支持链式调用
        """
        pass

    def set_router(self, router: "Router") -> "Workflow":
        """
        设置路由器
        
        输入: router: Router
        输出: Workflow - 支持链式调用
        """
        pass

    # 执行方法
    def run(self, input_data: Optional[Dict[str, Any]] = None) -> "WorkflowResult":
        """
        运行 Workflow
        
        输入: input_data: Optional[Dict[str, Any]] - 初始输入数据
        输出: WorkflowResult
        """
        pass

    def run_from_checkpoint(self, checkpoint: "Checkpoint") -> "WorkflowResult":
        """
        从检查点恢复运行
        
        输入: checkpoint: Checkpoint
        输出: WorkflowResult
        """
        pass

    def pause(self) -> None:
        """
        暂停 Workflow
        
        输入: 无
        输出: None
        """
        pass

    def resume(self) -> "WorkflowResult":
        """
        恢复 Workflow
        
        输入: 无
        输出: WorkflowResult
        """
        pass

    def cancel(self) -> None:
        """
        取消 Workflow
        
        输入: 无
        输出: None
        """
        pass

    def reset(self) -> None:
        """
        重置 Workflow 状态（清除执行结果）
        
        输入: 无
        输出: None
        """
        pass

    # 检查点方法
    def create_checkpoint(self, metadata: Optional[Dict[str, Any]] = None) -> "Checkpoint":
        """
        创建检查点
        
        输入: metadata: Optional[Dict[str, Any]]
        输出: Checkpoint
        """
        pass

    # 生命周期钩子
    def on_start(self) -> None:
        """
        Workflow 开始前调用
        
        输入: 无
        输出: None
        """
        pass

    def on_node_start(self, node_id: str) -> None:
        """
        Node 开始前调用
        
        输入: node_id: str
        输出: None
        """
        pass

    def on_node_complete(self, node_id: str, result: "NodeResult") -> None:
        """
        Node 完成后调用
        
        输入:
            node_id: str
            result: NodeResult
        输出: None
        """
        pass

    def on_node_error(self, node_id: str, error: Exception) -> None:
        """
        Node 出错时调用
        
        输入:
            node_id: str
            error: Exception
        输出: None
        """
        pass

    def on_complete(self, result: "WorkflowResult") -> None:
        """
        Workflow 完成后调用
        
        输入: result: WorkflowResult
        输出: None
        """
        pass

    def on_error(self, error: Exception) -> None:
        """
        Workflow 出错时调用
        
        输入: error: Exception
        输出: None
        """
        pass

    def on_pause(self) -> None:
        """
        Workflow 暂停时调用
        
        输入: 无
        输出: None
        """
        pass

    def on_resume(self) -> None:
        """
        Workflow 恢复时调用
        
        输入: 无
        输出: None
        """
        pass

    def on_cancel(self) -> None:
        """
        Workflow 取消时调用
        
        输入: 无
        输出: None
        """
        pass

    # 内部方法
    def _validate(self) -> None:
        """
        验证 Workflow 配置
        
        输入: 无
        输出: None
        异常: ValidationError - 配置无效时
        """
        pass

    def _get_next_node_id(
        self,
        current_node_id: str,
        ctx: "NodeContext",
        result: "NodeResult"
    ) -> Optional[str]:
        """
        获取下一个节点 ID
        
        输入:
            current_node_id: str
            ctx: NodeContext
            result: NodeResult
        输出: Optional[str]
        """
        pass

    def _is_end_node(self, node_id: str) -> bool:
        """
        判断是否是结束节点
        
        输入: node_id: str
        输出: bool
        """
        pass
```

### Workflow 生命周期
1. **初始化**: 创建 Workflow 实例
2. **构建**:
   - `add_node()` - 添加节点
   - `add_edge()` - 添加边
   - `set_start()` - 设置起始节点
   - `set_end()` - 设置结束节点
   - `set_router()` - 设置路由器（可选）
3. **验证**: `_validate()` 检查配置
4. **运行**:
   - `run()` - 从开始运行
   - 或 `run_from_checkpoint()` - 从检查点恢复
5. **执行过程**:
   - `on_start()` - 开始钩子
   - 循环执行节点:
     - `on_node_start()` - 节点开始钩子
     - 执行 Node.execute()
     - `on_node_complete()` - 节点完成钩子
     - 路由到下一个节点
   - 支持暂停/恢复/取消
6. **完成**:
   - `on_complete()` 或 `on_error()`
   - 返回 WorkflowResult

---

## 总结

以上是 Agent Workflow Engine 的完整公共 API 设计，包含：
- 完整的类型标注
- 清晰的属性和方法定义
- 生命周期说明
- 输入输出定义
