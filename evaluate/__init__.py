"""
Evaluation Module for RAG Learning Assistant

这个模块包含所有评估相关的组件：
- qa_generator: 从文档生成问答对
- qa_evaluator: 评估问答对的质量
- llm_as_judge: LLM-as-a-Judge 评估流程
- rag_evaluator: RAG 系统性能评估器
- evaluate_rag: 主要评估脚本
- generate_golden_dataset: 生成高质量测试数据集
"""

__version__ = "1.0.0"

# 方便导入的快捷方式
__all__ = [
    "QAGenerator",
    "QAEvaluator",
    "LLMAsJudgePipeline",
    "RAGEvaluator",
]

try:
    from .llm_as_judge import LLMAsJudgePipeline
    from .qa_evaluator import QAEvaluator
    from .qa_generator import QAGenerator
    from .rag_evaluator import RAGEvaluator
except ImportError:
    # 如果模块尚未完全设置，允许部分导入失败
    pass
