"""
带 RetryPolicy 的 Workflow 示例。

展示如何使用 RetryPolicy 来自动重试失败的节点。
"""

from dataclasses import dataclass
from typing import Any

from workflow_engine import (
    BaseNode,
    RetryPolicy,
    WorkflowBuilder,
    WorkflowRunner,
)


@dataclass
class FlakyNode(BaseNode):
    """容易失败的节点，但有一定概率成功。"""

    max_failures: int = 3
    _failure_count: int = 0

    def _run(self, ctx):
        self._failure_count += 1
        if self._failure_count <= self.max_failures:
            print(f"FlakyNode 尝试 {self._failure_count}: 失败")
            raise Exception("模拟失败")
        print(f"FlakyNode 尝试 {self._failure_count}: 成功")
        return "Flaky success"


@dataclass
class SimpleNode(BaseNode):
    """简单节点。"""

    def _run(self, ctx):
        print("SimpleNode: 执行成功")
        return "Simple success"


def main():
    """主函数。"""
    # 测试 1: 失败 2 次，第 3 次成功
    print("=" * 60)
    print("测试 1: 失败 2 次，第 3 次成功")
    print("=" * 60)

    retry_policy = RetryPolicy(
        max_retries=3,
        delay_seconds=0.1  # 短延迟便于测试
    )

    flaky_node = FlakyNode(
        node_id="flaky",
        name="Flaky Node",
        max_failures=2,  # 失败 2 次，第 3 次成功
        retry_policy=retry_policy
    )

    simple_node = SimpleNode(node_id="simple", name="Simple Node")

    workflow = (
        WorkflowBuilder("test_retry_1", "Test Retry 1")
        .add_nodes(flaky_node, simple_node)
        .add_edge("flaky", "simple")
        .set_start("flaky")
        .set_end("simple")
        .build()
    )

    runner = WorkflowRunner(workflow)
    result = runner.run()

    print(f"\n最终状态: {result.state}")
    print(f"最终输出: {result.final_output}")

    # 测试 2: 超过最大重试次数，最终失败
    print("\n" + "=" * 60)
    print("测试 2: 超过最大重试次数")
    print("=" * 60)

    flaky_node_2 = FlakyNode(
        node_id="flaky2",
        name="Flaky Node 2",
        max_failures=5,  # 失败 5 次，但只允许重试 3 次
        retry_policy=RetryPolicy(max_retries=3, delay_seconds=0.1)
    )

    workflow_2 = (
        WorkflowBuilder("test_retry_2", "Test Retry 2")
        .add_node(flaky_node_2)
        .set_start("flaky2")
        .set_end("flaky2")
        .build()
    )

    runner_2 = WorkflowRunner(workflow_2)
    result_2 = runner_2.run()

    print(f"\n最终状态: {result_2.state}")
    if result_2.is_failure:
        print(f"错误: {result_2.error}")


if __name__ == "__main__":
    main()
