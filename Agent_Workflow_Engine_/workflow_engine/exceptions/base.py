"""
基础异常类定义。

设计原因：
- 统一的异常基类，便于捕获和处理所有 Workflow 相关异常
- 清晰的异常层级结构，便于定位问题
"""


class WorkflowEngineError(Exception):
    """Workflow Engine 的基础异常类。"""
    pass


class WorkflowError(WorkflowEngineError):
    """Workflow 相关异常。"""
    pass


class NodeError(WorkflowEngineError):
    """Node 相关异常。"""
    pass


class ValidationError(WorkflowEngineError):
    """验证错误。"""
    pass


class WorkflowConfigurationError(ValidationError):
    """Workflow 配置错误。"""
    pass


class NodeConfigurationError(ValidationError):
    """Node 配置错误。"""
    pass
