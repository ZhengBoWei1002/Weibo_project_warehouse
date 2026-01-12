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
│   └── action.py       # Action 类
│   ├── state.py        # 状态枚举
│   ├── checkpoint.py   # Checkpoint 类
│   ├── result.py       # Result 类
│   ├── retry.py        # Retry 类
├── exceptions/         # 自定义异常
│   └── base.py         # 基础异常类
├── utils/              # 工具函数
├── examples/           # 使用示例
│   └── simple.py       # 简单示例
└── tests/              # 单元测试
```

## 文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 详细的架构设计

## 许可证

MIT
