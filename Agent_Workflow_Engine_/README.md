# Agent Workflow Engine

一个轻量级的 Agent 工作流引擎，用于学习和构建 Agent 系统。

## 特性

- 状态机驱动的工作流编排
- 支持顺序执行、条件分支、循环
- 内置重试机制
- Context 数据共享
- 简单易用，易于扩展
- 不依赖第三方工作流框架
- 支持暂停和取消
- 完整的类型注解

## 项目结构

```
workflow_engine/
├── core/               # 核心模块
│   ├── workflow.py     # Workflow 类
│   ├── builder.py      # WorkflowBuilder 类
│   ├── runner.py       # WorkflowRunner 类
│   ├── router.py       # Router 类
│   └── edge.py         # Edge 类
├── nodes/              # 节点模块
│   └── base.py         # BaseNode 抽象基类
├── models/             # 数据模型
│   ├── state.py        # 状态枚举
│   ├── context.py      # Context 类
│   └── result.py       # Result 类
├── exceptions/         # 自定义异常
│   └── base.py         # 基础异常类
├── utils/              # 工具函数
├── examples/           # 使用示例
│   └── simple.py       # 简单示例
└── tests/              # 单元测试
```

## 文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 详细的架构设计
- [API_DESIGN.md](./API_DESIGN.md) - 公共 API 设计

## 快速开始

```python
from dataclasses import dataclass
from workflow_engine import (
    BaseNode,
    WorkflowBuilder,
    WorkflowRunner,
)


# 定义 Node
@dataclass
class HelloNode(BaseNode):
    def _run(self, ctx):
        name = ctx.get_input("name", "World")
        message = f"Hello, {name}!"
        print(message)
        return message


@dataclass
class GoodbyeNode(BaseNode):
    def _run(self, ctx):
        print("Goodbye!")
        return "Goodbye!"


# 构建 Workflow
builder = WorkflowBuilder("wf_001", "My Workflow")

hello = HelloNode(node_id="hello", name="Hello Node")
goodbye = GoodbyeNode(node_id="goodbye", name="Goodbye Node")

builder.add_node(hello)
builder.add_node(goodbye)
builder.add_edge("hello", "goodbye")
builder.set_start("hello")
builder.set_end("goodbye")

workflow = builder.build()

# 运行 Workflow
runner = WorkflowRunner(workflow)
result = runner.run(input_data={"name": "Alice"})

print(f"State: {result.state}")
print(f"Output: {result.final_output}")
```

更多示例请参考 [examples/](./workflow_engine/examples/)。

## 设计理念

- **简单性优先**：核心代码少，易于理解
- **可扩展性**：通过抽象基类支持自定义节点
- **状态驱动**：基于状态机的调度机制
- **关注点分离**：Workflow 负责编排，Node 负责执行
- **职责单一**：每个类只有一个职责

## 许可证

MIT
