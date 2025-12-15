"""
上下文数据模型定义。

设计原因：
- 使用 dataclass 简化数据类定义，自动生成 __init__、__repr__ 等方法
- 分离 WorkflowContext 和 NodeContext，职责更清晰
- 提供便捷的访问方法，提高代码可读性
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class WorkflowContext:
    """Workflow 级别的 Context，在所有 Node 之间共享。

    设计原因：
    - 作为全局数据存储，让 Node 之间可以传递数据
    - 分离 data 和 metadata，数据和元数据职责清晰
    - 提供简单的 get/set/update 方法，使用方便
    """
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default: Any = None) -> Any:
        """获取数据。

        Args:
            key: 键名
            default: 默认值（键不存在时返回）

        Returns:
            对应的值或默认值
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置数据。

        Args:
            key: 键名
            value: 值
        """
        self.data[key] = value
        self.updated_at = datetime.now()

    def update(self, data: Dict[str, Any]) -> None:
        """批量更新数据。

        Args:
            data: 数据字典
        """
        self.data.update(data)
        self.updated_at = datetime.now()

    def clear(self) -> None:
        """清空数据。"""
        self.data.clear()
        self.updated_at = datetime.now()

    def copy(self) -> "WorkflowContext":
        """复制一份 Context。

        Returns:
            新的 WorkflowContext 实例
        """
        return WorkflowContext(
            data=self.data.copy(),
            metadata=self.metadata.copy(),
            created_at=self.created_at,
            updated_at=datetime.now()
        )


@dataclass
class NodeContext:
    """Node 级别的 Context，包含当前节点的局部数据。

    设计原因：
    - 每个 Node 有独立的 inputs/outputs，避免相互干扰
    - 保留对 WorkflowContext 的引用，可以访问全局数据
    - 提供便捷的访问方法，使用更简单
    """
    workflow_ctx: WorkflowContext
    node_id: str
    node_name: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def workflow_data(self) -> Dict[str, Any]:
        """快捷访问 WorkflowContext 的 data。"""
        return self.workflow_ctx.data

    def get_input(self, key: str, default: Any = None) -> Any:
        """获取输入。

        Args:
            key: 键名
            default: 默认值

        Returns:
            输入值或默认值
        """
        return self.inputs.get(key, default)

    def set_output(self, key: str, value: Any) -> None:
        """设置输出。

        Args:
            key: 键名
            value: 值
        """
        self.outputs[key] = value

    def get_workflow(self, key: str, default: Any = None) -> Any:
        """从 WorkflowContext 获取数据。

        Args:
            key: 键名
            default: 默认值

        Returns:
            全局数据值或默认值
        """
        return self.workflow_ctx.get(key, default)

    def set_workflow(self, key: str, value: Any) -> None:
        """向 WorkflowContext 设置数据。

        Args:
            key: 键名
            value: 值
        """
        self.workflow_ctx.set(key, value)
