# Evaluate 模块

这个目录包含所有评估相关的组件和工具，与正式系统代码（`app/`）明确分离。

## 📂 目录结构

```
evaluate/
├── __init__.py                   # 模块初始化和快捷导入
├── qa_generator.py              # QA 对生成器（Generator）
├── qa_evaluator.py              # QA 对评估器（Evaluator）
├── llm_as_judge.py              # LLM-as-a-Judge 完整流程
├── rag_evaluator.py             # RAG 系统性能评估器
├── evaluate_rag.py              # 主评估脚本
└── generate_golden_dataset.py   # Golden Dataset 生成工具
```

## 🎯 主要组件

### 1. QA Generator (`qa_generator.py`)
- 从文档 chunks 生成问答对
- 支持自定义 Ollama 模型
- 可配置生成策略

### 2. QA Evaluator (`qa_evaluator.py`)
- 评估问答对的质量
- 多维度评分（准确性、相关性、清晰度）
- 提供详细的评估报告

### 3. LLM-as-a-Judge (`llm_as_judge.py`)
- 整合 Generator 和 Evaluator
- 实现对抗式 QA 生成流程
- 自动重试和质量控制

### 4. RAG Evaluator (`rag_evaluator.py`)
- RAG 系统端到端性能评估
- 多种评估指标（语义相似度、精确匹配等）
- 生成详细的评估报告

### 5. Evaluate RAG (`evaluate_rag.py`)
- 使用 Golden Dataset 评估 RAG 系统
- 批量测试支持
- 生成可视化报告

### 6. Generate Golden Dataset (`generate_golden_dataset.py`)
- 从 Weaviate 或本地 pickle 生成测试数据集
- 双 LLM 对抗验证保证质量
- 支持增量生成

## 🚀 使用方法

### 生成 Golden Dataset

```bash
# 从 Weaviate 生成 50 组 QA
python evaluate/generate_golden_dataset.py --source weaviate --count 50

# 从特定来源生成
python evaluate/generate_golden_dataset.py --source "data_mining" --count 30

# 列出可用来源
python evaluate/generate_golden_dataset.py --list-sources
```

### 评估 RAG 系统

```bash
# 完整评估
python evaluate/evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json

# 快速测试（限制数量）
python evaluate/evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json --limit 10

# 自定义输出
python evaluate/evaluate_rag.py \
    --golden-dataset datasets/golden_weaviate_50_qa.json \
    --output-report my_report.txt \
    --output-json my_results.json
```

### 在代码中导入

```python
# 方式 1: 直接导入
from evaluate.llm_as_judge import LLMAsJudgePipeline
from evaluate.rag_evaluator import RAGEvaluator

# 方式 2: 从包导入
from evaluate import LLMAsJudgePipeline, RAGEvaluator

# 使用
pipeline = LLMAsJudgePipeline()
results = pipeline.process_chunks(chunks, max_qa_pairs=50)
```

## 📊 输出文件

评估结果会保存在以下位置：

- `datasets/` - Golden Dataset (JSON/JSONL 格式)
- `evaluation_reports/` - 评估报告和结果

## ⚙️ 配置

所有评估工具都支持通过环境变量或命令行参数配置：

- `GENERATOR_MODEL` - Generator 使用的模型
- `EVALUATOR_MODEL` - Evaluator 使用的模型
- `OLLAMA_BASE_URL` - Ollama API 端点
- `MAX_RETRIES` - 最大重试次数

## 🔗 相关文档

- [Golden Dataset 指南](../building_note/Golden_Dataset/GOLDEN_DATASET_GUIDE.md)
- [LLM-as-a-Judge 说明](../building_note/LLM_AS_JUDGE.md)
- [快速开始](../QUICK_START.md)
