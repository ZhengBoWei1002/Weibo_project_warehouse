"""
Checkpoint 功能示例。

演示如何使用 Checkpoint 保存和恢复 Workflow。
"""

import os
import shutil
from dataclasses import dataclass

from workflow_engine import (
    BaseNode,
    WorkflowBuilder,
    WorkflowRunner,
    JsonFileCheckpointStorage,
    WorkflowState,
)


@dataclass
class StepNode(BaseNode):
    """简单的步骤节点。"""
    message: str = ""

    def _run(self, ctx):
        step = ctx.get_workflow("step", 0)
        step += 1
        ctx.set_workflow("step", step)
        print(f"  {self.message} (Step {step})")
        return step


@dataclass
class PauseNode(BaseNode):
    """暂停节点，用于演示中间状态。"""

    def _run(self, ctx):
        print("  Pausing...")
        return "paused"

    def get_next_action(self, ctx, output):
        from workflow_engine import Action
        return Action.pause()


def main():
    """主函数。"""
    print("=" * 60)
    print("Checkpoint 功能示例")
    print("=" * 60)

    # 清理旧的 checkpoints
    checkpoint_dir = "checkpoint_example"
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)

    # 创建 Workflow
    node1 = StepNode(node_id="step1", name="Step 1", message="Hello from Step 1!")
    node2 = StepNode(node_id="step2", name="Step 2", message="Hello from Step 2!")
    node3 = StepNode(node_id="step3", name="Step 3", message="Hello from Step 3!")
    node4 = StepNode(node_id="step4", name="Step 4", message="Hello from Step 4!")

    workflow = (
        WorkflowBuilder("checkpoint_demo", "Checkpoint Demo")
        .add_nodes(node1, node2, node3, node4)
        .add_edge("step1", "step2")
        .add_edge("step2", "step3")
        .add_edge("step3", "step4")
        .set_start("step1")
        .set_end("step4")
        .build()
    )

    # 第一次运行：保存到中间状态
    print("\n1. 第一次运行，将执行到 Step 2 后结束...")

    storage = JsonFileCheckpointStorage(directory=checkpoint_dir)
    runner = WorkflowRunner(workflow, checkpoint_storage=storage, auto_save_checkpoint=True)

    # 运行
    result = runner.run()
    print(f"\n   结果状态: {result.state}")
    print(f"   最终输出: {result.final_output}")

    # 列出 checkpoints
    print(f"\n2. 检查 Checkpoint 文件 (在 {checkpoint_dir} 目录)")
    checkpoint_ids = storage.list()
    for cid in checkpoint_ids:
        print(f"   - {cid}")

    # 第二次运行：从 Checkpoint 恢复
    print("\n3. 从 Checkpoint 恢复并继续执行...")

    # 创建新的 runner 来恢复
    runner2 = WorkflowRunner(workflow, checkpoint_storage=storage)
    result2 = runner2.run_from_checkpoint("checkpoint_demo")

    print(f"\n   结果状态: {result2.state}")
    print(f"   最终输出: {result2.final_output}")

    # 清理
    print("\n4. 清理...")
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)
        print("   Checkpoint 目录已清理")


if __name__ == "__main__":
    main()
