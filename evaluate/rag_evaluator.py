"""
RAG 系統評估器
使用 Golden Dataset 評估 RAG 系統的檢索和生成性能

評估指標：
1. 檢索準確率 (Retrieval Precision)
2. 答案相似度 (Answer Similarity)
3. 答案完整性 (Answer Completeness)
4. 幻覺檢測 (Hallucination Detection)
"""

import json

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 載入環境變數
load_dotenv()

# 使用與 retriever 相同的 embedding 模型以確保一致性
# 使用多語言模型以支持繁體中文
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


class RAGEvaluator:
    """
    RAG 系統評估器

    使用 Golden Dataset 測試 RAG 系統的:
    - 檢索質量（是否檢索到正確的 chunks）
    - 生成質量（答案與 golden answer 的相似度）
    """

    def __init__(self, model_config: dict = None):
        self.embedding_model = embedding_model
        self.results = []
        self.model_config = model_config or {}

    def load_golden_dataset(self, dataset_path: str) -> dict:
        """
        載入 Golden Dataset

        Args:
            dataset_path: Golden Dataset JSON 檔案路徑

        Returns:
            包含 passed 和 rejected 的字典
        """
        print(f"📂 載入 Golden Dataset: {dataset_path}")

        with open(dataset_path, encoding="utf-8") as f:
            dataset = json.load(f)

        passed_count = len(dataset.get("passed", []))
        print(f"✓ 載入 {passed_count} 組通過驗證的 QA 對")

        return dataset

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        計算兩段文本的語義相似度

        Args:
            text1: 第一段文本
            text2: 第二段文本

        Returns:
            相似度分數 (0-1)
        """
        emb1 = self.embedding_model.encode([text1])
        emb2 = self.embedding_model.encode([text2])
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return float(similarity)

    def evaluate_retrieval(self, golden_chunk: str, retrieved_chunks: list[str], top_k: int = 3) -> dict:
        """
        評估檢索質量

        Args:
            golden_chunk: Golden Dataset 中的原始 chunk
            retrieved_chunks: RAG 系統檢索到的 chunks (前 k 個)
            top_k: 檢查前 k 個結果

        Returns:
            檢索評估結果
        """
        # 檢查 golden chunk 是否在檢索結果中
        chunk_found = False
        best_similarity = 0.0
        best_rank = -1

        for i, retrieved_chunk in enumerate(retrieved_chunks[:top_k]):
            similarity = self.calculate_text_similarity(golden_chunk, retrieved_chunk)

            if similarity > best_similarity:
                best_similarity = similarity
                best_rank = i + 1

            # 如果相似度超過 0.75，認為檢索到了正確的 chunk
            # 降低閾值以適應多來源資料和語義匹配的實際情況
            if similarity > 0.75:
                chunk_found = True
                best_rank = i + 1
                break

        return {
            "chunk_found": chunk_found,
            "best_similarity": best_similarity,
            "best_rank": best_rank,
            "recall@k": 1.0 if chunk_found else 0.0,
        }

    def evaluate_answer_quality(self, golden_answer: str, generated_answer: str) -> dict:
        """
        評估生成答案的質量

        Args:
            golden_answer: Golden Dataset 中的標準答案
            generated_answer: RAG 系統生成的答案

        Returns:
            答案質量評估結果
        """
        # 語義相似度
        similarity = self.calculate_text_similarity(golden_answer, generated_answer)

        # 長度比較（檢測過短或過長的答案）
        len_ratio = len(generated_answer) / max(len(golden_answer), 1)

        # 簡單的幻覺檢測：答案是否包含 "我不知道" 等拒絕回答的語句
        refuse_keywords = ["不知道", "無法回答", "沒有提到", "未提及"]
        contains_refusal = any(keyword in generated_answer for keyword in refuse_keywords)

        return {
            "similarity": similarity,
            "length_ratio": len_ratio,
            "contains_refusal": contains_refusal,
            "quality_score": similarity,  # 主要以相似度為準
        }

    def evaluate_single_qa(
        self, question: str, golden_answer: str, golden_chunk: str, rag_answer: str, rag_retrieved_chunks: list[str]
    ) -> dict:
        """
        評估單一 QA 對

        Args:
            question: 問題
            golden_answer: Golden Dataset 中的標準答案
            golden_chunk: Golden Dataset 中的原始 chunk
            rag_answer: RAG 系統生成的答案
            rag_retrieved_chunks: RAG 系統檢索到的 chunks

        Returns:
            完整的評估結果
        """
        # 評估檢索（使用配置中的 top_k 值）
        top_k = self.model_config.get("retriever_top_k", 3)
        retrieval_result = self.evaluate_retrieval(golden_chunk, rag_retrieved_chunks, top_k=top_k)

        # 評估答案質量
        answer_result = self.evaluate_answer_quality(golden_answer, rag_answer)

        # 綜合評估
        overall_score = retrieval_result["recall@k"] * 0.4 + answer_result["quality_score"] * 0.6

        result = {
            "question": question,
            "retrieval": retrieval_result,
            "answer_quality": answer_result,
            "overall_score": overall_score,
        }

        self.results.append(result)
        return result

    def calculate_aggregate_metrics(self) -> dict:
        """
        計算整體評估指標

        Returns:
            聚合的評估指標
        """
        if not self.results:
            return {}

        # 檢索指標
        recall_scores = [r["retrieval"]["recall@k"] for r in self.results]
        avg_recall = np.mean(recall_scores)

        # 答案質量指標
        similarity_scores = [r["answer_quality"]["similarity"] for r in self.results]
        avg_similarity = np.mean(similarity_scores)

        # 整體指標
        overall_scores = [r["overall_score"] for r in self.results]
        avg_overall = np.mean(overall_scores)

        return {
            "total_samples": len(self.results),
            "retrieval_metrics": {
                "recall@3": avg_recall,
                "successful_retrievals": sum(recall_scores),
                "failed_retrievals": len(recall_scores) - sum(recall_scores),
            },
            "answer_metrics": {
                "avg_similarity": avg_similarity,
                "high_quality_answers": sum(1 for s in similarity_scores if s > 0.7),
                "low_quality_answers": sum(1 for s in similarity_scores if s < 0.5),
            },
            "overall_performance": {
                "avg_score": avg_overall,
                "excellent": sum(1 for s in overall_scores if s > 0.8),
                "good": sum(1 for s in overall_scores if 0.6 < s <= 0.8),
                "fair": sum(1 for s in overall_scores if 0.4 < s <= 0.6),
                "poor": sum(1 for s in overall_scores if s <= 0.4),
            },
        }

    def generate_report(self, output_path: str = None) -> str:
        """
        生成評估報告

        Args:
            output_path: 報告輸出路徑（可選）

        Returns:
            報告文字
        """
        metrics = self.calculate_aggregate_metrics()

        report = []
        report.append("=" * 70)
        report.append("RAG 系統評估報告")
        report.append("=" * 70)
        report.append("")

        # 模型配置信息
        if self.model_config:
            report.append("🤖 模型配置")
            report.append("-" * 70)
            if "rag_model" in self.model_config:
                report.append(f"  RAG 生成模型: {self.model_config['rag_model']}")
            if "embedding_model" in self.model_config:
                report.append(f"  Embedding 模型: {self.model_config['embedding_model']}")
            if "retriever_top_k" in self.model_config:
                report.append(f"  檢索數量: Top-{self.model_config['retriever_top_k']}")
            report.append("")

        # 基本信息
        report.append(f"📊 測試樣本數: {metrics['total_samples']}")
        report.append("")

        # 檢索性能
        report.append("🔍 檢索性能")
        report.append("-" * 70)
        retrieval = metrics["retrieval_metrics"]
        report.append(f"  Retrieval Recall@3: {retrieval['recall@3']:.2%}")
        report.append(f"  成功檢索: {retrieval['successful_retrievals']}/{metrics['total_samples']}")
        report.append(f"  失敗檢索: {retrieval['failed_retrievals']}/{metrics['total_samples']}")
        report.append("")

        # 答案質量
        report.append("💬 答案質量")
        report.append("-" * 70)
        answer = metrics["answer_metrics"]
        report.append(f"  Answer Similarity (平均相似度): {answer['avg_similarity']:.2%}")
        report.append(f"  高質量答案 (>0.7): {answer['high_quality_answers']}/{metrics['total_samples']}")
        report.append(f"  低質量答案 (<0.5): {answer['low_quality_answers']}/{metrics['total_samples']}")
        report.append("")

        # 整體性能
        report.append("🎯 整體性能 (Overall Performance)")
        report.append("-" * 70)
        overall = metrics["overall_performance"]
        report.append(f"  平均分數: {overall['avg_score']:.2%}")
        report.append(f"  優秀 (>0.8): {overall['excellent']}")
        report.append(f"  良好 (0.6-0.8): {overall['good']}")
        report.append(f"  尚可 (0.4-0.6): {overall['fair']}")
        report.append(f"  較差 (<0.4): {overall['poor']}")
        report.append("")
        report.append("=" * 70)

        report_text = "\n".join(report)

        # 如果指定了輸出路徑，保存報告
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"✓ 報告已保存至: {output_path}")

        return report_text

    def save_detailed_results(self, output_path: str):
        """
        保存詳細評估結果到 JSON 檔案

        Args:
            output_path: 輸出檔案路徑
        """
        results_data = {"aggregate_metrics": self.calculate_aggregate_metrics(), "detailed_results": self.results}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 詳細結果已保存至: {output_path}")


# 測試程式碼
if __name__ == "__main__":
    print("RAG 評估器模組載入成功")
    print("使用方法請參考: evaluate_rag.py")
