"""
LLM-as-a-Judge Pipeline
整合 Generator 和 Evaluator，實現完整的對抗式 QA 生成流程

這個 Pipeline 實現了三回合的對抗機制：
1. Generation (生成) - Generator 從 chunk 生成 QA 對
2. Critique (審查) - Evaluator 嚴格評估 QA 對的品質
3. Decision (決策) - 根據評估結果決定是否採納或重試
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .qa_evaluator import QAEvaluator
from .qa_generator import QAGenerator

load_dotenv()


class LLMAsJudgePipeline:
    """LLM-as-a-Judge 完整流水線"""

    def __init__(
        self, generator_model: str = None, evaluator_model: str = None, base_url: str = None, max_retries: int = None
    ):
        """
        初始化 Pipeline

        Args:
            generator_model: Generator 使用的模型（None 則從環境變數讀取）
            evaluator_model: Evaluator 使用的模型（None 則從環境變數讀取）
            base_url: Ollama API 端點（None 則從環境變數讀取）
            max_retries: 最大重試次數（None 則從環境變數讀取）
        """
        # 從環境變數獲取配置
        if max_retries is None:
            max_retries = int(os.getenv("MAX_RETRIES", "2"))

        self.generator = QAGenerator(base_url=base_url, model=generator_model)

        self.evaluator = QAEvaluator(base_url=base_url, model=evaluator_model)

        self.max_retries = max_retries

        print(f"\n{'=' * 60}")
        print("🚀 LLM-as-a-Judge Pipeline 初始化完成")
        print(f"{'=' * 60}")
        print(f"Generator: {self.generator.model}")
        print(f"Evaluator: {self.evaluator.model}")
        print(f"API 端點: {self.generator.base_url}")
        print(f"最大重試次數: {max_retries}")
        print(f"{'=' * 60}\n")

    def process_single_chunk(self, chunk: str, chunk_id: str | None = None) -> dict | None:
        """
        處理單一 chunk，包含生成、評估、重試邏輯

        Args:
            chunk: 文檔片段
            chunk_id: chunk 的識別ID（選填）

        Returns:
            通過審查的 QA 對，或 None（如果多次重試後仍失敗）
        """
        chunk_id = chunk_id or f"chunk_{int(time.time())}"

        for attempt in range(self.max_retries + 1):
            # 第一回合：生成
            if attempt == 0:
                print(f"🎯 [{chunk_id}] 第 {attempt + 1} 次嘗試：生成 QA 對...")
            else:
                print(f"🔄 [{chunk_id}] 第 {attempt + 1} 次嘗試：重新生成...")

            qa_pair = self.generator.generate_qa_pair(chunk)

            if not qa_pair:
                print("   ✗ 生成失敗")
                continue

            print(f"   ✓ 問題: {qa_pair['question'][:50]}...")

            # 第二回合：審查
            print(f"⚖️  [{chunk_id}] 送交評估...")

            evaluation = self.evaluator.evaluate_qa_pair(
                chunk=chunk, question=qa_pair["question"], ground_truth=qa_pair["ground_truth"]
            )

            # 第三回合：決策
            if evaluation["verdict"] == "PASS":
                print("   ✓ PASS - 已通過審查！")
                return {
                    "chunk_id": chunk_id,
                    "chunk": chunk,
                    "question": qa_pair["question"],
                    "ground_truth": qa_pair["ground_truth"],
                    "evaluation": evaluation,
                    "attempts": attempt + 1,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                print(f"   ✗ REJECT - {evaluation['reason']}")
                print(f"      評分: {evaluation['scores']}")

        # 達到最大重試次數仍失敗
        print(f"   ⚠️  [{chunk_id}] 達到最大重試次數，放棄此 chunk")
        return None

    def process_chunks(
        self, chunks: list[str], max_qa_pairs: int | None = None, save_to_file: str | None = None
    ) -> dict[str, list[dict]]:
        """
        批量處理多個 chunks

        Args:
            chunks: 文檔片段列表
            max_qa_pairs: 想要獲得的 QA 對數量（None = 處理全部）
            save_to_file: 結果儲存路徑（選填）

        Returns:
            {
                "passed": [...],      # 通過審查的 QA 對
                "rejected": [...]     # 最終被拒絕的統計資訊
            }
        """
        passed_qa_pairs = []
        rejected_count = 0
        total_attempts = 0

        target_count = max_qa_pairs if max_qa_pairs else len(chunks)

        print(f"\n{'=' * 60}")
        print("開始批量處理")
        print(f"{'=' * 60}")
        print(f"總 chunks 數: {len(chunks)}")
        print(f"目標 QA 數: {target_count}")
        print(f"{'=' * 60}\n")

        start_time = time.time()

        for i, chunk in enumerate(chunks):
            # 如果已經收集到足夠的 QA 對，就停止
            if len(passed_qa_pairs) >= target_count:
                print(f"\n✓ 已收集到 {target_count} 組 QA 對，停止處理")
                break

            print(f"\n{'─' * 60}")
            print(f"處理進度: {i + 1}/{len(chunks)} | 已通過: {len(passed_qa_pairs)}/{target_count}")
            print(f"{'─' * 60}")

            result = self.process_single_chunk(chunk=chunk, chunk_id=f"chunk_{i + 1:03d}")

            total_attempts += 1

            if result:
                passed_qa_pairs.append(result)
            else:
                rejected_count += 1

        # 統計
        elapsed_time = time.time() - start_time
        success_rate = len(passed_qa_pairs) / total_attempts * 100 if total_attempts > 0 else 0

        print(f"\n{'=' * 60}")
        print("處理完成！")
        print(f"{'=' * 60}")
        print(f"✓ 通過: {len(passed_qa_pairs)} 組")
        print(f"✗ 拒絕: {rejected_count} 組")
        print(f"成功率: {success_rate:.1f}%")
        print(f"總耗時: {elapsed_time:.1f} 秒")
        print(f"平均每組: {elapsed_time / total_attempts:.1f} 秒" if total_attempts > 0 else "N/A")
        print(f"{'=' * 60}\n")

        # 儲存結果
        results = {
            "passed": passed_qa_pairs,
            "statistics": {
                "total_passed": len(passed_qa_pairs),
                "total_rejected": rejected_count,
                "success_rate": success_rate,
                "elapsed_time": elapsed_time,
                "timestamp": datetime.now().isoformat(),
            },
        }

        if save_to_file:
            self.save_results(results, save_to_file)

        return results

    def save_results(self, results: dict, filepath: str):
        """
        儲存結果到檔案

        Args:
            results: 包含 passed 和 statistics 的結果字典
            filepath: 儲存路徑
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 儲存為 JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"💾 結果已儲存至: {output_path}")

        # 同時儲存為 JSONL 格式（方便訓練使用）
        jsonl_path = output_path.with_suffix(".jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for qa in results["passed"]:
                # 只保存必要欄位
                minimal_qa = {"chunk": qa["chunk"], "question": qa["question"], "ground_truth": qa["ground_truth"]}
                f.write(json.dumps(minimal_qa, ensure_ascii=False) + "\n")

        print(f"💾 JSONL 格式已儲存至: {jsonl_path}")


if __name__ == "__main__":
    # 測試程式碼
    print("初始化 Pipeline...")

    pipeline = LLMAsJudgePipeline(
        generator_model="qwen2.5:7b-instruct", evaluator_model="llama3.1:8b-instruct", max_retries=2
    )

    # 測試 chunks
    test_chunks = [
        """
        機器學習是人工智慧的一個分支，它使電腦系統能夠從數據中學習並改進，
        而無需明確編程。監督式學習是機器學習中最常見的類型，它使用標記的
        訓練數據來教導算法進行預測。
        """,
        """
        深度學習是機器學習的一個子領域，使用多層神經網路來處理複雜的
        模式識別任務。卷積神經網路(CNN)特別適合處理圖像數據，而循環
        神經網路(RNN)則擅長處理序列數據如文本和語音。
        """,
    ]

    # 執行處理
    results = pipeline.process_chunks(chunks=test_chunks, max_qa_pairs=2, save_to_file="test_golden_dataset.json")

    print(f"\n最終獲得 {len(results['passed'])} 組高品質 QA 對！")
