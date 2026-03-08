"""
增强版 WorkflowBuilder 示例。

展示如何使用完整的 Builder API。
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
class InputNode(BaseNode):
    """输入处理节点。"""

    def _run(self, ctx):
        data = ctx.get_workflow("data", "default")
        print(f"Input: {data}")
        return data


@dataclass
class ProcessNode(BaseNode):
    """处理节点。"""

    def _run(self, ctx):
        data = ctx.get_workflow("data", "")
        processed = data.upper()
        print(f"Processed: {processed}")
        ctx.set_workflow("processed", processed)
        return processed


@dataclass
class ValidateNode(BaseNode):
    """验证节点，根据条件决定下一步。"""

    def _run(self, ctx):
        processed = ctx.get_workflow("processed", "")
        print(f"Validating: {processed}")
        return processed

    def get_next_action(self, ctx, output):
        """根据长度决定下一步。"""
        if len(output) > 10:
            print("Action: Jump to long handler")
            return Action.jump("handle_long")
        else:
            return Action.continue_()


@dataclass
class HandleLongNode(BaseNode):
    """处理长输入的节点。"""

    def _run(self, ctx):
        data = ctx.get_workflow("processed", "")
        print(f"Handling long input: {data}")
        return f"[LONG] {data}"


@dataclass
class SaveNode(BaseNode):
    """保存节点。"""

    def _run(self, ctx):
        data = ctx.get_workflow("processed", "")
        print(f"Saving: {data}")
        return f"Saved: {data}"


@dataclass
class OutputNode(BaseNode):
    """输出节点。"""

    def _run(self, ctx):
        result = ctx.get_workflow("processed", "empty")
        print(f"Final Output: {result}")
        return result


def main():
    """主函数。"""
    # 创建节点
    input_node = InputNode(node_id="input", name="Input Handler")
    process_node = ProcessNode(node_id="process", name="Processor")
    validate_node = ValidateNode(node_id="validate", name="Validator")
    handle_long_node = HandleLongNode(node_id="handle_long", name="Long Handler")
    save_node = SaveNode(node_id="save", name="Saver")
    output_node = OutputNode(node_id="output", name="Output")

    # 定义条件函数
    def is_valid_output(ctx, result):
        """验证条件。"""
        return result.output is not None and result.output != ""

    # 使用增强版 WorkflowBuilder
    workflow = (
        WorkflowBuilder(workflow_id="enhanced_workflow", name="Enhanced Workflow")
        # 批量添加节点
        .add_nodes(input_node, process_node, validate_node)
        .add_node(handle_long_node)
        .add_node(save_node)
        .add_node(output_node)
        # 添加边（多种方式）
        .add_default_edge("input", "process")
        .add_conditional_edge(
            "process",
            "validate",
            condition=is_valid_output,
            name="validate branch"
        )
        .add_edge("handle_long", "save")
        .add_default_edge("save", "output")
        # 设置起始和结束
        .set_start("input")
        .set_end("output")
        # 设置元数据
        .set_metadata_item("version", "1.0")
        .set_metadata_item("author", "Test")
        .build()
    )

    print("=" * 60)
    print("Testing with normal input:")
    print("=" * 60)
    runner = WorkflowRunner(workflow)
    result = runner.run(input_data={"data": "hello"})
    print(f"\nResult state: {result.state}")
    print(f"Final output: {result.final_output}")

    print("\n" + "=" * 60)
    print("Testing with long input:")
    print("=" * 60)
    runner = WorkflowRunner(workflow)
    result = runner.run(input_data={"data": "hello world, this is a long input"})
    print(f"\nResult state: {result.state}")
    print(f"Final output: {result.final_output}")


if __name__ == "__main__":
    main()
