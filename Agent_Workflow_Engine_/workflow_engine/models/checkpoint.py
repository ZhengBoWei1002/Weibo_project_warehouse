"""
Checkpoint 模型定义。

设计原因：
- 保存 Workflow 执行状态
- 支持从检查点恢复
- 使用 JSON 格式，无需数据库
- 接口可扩展
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from workflow_engine.models.state import WorkflowState
from workflow_engine.models.retry import RetryState


@dataclass
class Checkpoint:
    """Workflow 执行检查点。

    设计原因：
    - 保存执行状态
    - 支持恢复
    - 可序列化
    - 可扩展
    """
    workflow_id: str
    workflow_name: str
    state: WorkflowState
    current_node_id: Optional[str]
    context_data: Dict[str, Any]
    node_results: List[Dict[str, Any]]
    retry_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    started_at: Optional[str] = None
    checkpoint_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于序列化。"""
        data = asdict(self)
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """从字典创建 Checkpoint。"""
        data = data.copy()
        data["state"] = WorkflowState(data["state"])
        return cls(**data)


class CheckpointStorage:
    """Checkpoint 存储接口。

    设计原因：
    - 抽象存储逻辑
    - 可扩展（支持文件、内存等）
    - 单一职责
    """

    def save(self, checkpoint: Checkpoint) -> None:
        """保存检查点。"""
        raise NotImplementedError()

    def load(self, workflow_id: str) -> Optional[Checkpoint]:
        """加载检查点。"""
        raise NotImplementedError()

    def delete(self, workflow_id: str) -> None:
        """删除检查点。"""
        raise NotImplementedError()

    def list(self) -> List[str]:
        """列出所有检查点的 workflow_id。"""
        raise NotImplementedError()


class MemoryCheckpointStorage(CheckpointStorage):
    """内存中的 Checkpoint 存储。

    设计原因：
    - 简单实现
    - 便于测试
    - 可作为参考实现
    """

    def __init__(self):
        self._storage: Dict[str, Checkpoint] = {}

    def save(self, checkpoint: Checkpoint) -> None:
        self._storage[checkpoint.workflow_id] = checkpoint

    def load(self, workflow_id: str) -> Optional[Checkpoint]:
        return self._storage.get(workflow_id)

    def delete(self, workflow_id: str) -> None:
        if workflow_id in self._storage:
            del self._storage[workflow_id]

    def list(self) -> List[str]:
        return list(self._storage.keys())


class JsonFileCheckpointStorage(CheckpointStorage):
    """JSON 文件 Checkpoint 存储。

    设计原因：
    - 使用 JSON 格式
    - 无需数据库
    - 持久化存储
    - 可扩展
    """

    def __init__(self, directory: str = "checkpoints"):
        self.directory = directory
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """确保目录存在。"""
        import os
        os.makedirs(self.directory, exist_ok=True)

    def _get_file_path(self, workflow_id: str) -> str:
        """获取文件路径。"""
        import os
        safe_id = workflow_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.directory, f"{safe_id}.json")

    def save(self, checkpoint: Checkpoint) -> None:
        import json
        file_path = self._get_file_path(checkpoint.workflow_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, workflow_id: str) -> Optional[Checkpoint]:
        import json
        file_path = self._get_file_path(workflow_id)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Checkpoint.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def delete(self, workflow_id: str) -> None:
        import os
        file_path = self._get_file_path(workflow_id)
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

    def list(self) -> List[str]:
        import os
        workflow_ids = []
        try:
            for filename in os.listdir(self.directory):
                if filename.endswith(".json"):
                    workflow_id = filename[:-5]
                    workflow_ids.append(workflow_id)
        except FileNotFoundError:
            pass
        return workflow_ids
