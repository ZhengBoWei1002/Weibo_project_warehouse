"""
第一个 Agent Workflow 示例：

Plan -> Search -> Read -> Finish
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dataclasses import dataclass

from workflow_engine import (
    BaseNode,
    WorkflowBuilder,
    WorkflowRunner,
    Action,
)


@dataclass
class PlanNode(BaseNode):
    """规划阶段节点。"""

    def _run(self, ctx):
        print("\n" + "=" * 60)
        print("[Plan] 执行：Plan")
        plan = "Research workflow engine"
        ctx.set_workflow("plan", plan)
        print(f"  [OK] 规划完成：{plan}")
        return plan


@dataclass
class SearchNode(BaseNode):
    """搜索阶段节点。"""

    def _run(self, ctx):
        print("\n" + "=" * 60)
        print("[Search] 执行：Search")
        results = ["Workflow engine basics", "State machine patterns", "Checkpointing"]
        ctx.set_workflow("search_results", results)
        print(f"  [OK] 搜索到 {len(results)} 条结果")
        for r in results:
            print(f"    - {r}")
        return results


@dataclass
class ReadNode(BaseNode):
    """阅读阶段节点。"""

    def _run(self, ctx):
        print("\n" + "=" * 60)
        print("[Read] 执行：Read")
        results = ctx.get_workflow("search_results", [])
        summary = "\n".join([f"阅读了：{r}" for r in results])
        ctx.set_workflow("summary", summary)
        print("  [OK] 阅读完成")
        for r in results:
            print(f"    - {r}")
        return summary


@dataclass
class FinishNode(BaseNode):
    """结束阶段节点。"""

    def _run(self, ctx):
        print("\n" + "=" * 60)
        print("[Finish] 执行：Finish")
        summary = ctx.get_workflow("summary", "")
        print("  [OK] 最终结果：")
        print(summary)
        print("\n" + "=" * 60)
        print("[Complete] Workflow 结束！")
        print("=" * 60)
        return summary


def main():
    """主函数，运行第一个示例。"""
    print("\n" + "=" * 60)
    print("Agent Workflow Example 1: Plan -> Search -> Read -> Finish")
    print("=" * 60)

    # 创建节点
    plan_node = PlanNode(node_id="plan", name="Plan")
    search_node = SearchNode(node_id="search", name="Search")
    read_node = ReadNode(node_id="read", name="Read")
    finish_node = FinishNode(node_id="finish", name="Finish")

    # 构建 Workflow
    workflow = (
        WorkflowBuilder("agent_research_1", "Agent Research Flow 1")
        .add_nodes(plan_node, search_node, read_node, finish_node)
        .add_edge("plan", "search")
        .add_edge("search", "read")
        .add_edge("read", "finish")
        .set_start("plan")
        .set_end("finish")
        .build()
    )

    # 运行 Workflow
    runner = WorkflowRunner(workflow)
    result = runner.run()

    print("\n[Result] Workflow Result:")
    print(f"  State: {result.state}")
    print(f"  Success: {result.is_success}")


if __name__ == "__main__":
    main()
