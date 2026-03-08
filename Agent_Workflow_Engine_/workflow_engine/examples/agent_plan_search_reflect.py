"""
第二个 Agent Workflow 示例：

Plan -> Search -> Reflection -> (Need Retry? -> Search) -> Report
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import random
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
        plan = "Research Python workflow engine"
        ctx.set_workflow("plan", plan)
        print(f"  [OK] 规划完成：{plan}")
        return plan


@dataclass
class SearchNode(BaseNode):
    """搜索阶段节点，可能失败或成功。"""

    def _run(self, ctx):
        print("\n" + "=" * 60)
        print("[Search] 执行：Search")
        attempt = ctx.get_workflow("search_attempts", 0)
        attempt += 1
        ctx.set_workflow("search_attempts", attempt)
        
        # 模拟：第 2 次才成功（为了演示效果）
        good_results = attempt >= 2
        print(f"  搜索尝试次数：{attempt}")
        print(f"  结果质量：{'Good' if good_results else 'Not good'}")
        
        results = [
            "Workflow engine basics",
            "State machine patterns",
            "Checkpointing"
        ]
        
        if not good_results:
            results = results[:1]  # 只返回 1 个结果，表示不够好
            print(f"  [Warning] 只找到 {len(results)} 条结果")
        else:
            print(f"  [OK] 找到 {len(results)} 条结果")
            
        ctx.set_workflow("search_results", results)
        ctx.set_workflow("results_good", good_results)
        
        return results


@dataclass
class ReflectionNode(BaseNode):
    """反思阶段节点，判断是否需要重试。"""

    def _run(self, ctx):
        print("\n" + "=" * 60)
        print("[Reflection] 执行：Reflection")
        results = ctx.get_workflow("search_results", [])
        good = ctx.get_workflow("results_good", False)
        print(f"  反思结果：")
        print(f"    - 已搜索到 {len(results)} 条结果")
        print(f"    - 结果质量：{'OK' if good else 'NEEDS IMPROVEMENT'}")
        need_retry = not good
        
        # 检查是否已经尝试太多次
        attempts = ctx.get_workflow("search_attempts", 0)
        if attempts >= 3:
            print(f"  [Info] 已尝试 {attempts} 次，接受当前结果")
            need_retry = False
            
        ctx.set_workflow("need_retry", need_retry)
        print(f"  [Decision] 是否需要重试：{'YES' if need_retry else 'NO'}")
        return need_retry

    def get_next_action(self, ctx, output):
        need_retry = ctx.get_workflow("need_retry", False)
        if need_retry:
            # 使用 Action.jump 返回到 search
            return Action.jump("search")
        return Action.continue_()


@dataclass
class ReportNode(BaseNode):
    """报告阶段节点。"""

    def _run(self, ctx):
        print("\n" + "=" * 60)
        print("[Report] 执行：Report")
        results = ctx.get_workflow("search_results", [])
        attempts = ctx.get_workflow("search_attempts", 1)
        
        print(f"  [OK] 最终报告：")
        print(f"    - 搜索尝试次数：{attempts}")
        print(f"    - 最终搜索结果：")
        for r in results:
            print(f"      - {r}")
            
        report = f"Research complete after {attempts} attempts"
        ctx.set_workflow("report", report)
        
        print("\n" + "=" * 60)
        print("[Complete] Workflow 结束！")
        print("=" * 60)
        return report


def main():
    """主函数，运行第二个示例。"""
    print("\n" + "=" * 60)
    print("Agent Workflow Example 2: Plan -> Search -> Reflection -> Report")
    print("=" * 60)

    # 创建节点
    plan_node = PlanNode(node_id="plan", name="Plan")
    search_node = SearchNode(node_id="search", name="Search")
    reflect_node = ReflectionNode(node_id="reflect", name="Reflection")
    report_node = ReportNode(node_id="report", name="Report")

    # 构建 Workflow
    workflow = (
        WorkflowBuilder("agent_research_2", "Agent Research Flow 2")
        .add_nodes(plan_node, search_node, reflect_node, report_node)
        .add_edge("plan", "search")
        .add_edge("search", "reflect")
        .add_edge("reflect", "report")
        .set_start("plan")
        .set_end("report")
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
