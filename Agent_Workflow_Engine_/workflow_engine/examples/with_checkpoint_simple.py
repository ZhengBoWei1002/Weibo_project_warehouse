"""
Checkpoint 简单示例。
"""

import os
import shutil
from dataclasses import dataclass

from workflow_engine import (
    BaseNode,
    WorkflowBuilder,
    WorkflowRunner,
    JsonFileCheckpointStorage,
)


@dataclass
class SimpleNode(BaseNode):
    """简单的节点，递增计数器。"""
    msg: str = ""

    def _run(self, ctx):
        count = ctx.get_workflow("count", 0)
        count += 1
        ctx.set_workflow("count", count)
        print(f"  {self.msg}: {count}")
        return count


def main():
    print("=" * 60)
    print("Checkpoint 简单示例")
    print("=" * 60)

    checkpoint_dir = "checkpoint_test"
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)

    # 创建 Workflow
    node_a = SimpleNode(node_id="a", name="Node A", msg="A")
    node_b = SimpleNode(node_id="b", name="Node B", msg="B")
    node_c = SimpleNode(node_id="c", name="Node C", msg="C")

    workflow = (
        WorkflowBuilder("test_checkpoint", "Checkpoint Test")
        .add_nodes(node_a, node_b, node_c)
        .add_edge("a", "b")
        .add_edge("b", "c")
        .set_start("a")
        .set_end("c")
        .build()
    )

    # 第一步：只运行到 A
    print("\n--- 第一次运行：只运行 Node A ---")

    # 修改 workflow，让它只到 A 就结束，这样能创建一个中间状态的 checkpoint
    partial_workflow = (
        WorkflowBuilder("test_checkpoint", "Checkpoint Test")
        .add_nodes(node_a)
        .set_start("a")
        .set_end("a")
        .build()
    )

    storage = JsonFileCheckpointStorage(directory=checkpoint_dir)
    runner = WorkflowRunner(partial_workflow, checkpoint_storage=storage, auto_save_checkpoint=True)
    result1 = runner.run()
    print(f"  结果: {result1.state}")

    # 查看 checkpoint
    print("\n--- 检查 Checkpoint ---")
    checkpoint = storage.load("test_checkpoint")
    if checkpoint:
        print(f"  Checkpoint 状态: {checkpoint.state}")
        print(f"  Context: {checkpoint.context_data}")
        print(f"  已执行节点: {[r['node_id'] for r in checkpoint.node_results]}")

    # 第二步：从 checkpoint 恢复，执行完整 workflow
    print("\n--- 从 Checkpoint 恢复，执行完整 Workflow ---")
    runner2 = WorkflowRunner(workflow, checkpoint_storage=storage)
    result2 = runner2.run_from_checkpoint("test_checkpoint")
    print(f"  最终结果: {result2.state}")
    print(f"  最终输出: {result2.final_output}")

    # 清理
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)
    print("\n--- 清理完成 ---")


if __name__ == "__main__":
    main()
