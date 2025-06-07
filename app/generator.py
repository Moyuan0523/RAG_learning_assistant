from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

# 組合出送進 GPT 的 Prompt (User's question + relative chunks)
def build_prompt(query: str, contexts: list[str]) -> str:
    context_text = "\n---\n".join(contexts)
    return f"""以下是與問題有關的資料段落：

{context_text}

請根據上述資料段落、以及與使用者的對話內容，詳細回答以下問題。
若段落中沒有提及的資訊，也可根據常識與已知對話內容進行合理說明。請勿胡亂猜測。

{query}
"""
# 資料內容：
# 段落1內容
# ---
# 段落2內容
# ---
# 段落3內容

# 問題：
# 什麼是 Gini 指數？

# 回答：

def convert_history_to_openai_format(history):
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})
    return messages

def generate_answer(query: str, contexts: list[str], history: list = [], model = "gpt-3.5-turbo") -> str:
    messages = [
        {"role" : "system", "content" : "你是個嚴謹的學習助理，請根據提供的資料與對話內容作答。嚴禁編造。"}
    ]

    # 加入歷史對話，轉換成 GPT 接受的格式
    messages += convert_history_to_openai_format(history)
    # 組合 prompt
    prompt = build_prompt(query, contexts)
    # 將這次的 prompt 加入 user 歷史回答中
    messages.append({"role" : "user", "content" : prompt})

    # 呼叫 OpenAI 的 Chat Completions API
    response = client.chat.completions.create(
        model = model,
        messages = messages,
        temperature = 0.3, # 回答的創意程度，卻低越穩定，越高越創意
        max_tokens=1024
    )
    return response.choices[0].message.content.strip()