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
├── nodes/              # 节点模块
│   └── base.py         # BaseNode 抽象基类
├── models/             # 数据模型
├── exceptions/         # 自定义异常
│   └── base.py         # 基础异常类
├── utils/              # 工具函数
├── examples/           # 使用示例
└── tests/              # 单元测试
```

## 许可证

MIT
