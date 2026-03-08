"""
带 Action 的 Workflow 示例。

展示如何使用 Action 来控制 Workflow 执行流程。
"""

from dataclasses import dataclass

from workflow_engine import (
    Action,
    ActionType,
    BaseNode,
    WorkflowBuilder,
    WorkflowRunner,
)


@dataclass
class HelloNode(BaseNode):
    """打印 Hello 的节点。"""

    def _run(self, ctx):
        name = ctx.get_workflow("name", "World")
        message = f"Hello, {name}!"
        print(message)
        ctx.set_workflow("message", message)
        return message


@dataclass
class CheckNode(BaseNode):
    """检查数据的节点，根据条件决定下一步 Action。"""

    def _run(self, ctx):
        message = ctx.get_workflow("message", "")
        print(f"Checking message: {message}")
        return message

    def get_next_action(self, ctx, output):
        """根据输出决定 Action。"""
        if "Alice" in output:
            print("Action: JUMP to special_hello")
            return Action.jump("special_hello")
        elif "Bob" in output:
            print("Action: END here")
            return Action.end("Stop workflow for Bob")
        else:
            print("Action: CONTINUE")
            return Action.continue_()


@dataclass
class SpecialHelloNode(BaseNode):
    """对特殊名字的问候。"""

    def _run(self, ctx):
        message = ctx.get_workflow("message", "")
        special_message = f"Special hello! {message}"
        print(special_message)
        return special_message


@dataclass
class GoodbyeNode(BaseNode):
    """打印 Goodbye 的节点。"""

    def _run(self, ctx):
        message = "Goodbye!"
        print(message)
        return message


def main():
    """主函数。"""
    print("=== Testing with Alice ===")
    test_with_alice()

    print("\n=== Testing with Bob ===")
    test_with_bob()

    print("\n=== Testing with Charlie ===")
    test_with_charlie()


def test_with_alice():
    """测试 Alice 的情况，应该跳转到 special_hello。"""
    builder = WorkflowBuilder("wf_001", "Test with Action")

    hello = HelloNode(node_id="hello", name="Hello Node")
    check = CheckNode(node_id="check", name="Check Node")
    special = SpecialHelloNode(node_id="special_hello", name="Special Hello Node")
    goodbye = GoodbyeNode(node_id="goodbye", name="Goodbye Node")

    builder.add_node(hello)
    builder.add_node(check)
    builder.add_node(special)
    builder.add_node(goodbye)

    builder.add_edge("hello", "check")
    builder.add_edge("check", "goodbye")
    builder.add_edge("special_hello", "goodbye")

    builder.set_start("hello")
    builder.set_end("goodbye")

    workflow = builder.build()
    runner = WorkflowRunner(workflow)
    result = runner.run(input_data={"name": "Alice"})

    print(f"\nResult state: {result.state}")
    print(f"Final output: {result.final_output}")


def test_with_bob():
    """测试 Bob 的情况，应该在 check 节点结束。"""
    builder = WorkflowBuilder("wf_002", "Test with Action")

    hello = HelloNode(node_id="hello", name="Hello Node")
    check = CheckNode(node_id="check", name="Check Node")
    goodbye = GoodbyeNode(node_id="goodbye", name="Goodbye Node")

    builder.add_node(hello)
    builder.add_node(check)
    builder.add_node(goodbye)

    builder.add_edge("hello", "check")
    builder.add_edge("check", "goodbye")

    builder.set_start("hello")
    builder.set_end("goodbye")

    workflow = builder.build()
    runner = WorkflowRunner(workflow)
    result = runner.run(input_data={"name": "Bob"})

    print(f"\nResult state: {result.state}")
    print(f"Final output: {result.final_output}")


def test_with_charlie():
    """测试 Charlie 的情况，应该正常继续执行。"""
    builder = WorkflowBuilder("wf_003", "Test with Action")

    hello = HelloNode(node_id="hello", name="Hello Node")
    check = CheckNode(node_id="check", name="Check Node")
    goodbye = GoodbyeNode(node_id="goodbye", name="Goodbye Node")

    builder.add_node(hello)
    builder.add_node(check)
    builder.add_node(goodbye)

    builder.add_edge("hello", "check")
    builder.add_edge("check", "goodbye")

    builder.set_start("hello")
    builder.set_end("goodbye")

    workflow = builder.build()
    runner = WorkflowRunner(workflow)
    result = runner.run(input_data={"name": "Charlie"})

    print(f"\nResult state: {result.state}")
    print(f"Final output: {result.final_output}")


if __name__ == "__main__":
    main()
