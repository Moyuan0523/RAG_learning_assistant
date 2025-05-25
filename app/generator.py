from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

# 組合出送進 GPT 的 Prompt (User's question + relative chunks)
def bulid_prompt(query:str, contexts: list[str]) -> str:
    context_text = "\n___\n".join(contexts)
    return f"""根據以下資料之內容回答問題。若無明確資料，誠實說不知道，不可編造或猜測。
    資料內容：
    {context_text}

    問題：
    {query}

    回答：
"""

# 根據以下資料內容回答問題。若無明確資訊，請誠實說不知道，不要編造。

# 資料內容：
# 段落1內容
# ---
# 段落2內容
# ---
# 段落3內容

# 問題：
# 什麼是 Gini 指數？

# 回答：


def generate_answer(query: str, contexts: list[str], model = "gpt-3.5-turbo") -> str:
    prompt = bulid_prompt(query, contexts)
    response = client.chat.completions.create(
        model = model,
        messages = [
            {"role" : "system", "content" : "你是個嚴謹的學習助理。請根據提供的內容來作答，禁止編造。"},
            {"role" : "user", "content" : prompt}
        ],
        temperature = 0.3 # 回答的創意程度，卻低越穩定，越高越創意
    )
    return response.choices[0].message.content