"""
简单的 Workflow 示例。

演示如何使用 Workflow Engine 创建和执行一个简单的工作流。
"""

from dataclasses import dataclass

from workflow_engine import (
    BaseNode,
    Workflow,
    WorkflowBuilder,
    WorkflowRunner,
)


# 定义简单的 Node
@dataclass
class HelloNode(BaseNode):
    """打印 Hello 的节点。"""

    def _run(self, ctx):
        name = ctx.get_input("name", "World")
        message = f"Hello, {name}!"
        print(message)
        ctx.set_output("message", message)
        return message


@dataclass
class ProcessNode(BaseNode):
    """处理数据的节点。"""

    def _run(self, ctx):
        message = ctx.get_workflow("message", "")
        processed = message.upper()
        print(f"Processed: {processed}")
        return processed


@dataclass
class GoodbyeNode(BaseNode):
    """打印 Goodbye 的节点。"""

    def _run(self, ctx):
        message = "Goodbye!"
        print(message)
        return message


def main():
    """主函数。"""
    # 构建 Workflow
    builder = WorkflowBuilder("wf_001", "Simple Workflow")

    # 添加节点
    hello_node = HelloNode(node_id="hello", name="Hello Node")
    process_node = ProcessNode(node_id="process", name="Process Node")
    goodbye_node = GoodbyeNode(node_id="goodbye", name="Goodbye Node")

    builder.add_node(hello_node)
    builder.add_node(process_node)
    builder.add_node(goodbye_node)

    # 添加边
    builder.add_edge("hello", "process")
    builder.add_edge("process", "goodbye")

    # 设置起始和结束节点
    builder.set_start("hello")
    builder.set_end("goodbye")

    # 构建 Workflow
    workflow = builder.build()

    # 创建运行器
    runner = WorkflowRunner(workflow)

    # 运行 Workflow
    print("Running workflow...")
    result = runner.run(input_data={"name": "Alice"})

    # 打印结果
    print(f"\nWorkflow completed with state: {result.state}")
    if result.is_success:
        print(f"Final output: {result.final_output}")
    else:
        print(f"Error: {result.error_message}")


if __name__ == "__main__":
    main()
