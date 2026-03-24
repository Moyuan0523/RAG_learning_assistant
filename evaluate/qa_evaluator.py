"""
QA Evaluator Module
使用 Llama 3.1 模型嚴格評估問答對的品質
負責「審查/裁判」的角色
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class QAEvaluator:
    """問答評估器 - 負責嚴格審查 QA 對的品質"""

    def __init__(self, base_url: str = None, model: str = None, api_key: str = "ollama"):
        """
        初始化 QA Evaluator

        Args:
            base_url: Ollama API 端點（None 則從環境變數讀取）
            model: 使用的模型名稱（None 則從環境變數讀取）
            api_key: API key（Ollama 不需要真實 key）
        """
        # 從環境變數獲取配置（如果未指定）
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if model is None:
            model = os.getenv("EVALUATOR_MODEL", "llama3.2:3b")

        # 確保 base_url 包含 /v1 路徑
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.base_url = base_url
        print("✓ QA Evaluator 初始化完成")
        print(f"  模型: {model}")
        print(f"  端點: {base_url}")

    def evaluate_qa_pair(
        self,
        chunk: str,
        question: str,
        ground_truth: str,
        temperature: float = 0.2,  # 評估時需要更嚴謹，溫度較低
    ) -> dict[str, any]:
        """
        評估一組問答對是否符合標準

        Args:
            chunk: 原始文檔片段
            question: 生成的問題
            ground_truth: 生成的標準答案
            temperature: 生成溫度（0.2 更嚴謹）

        Returns:
            {
                "verdict": "PASS" | "REJECT",
                "reason": "評估理由",
                "scores": {
                    "answer_grounded": True/False,  # 答案是否基於文本
                    "question_clear": True/False,    # 問題是否清晰
                    "answer_precise": True/False     # 答案是否精準
                }
            }
        """

        system_prompt = """你是一個嚴格的 QA 審查員（Quality Assurance Judge），專門評估問答對的品質。

你的職責：
對給定的【原始文本】、【問題】、【答案】進行三項嚴格檢查：

1️⃣ 答案基於文本（Answer Grounded）
   ✓ 答案的每一個關鍵資訊都能在原始文本中找到
   ✗ 答案包含任何文本中沒有的資訊（視為幻覺）

2️⃣ 問題清晰具體（Question Clear）
   ✓ 問題有完整的上下文，任何人都能理解
   ✗ 問題使用代名詞（如「它」、「他」、「這個方法」）或缺乏背景

3️⃣ 答案精準對題（Answer Precise）
   ✓ 答案確實回答了問題的核心
   ✗ 答案答非所問或過於發散

評分標準：
- 三項全部通過 ➡️ PASS
- 任何一項不通過 ➡️ REJECT

輸出格式（JSON）：
{
  "verdict": "PASS" or "REJECT",
  "reason": "簡短說明為何 PASS 或 REJECT（50字內）",
  "scores": {
    "answer_grounded": true or false,
    "question_clear": true or false,
    "answer_precise": true or false
  }
}

請保持客觀、嚴格、無情。"""

        user_prompt = f"""請評估以下問答對：

【原始文本】
{chunk}

【問題】
{question}

【答案】
{ground_truth}

請以 JSON 格式輸出你的評估結果。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_tokens=500,
            )

            # 解析 LLM 輸出
            raw_output = response.choices[0].message.content.strip()

            # 嘗試從 markdown code block 中提取 JSON
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()

            # 解析 JSON
            evaluation = json.loads(raw_output)

            # 驗證必要欄位
            required_fields = ["verdict", "reason", "scores"]
            if not all(field in evaluation for field in required_fields):
                print("⚠️  評估結果缺少必要欄位")
                return {
                    "verdict": "REJECT",
                    "reason": "評估器輸出格式錯誤",
                    "scores": {"answer_grounded": False, "question_clear": False, "answer_precise": False},
                }

            # 標準化 verdict（確保是大寫）
            evaluation["verdict"] = evaluation["verdict"].upper()

            return evaluation

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON 解析失敗: {e}")
            print(f"   原始輸出: {raw_output[:200]}...")
            return {
                "verdict": "REJECT",
                "reason": "評估器輸出無法解析",
                "scores": {"answer_grounded": False, "question_clear": False, "answer_precise": False},
            }
        except Exception as e:
            print(f"⚠️  評估失敗: {e}")
            return {
                "verdict": "REJECT",
                "reason": f"評估過程出錯: {str(e)}",
                "scores": {"answer_grounded": False, "question_clear": False, "answer_precise": False},
            }

    def batch_evaluate(self, qa_pairs: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
        """
        批量評估多組問答對

        Args:
            qa_pairs: 問答對列表，每個包含 {chunk, question, ground_truth}

        Returns:
            (passed_pairs, rejected_pairs)
            兩個列表，每個元素都包含原始 QA + 評估結果
        """
        passed = []
        rejected = []

        total = len(qa_pairs)
        print("\n⚖️  開始評估問答對...")
        print(f"   總數: {total}")

        for i, qa in enumerate(qa_pairs):
            print(f"\n📋 [{i + 1}/{total}] 評估中...")

            evaluation = self.evaluate_qa_pair(
                chunk=qa["chunk"], question=qa["question"], ground_truth=qa["ground_truth"]
            )

            # 組合結果
            result = {
                **qa,  # 原始 QA 對
                "evaluation": evaluation,
            }

            if evaluation["verdict"] == "PASS":
                passed.append(result)
                print("   ✓ PASS")
            else:
                rejected.append(result)
                print(f"   ✗ REJECT - {evaluation['reason']}")

        pass_rate = len(passed) / total * 100 if total > 0 else 0
        print("\n✓ 評估完成！")
        print(f"   通過: {len(passed)}/{total} ({pass_rate:.1f}%)")
        print(f"   拒絕: {len(rejected)}/{total}")

        return passed, rejected


if __name__ == "__main__":
    # 測試程式碼
    evaluator = QAEvaluator(base_url="http://localhost:11434/v1", model="llama3.1:8b-instruct")

    # 測試案例 1：好的問答對
    test_chunk = """
    機器學習是人工智慧的一個分支，它使電腦系統能夠從數據中學習並改進，
    而無需明確編程。監督式學習是機器學習中最常見的類型。
    """

    test_question = "什麼是機器學習？"
    test_ground_truth = "機器學習是人工智慧的一個分支，它使電腦系統能夠從數據中學習並改進，而無需明確編程。"

    print("\n" + "=" * 60)
    print("測試案例 1：好的問答對")
    print("=" * 60)

    result = evaluator.evaluate_qa_pair(test_chunk, test_question, test_ground_truth)
    print(f"\n判決: {result['verdict']}")
    print(f"理由: {result['reason']}")
    print(f"詳細評分: {result['scores']}")

    # 測試案例 2：不好的問答對（有幻覺）
    bad_ground_truth = "機器學習是由 Alan Turing 在 1950 年發明的技術。"

    print("\n" + "=" * 60)
    print("測試案例 2：包含幻覺的答案")
    print("=" * 60)

    result2 = evaluator.evaluate_qa_pair(test_chunk, test_question, bad_ground_truth)
    print(f"\n判決: {result2['verdict']}")
    print(f"理由: {result2['reason']}")
    print(f"詳細評分: {result2['scores']}")
