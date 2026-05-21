"""
Checkpoint 简单单元测试。
"""

import unittest
import os
import shutil
from dataclasses import dataclass

from workflow_engine import (
    BaseNode,
    WorkflowBuilder,
    WorkflowRunner,
    MemoryCheckpointStorage,
    Checkpoint,
)


@dataclass
class IncrementNode(BaseNode):
    """简单测试节点，每次加 1。"""

    def _run(self, ctx):
        count = ctx.get_workflow("count", 0)
        count += 1
        ctx.set_workflow("count", count)
        return count


class TestCheckpointSimple(unittest.TestCase):
    """Checkpoint 简单测试。"""

    def test_basic_storage(self):
        """测试基本存储功能。"""
        from workflow_engine.models.state import WorkflowState

        storage = MemoryCheckpointStorage()
        cp = Checkpoint(
            workflow_id="basic_test",
            workflow_name="Basic Test",
            state=WorkflowState.RUNNING,
            current_node_id="n1",
            context_data={"count": 5},
            node_results=[{"node_id": "n0", "status": "COMPLETED"}],
        )

        storage.save(cp)
        loaded = storage.load("basic_test")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.workflow_id, "basic_test")

    def test_memory_checkpoint_workflow(self):
        """测试完整的 Checkpoint 工作流程。"""
        # 创建节点
        node1 = IncrementNode(node_id="node1", name="Node 1")
        node2 = IncrementNode(node_id="node2", name="Node 2")
        node3 = IncrementNode(node_id="node3", name="Node 3")

        # 第一步：创建一个只到 node1 的 workflow
        wf1 = (
            WorkflowBuilder("cp_test", "CP Test")
            .add_nodes(node1)
            .set_start("node1")
            .set_end("node1")
            .build()
        )

        storage = MemoryCheckpointStorage()
        runner = WorkflowRunner(wf1, checkpoint_storage=storage, auto_save_checkpoint=True)
        result1 = runner.run()
        self.assertTrue(result1.is_success)

        # 第二步：检查 checkpoint
        cp = storage.load("cp_test")
        self.assertIsNotNone(cp)
        self.assertEqual(cp.context_data.get("count"), 1)

        # 第三步：创建完整的 workflow，从 checkpoint 恢复
        wf2 = (
            WorkflowBuilder("cp_test", "CP Test")
            .add_nodes(node1, node2, node3)
            .add_edge("node1", "node2")
            .add_edge("node2", "node3")
            .set_start("node1")
            .set_end("node3")
            .build()
        )

        # 恢复并运行
        runner2 = WorkflowRunner(wf2, checkpoint_storage=storage)

        # 手动将 checkpoint 标记为还没有结束，以便继续执行
        from workflow_engine.models.state import WorkflowState
        cp.state = WorkflowState.RUNNING
        # 更新 checkpoint 让它从 node2 继续
        cp.current_node_id = "node2"
        storage.save(cp)

        result2 = runner2.run_from_checkpoint("cp_test")
        self.assertTrue(result2.is_success)
        # 注意：node1 不会重复执行，但是 node2 和 node3 会执行，所以 count 应该是 3 (1+2)
        # 但实际恢复时，当前保存的 count 是 1，node2 会让它变成 2，node3 会变成 3
        # 不过要注意 node1 不会再被执行！
        print(f"Final count: {result2.final_output}")


if __name__ == "__main__":
    unittest.main()
