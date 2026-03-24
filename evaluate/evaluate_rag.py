"""
使用 Golden Dataset 評估 RAG 系統性能

這個腳本會：
1. 載入 Golden Dataset（高質量的問題-答案對）
2. 用每個問題測試 RAG 系統
3. 比較 RAG 的答案與 Golden Answer
4. 生成評估報告

使用方法：
    # 基本評估
    python evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json

    # 指定輸出報告
    python evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json \\
                           --output-report evaluation_report.txt \\
                           --output-json evaluation_results.json

    # 限制測試數量（快速測試）
    python evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json --limit 10
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案根目錄到 Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 導入 RAG 系統組件
from app.retriever import search_similar_chunks  # noqa: E402
from evaluate.rag_evaluator import RAGEvaluator  # noqa: E402

# 根據環境變數決定使用哪個 generator
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

if USE_LOCAL_LLM:
    from app.generator_local import generate_answer

    print("🚀 使用本地 LLM（Llama 3.2）進行評估")
else:
    from app.generator import generate_answer

    print("🚀 使用 OpenAI API 進行評估")


def test_rag_with_question(question: str, source_filter: str = None) -> dict:
    """
    用單一問題測試 RAG 系統

    Args:
        question: 問題文本
        source_filter: 來源過濾器（可選）

    Returns:
        包含答案和檢索結果的字典
    """
    # 檢索相關 chunks
    retrieved_chunks = search_similar_chunks(query=question, top_k=10, source_filter=source_filter)

    # 提取文本
    chunk_texts = [chunk["text"] for chunk in retrieved_chunks]

    # 生成答案
    answer = generate_answer(
        query=question,
        contexts=chunk_texts,
        history=[],  # 不使用對話歷史，保持公平性
    )

    return {"answer": answer, "retrieved_chunks": chunk_texts, "retrieval_details": retrieved_chunks}


def evaluate_rag_system(golden_dataset_path: str, limit: int = None, source_filter: str = None) -> RAGEvaluator:
    """
    使用 Golden Dataset 評估 RAG 系統

    Args:
        golden_dataset_path: Golden Dataset JSON 檔案路徑
        limit: 限制測試數量（None = 全部測試）
        source_filter: 來源過濾器（可選）

    Returns:
        RAGEvaluator 物件，包含評估結果
    """
    # 準備模型配置信息
    model_config = {
        "rag_model": os.getenv("LOCAL_LLM_MODEL", "Unknown"),
        "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
        "retriever_top_k": 10,
    }

    # 初始化評估器
    evaluator = RAGEvaluator(model_config=model_config)

    # 載入 Golden Dataset
    golden_dataset = evaluator.load_golden_dataset(golden_dataset_path)

    # 取得通過驗證的 QA 對
    passed_qa_pairs = golden_dataset.get("passed", [])

    if not passed_qa_pairs:
        print("❌ Golden Dataset 中沒有通過驗證的 QA 對")
        return evaluator

    # 限制測試數量
    if limit:
        passed_qa_pairs = passed_qa_pairs[:limit]
        print(f"📋 限制測試數量: {limit}")

    print(f"\n🚀 開始評估 RAG 系統（共 {len(passed_qa_pairs)} 個測試）")
    print("=" * 70)

    # 逐一測試
    for i, qa_pair in enumerate(passed_qa_pairs, 1):
        question = qa_pair["question"]
        # 支持兩種字段名：ground_truth（新格式）或 answer（舊格式）
        golden_answer = qa_pair.get("ground_truth") or qa_pair.get("answer")
        golden_chunk = qa_pair["chunk"]

        print(f"\n[{i}/{len(passed_qa_pairs)}] 測試問題: {question[:60]}...")

        try:
            # 測試 RAG 系統
            rag_result = test_rag_with_question(question, source_filter)

            # 評估結果
            eval_result = evaluator.evaluate_single_qa(
                question=question,
                golden_answer=golden_answer,
                golden_chunk=golden_chunk,
                rag_answer=rag_result["answer"],
                rag_retrieved_chunks=rag_result["retrieved_chunks"],
            )

            # 顯示簡要結果
            print(
                f"  檢索: {'✓' if eval_result['retrieval']['chunk_found'] else '✗'} "
                + f"(相似度: {eval_result['retrieval']['best_similarity']:.2f})"
            )
            print(f"  答案: {eval_result['answer_quality']['similarity']:.2%} 相似度")
            print(f"  總分: {eval_result['overall_score']:.2%}")

        except Exception as e:
            print(f"  ❌ 錯誤: {str(e)}")
            continue

    print("\n" + "=" * 70)
    print("✓ 評估完成！")

    return evaluator


def main():
    parser = argparse.ArgumentParser(
        description="使用 Golden Dataset 評估 RAG 系統性能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 基本評估
  python evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json

  # 限制測試 10 個樣本（快速測試）
  python evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json --limit 10

  # 指定輸出檔案
  python evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json \\
                         --output-report reports/evaluation.txt \\
                         --output-json reports/evaluation.json

  # 指定來源過濾
  python evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json \\
                         --source "Data_Mining__The_Textbook_Aggarwal_2015-04-14"
        """,
    )

    parser.add_argument("--golden-dataset", type=str, required=True, help="Golden Dataset JSON 檔案路徑")

    parser.add_argument("--limit", type=int, default=None, help="限制測試的 QA 對數量（用於快速測試）")

    parser.add_argument("--source", type=str, default=None, help="來源過濾器（可選，用於限制檢索範圍）")

    parser.add_argument(
        "--output-report",
        type=str,
        default="evaluation_report.txt",
        help="評估報告輸出路徑（預設: evaluation_report.txt）",
    )

    parser.add_argument(
        "--output-json",
        type=str,
        default="evaluation_results.json",
        help="詳細結果 JSON 輸出路徑（預設: evaluation_results.json）",
    )

    args = parser.parse_args()

    # 檢查 Golden Dataset 是否存在
    if not Path(args.golden_dataset).exists():
        print(f"❌ 找不到 Golden Dataset: {args.golden_dataset}")
        sys.exit(1)

    print("=" * 70)
    print("RAG 系統評估")
    print("=" * 70)
    print(f"📂 Golden Dataset: {args.golden_dataset}")
    if args.limit:
        print(f"📋 測試限制: {args.limit} 個樣本")
    if args.source:
        print(f"📚 來源過濾: {args.source}")
    print("")

    # 執行評估
    evaluator = evaluate_rag_system(
        golden_dataset_path=args.golden_dataset, limit=args.limit, source_filter=args.source
    )

    # 生成報告
    print("\n" + "=" * 70)
    print("📊 生成評估報告")
    print("=" * 70)

    # 文字報告
    report = evaluator.generate_report(args.output_report)
    print(report)

    # 詳細結果 JSON
    evaluator.save_detailed_results(args.output_json)

    print("\n✓ 評估完成！")
    print(f"  📄 文字報告: {args.output_report}")
    print(f"  📊 詳細結果: {args.output_json}")


if __name__ == "__main__":
    main()
