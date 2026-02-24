"""
Local LLM Generator for RAG System
支援 Ollama、vLLM 和 Transformers 三種本地部署方式
"""

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# 設定檔讀取
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
LOCAL_LLM_TYPE = os.getenv("LOCAL_LLM_TYPE", "ollama")  # ollama, vllm, transformers
LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3.2:3b-instruct")

# OpenAI 作為備用
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 初始化 client
if USE_LOCAL_LLM:
    if LOCAL_LLM_TYPE in ["ollama", "vllm"]:
        # Ollama 和 vLLM 都使用 OpenAI 兼容的 API
        if LOCAL_LLM_TYPE == "ollama":
            # Ollama 的 OpenAI 兼容端點
            base_url = LOCAL_LLM_BASE_URL.rstrip('/') + '/v1'
        else:
            # vLLM 的 OpenAI 兼容端點
            base_url = LOCAL_LLM_BASE_URL.rstrip('/') + '/v1'
        
        client = OpenAI(
            base_url=base_url,
            api_key="ollama"  # Ollama 不需要真實的 API key，但必須提供
        )
        print(f"✓ 使用本地 LLM: {LOCAL_LLM_TYPE}")
        print(f"✓ 模型: {LOCAL_LLM_MODEL}")
        print(f"✓ API 端點: {base_url}")
    elif LOCAL_LLM_TYPE == "transformers":
        # 使用 Transformers 直接載入模型
        client = None
        print(f"✓ 使用 Transformers 本地模型: {LOCAL_LLM_MODEL}")
else:
    # 使用 OpenAI API
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("✓ 使用 OpenAI API")


def build_prompt(query: str, contexts: list[str]) -> str:
    """
    建立包含檢索到的上下文的 prompt
    """
    context_text = "\n---\n".join(contexts)
    return f"""以下是與問題有關的資料段落：

{context_text}

請根據上述資料段落、以及與使用者的對話內容，詳細回答以下問題。
若段落中沒有提及的資訊，也可根據常識與已知對話內容進行合理說明。請勿胡亂猜測。

{query}
"""


def convert_history_to_openai_format(history):
    """
    將自定義的歷史格式轉換為 OpenAI 格式
    """
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})
    return messages


def generate_answer_with_transformers(query: str, contexts: list[str], history: list = []):
    """
    使用 Transformers 直接生成回答（不透過 API）
    """
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    
    # 載入模型和 tokenizer（只在第一次執行時載入）
    if not hasattr(generate_answer_with_transformers, "model"):
        print("正在載入模型...")
        tokenizer = AutoTokenizer.from_pretrained(LOCAL_LLM_MODEL)
        model = AutoModelForCausalLM.from_pretrained(
            LOCAL_LLM_MODEL,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        generate_answer_with_transformers.model = model
        generate_answer_with_transformers.tokenizer = tokenizer
        print("模型載入完成！")
    
    model = generate_answer_with_transformers.model
    tokenizer = generate_answer_with_transformers.tokenizer
    
    # 建立完整的 prompt
    system_prompt = "你是個嚴謹的學習助理，請根據提供的資料與對話內容作答。嚴禁編造。"
    
    # 組合歷史對話和當前問題
    conversation = f"{system_prompt}\n\n"
    for msg in history:
        if msg["role"] == "user":
            conversation += f"User: {msg['content']}\n"
        elif msg["role"] == "assistant":
            conversation += f"Assistant: {msg['content']}\n"
    
    # 加入當前問題
    prompt = build_prompt(query, contexts)
    conversation += f"User: {prompt}\nAssistant: "
    
    # 進行生成
    inputs = tokenizer(conversation, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.3,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response.strip()


def generate_answer(
    query: str, 
    contexts: list[str], 
    history: list = [], 
    model: str = None
) -> str:
    """
    生成回答的主要函數
    
    Args:
        query: 使用者問題
        contexts: 檢索到的相關段落
        history: 對話歷史
        model: 指定使用的模型（可選，預設使用環境變數設定）
    
    Returns:
        生成的回答文字
    """
    # 決定使用哪個模型
    if model is None:
        model = LOCAL_LLM_MODEL if USE_LOCAL_LLM else "gpt-3.5-turbo"
    
    # 如果使用 Transformers，呼叫特殊的函數
    if USE_LOCAL_LLM and LOCAL_LLM_TYPE == "transformers":
        return generate_answer_with_transformers(query, contexts, history)
    
    # 使用 OpenAI 兼容的 API（包括 OpenAI、Ollama、vLLM）
    messages = [
        {"role": "system", "content": "你是個嚴謹的學習助理，請根據提供的資料與對話內容作答。嚴禁編造。"}
    ]
    
    # 加入歷史對話
    messages += convert_history_to_openai_format(history)
    
    # 建立包含檢索上下文的 prompt
    prompt = build_prompt(query, contexts)
    messages.append({"role": "user", "content": prompt})
    
    try:
        # 呼叫 API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,  # 降低隨機性，提高回答的一致性
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        error_msg = f"生成回答時發生錯誤: {str(e)}"
        print(error_msg)
        
        # 如果是本地 LLM 失敗，且有設定 OpenAI API，嘗試使用備用方案
        if USE_LOCAL_LLM and OPENAI_API_KEY:
            print("嘗試使用 OpenAI API 作為備用...")
            try:
                backup_client = OpenAI(api_key=OPENAI_API_KEY)
                response = backup_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1024
                )
                return response.choices[0].message.content.strip()
            except Exception as backup_error:
                return f"錯誤：本地模型和備用 OpenAI API 都失敗了。\n本地錯誤: {str(e)}\n備用錯誤: {str(backup_error)}"
        
        return error_msg


# 測試函數
def test_connection():
    """
    測試與 LLM 的連線是否正常
    """
    test_query = "請簡單解釋什麼是機器學習。"
    test_contexts = ["機器學習是人工智慧的一個分支，讓電腦系統能夠從數據中學習並改進。"]
    
    print("\n" + "="*50)
    print("測試 LLM 連線...")
    print("="*50)
    
    try:
        answer = generate_answer(test_query, test_contexts, history=[])
        print(f"\n✓ 連線成功！")
        print(f"\n問題: {test_query}")
        print(f"\n回答: {answer}")
        print("\n" + "="*50)
        return True
    except Exception as e:
        print(f"\n✗ 連線失敗: {str(e)}")
        print("\n" + "="*50)
        return False


# 如果直接執行此檔案，進行連線測試
if __name__ == "__main__":
    test_connection()
