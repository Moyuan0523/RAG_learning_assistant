"""
QA Generator Module
使用 Qwen2 模型從文檔 chunks 生成問答對
負責「出題」的角色
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class QAGenerator:
    """問答生成器 - 負責從文檔片段生成問題和答案"""

    def __init__(self, base_url: str = None, model: str = None, api_key: str = "ollama"):
        """
        初始化 QA Generator

        Args:
            base_url: Ollama API 端點（None 則從環境變數讀取）
            model: 使用的模型名稱（None 則從環境變數讀取）
            api_key: API key（Ollama 不需要真實 key）
        """
        # 從環境變數獲取配置（如果未指定）
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if model is None:
            model = os.getenv("GENERATOR_MODEL", "qwen2.5:7b-instruct-q4_K_M")

        # 確保 base_url 包含 /v1 路徑
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.base_url = base_url
        print("✓ QA Generator 初始化完成")
        print(f"  模型: {model}")
        print(f"  端點: {base_url}")

    def generate_qa_pair(self, chunk: str, temperature: float = 0.7, max_tokens: int = 1000) -> dict[str, str] | None:
        """
        從文檔片段生成一組問答對

        Args:
            chunk: 文檔片段
            temperature: 生成溫度（0.7 較有創意）
            max_tokens: 最大生成長度

        Returns:
            {"question": "...", "ground_truth": "...", "chunk": "..."}
            如果生成失敗則返回 None
        """

        system_prompt = """你是一個專業的教育內容創建者，擅長從學術文本中設計有價值的問答題目。

你的任務：
1. 仔細閱讀給定的文本片段
2. 生成一個學習者可能會問的「有深度」的問題
3. 提供一個精準的標準答案（ground truth）

要求：
- 問題必須具備完整的上下文（避免代名詞如「它」、「他」、「這個」）
- 答案必須 100% 基於給定的文本內容，不能添加臆測
- 問題應該測試理解力，而非簡單的記憶
- 使用繁體中文

輸出格式（JSON）：
{
  "question": "你生成的問題",
  "ground_truth": "標準答案"
}"""

        user_prompt = f"""請根據以下文本片段，生成一組問答對：

【文本】
{chunk}

請以 JSON 格式輸出你的問答對。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 解析 LLM 輸出
            raw_output = response.choices[0].message.content.strip()

            # 嘗試從 markdown code block 中提取 JSON
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()

            # 解析 JSON
            qa_pair = json.loads(raw_output)

            # 驗證必要欄位
            if "question" not in qa_pair or "ground_truth" not in qa_pair:
                print("⚠️  生成的 JSON 缺少必要欄位")
                return None

            # 附加原始 chunk
            qa_pair["chunk"] = chunk

            return qa_pair

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON 解析失敗: {e}")
            print(f"   原始輸出: {raw_output[:200]}...")
            return None
        except Exception as e:
            print(f"⚠️  生成失敗: {e}")
            return None

    def generate_multiple_qa_pairs(self, chunks: list[str], max_pairs: int | None = None) -> list[dict[str, str]]:
        """
        批量生成多個問答對

        Args:
            chunks: 文檔片段列表
            max_pairs: 最多生成幾組（None 表示全部處理）

        Returns:
            成功生成的問答對列表
        """
        qa_pairs = []
        total = min(len(chunks), max_pairs) if max_pairs else len(chunks)

        print("\n🎯 開始生成問答對...")
        print(f"   目標數量: {total}")

        for i, chunk in enumerate(chunks[:total]):
            print(f"\n📝 [{i + 1}/{total}] 正在生成...")

            qa_pair = self.generate_qa_pair(chunk)

            if qa_pair:
                qa_pairs.append(qa_pair)
                print(f"   ✓ 問題: {qa_pair['question'][:60]}...")
            else:
                print("   ✗ 生成失敗，跳過")

        print(f"\n✓ 完成！成功生成 {len(qa_pairs)}/{total} 組問答對")
        return qa_pairs


if __name__ == "__main__":
    # 測試程式碼
    generator = QAGenerator(base_url="http://localhost:11434/v1", model="qwen2.5:7b-instruct")

    # 測試文本
    test_chunk = """
    機器學習是人工智慧的一個分支，它使電腦系統能夠從數據中學習並改進，
    而無需明確編程。監督式學習是機器學習中最常見的類型，它使用標記的
    訓練數據來教導算法進行預測。深度學習是機器學習的一個子領域，
    使用多層神經網路來處理複雜的模式識別任務。
    """

    print("\n" + "=" * 60)
    print("測試 QA Generator")
    print("=" * 60)

    qa_pair = generator.generate_qa_pair(test_chunk)

    if qa_pair:
        print("\n✓ 生成成功！")
        print(f"\n問題: {qa_pair['question']}")
        print(f"\n答案: {qa_pair['ground_truth']}")
    else:
        print("\n✗ 生成失敗")
