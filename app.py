# 利用 flask 將 python 變成網頁應用的Web框架
from flask import Flask, render_template, request, jsonify, current_app
from app.retriever import search_similar_chunks
from app.generator import generate_answer
#from langchain.memory import ConversationBufferMemory
from app.selfmake_memory import CustomMemory 
import pickle, os
import uuid

os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = Flask(__name__)
#memory = ConversationBufferMemory(return_messages = True) # 初始化 memory
#source_mapping = {} # 原本是 list，改用 dict 以 uuid 當 Key 辨識每一次回答，避免記憶遺失
app.config["memory"] = CustomMemory() # Flask context-safe，確保每次讀同樣的 memory (Flask 可能開啟多執行序，因debug = true)
print("🔥 Flask 啟動中，DEBUG =", app.debug)

# 用以載入首頁
@app.route("/", methods=["GET"])
def home():
    memory = current_app.config["memory"]
    return render_template("index.html", memory=memory.get_history())

# 清除重置 Memory
@app.route("/reset", methods=["POST"])
def reset_memory():
    current_app.config["memory"] = CustomMemory()
    return jsonify({"status": "cleared"})

# fetch User 發過來的 json
@app.route("/chat", methods=["POST"])
def chat():
    memory = current_app.config["memory"]
    data = request.get_json()
    query = data.get("query", "")
    memory.add_user_message(query)

    # Debug 印出記憶內容
    print("現在的記憶內容：")
    for m in memory.get_history():
        print(f"{m['role']}: {m['content']}")

    retrieved_chunks = search_similar_chunks(query, top_k=4) # 引用段落
    top_chunks = [chunk["text"] for chunk in retrieved_chunks]
    answer = generate_answer(query, top_chunks, history=memory.get_history())
    memory.add_ai_message(answer, sources=retrieved_chunks)

    return jsonify({
        "answer": answer,
        "sources": retrieved_chunks
    })

# def home():
#     answer = ""
#     query = ""
#     retrieved_chunks = []

#     if request.method == "POST":
#         # 取得使用者輸入的問題
#         query = request.form["query"]
#         memory.add_user_message(query) # 加入 memory

#         # 語意檢索相關段落
#         retrieved_chunks = search_similar_chunks(query, top_k = 4)
#         top_chunks = [chunk["text"] for chunk in retrieved_chunks]

#         # # 更新記憶體（問 + 留空回答）
#         # memory.chat_memory.add_user_message(query)
#         # memory.chat_memory.add_ai_message("(尚未回答)")

#         #newer version
#         answer = generate_answer(query, top_chunks, history = memory.get_history())
#         msg_id = memory.add_ai_message(answer, sources = retrieved_chunks)
#         # # 以 uuid 儲存並引用段落
#         # msg_id = str(uuid.uuid4())
#         # memory.chat_memory.messages[-1].metadata = {"id" : msg_id} # 在最後（[-1]）的位置加上id，此時最後一筆是 AI_message "尚未回答"
#         # source_mapping[msg_id] = retrieved_chunks

#         # # 呼叫 GPT 模型產生回答（內部會組 prompt）
#         # history = memory.chat_memory.messages
#         # answer = generate_answer(query, top_chunks, history = history)
#         # memory.chat_memory.messages[-1].content = answer  # 將 GPT 回答寫入記憶體

#         query = ""  # 清空查詢欄

#     return render_template(
#         "index.html", 
#         query = query, 
#         memory=build_memory(memory),
#         #answer = answer
#     )

if __name__ == "__main__":
    app.run(use_reloader=False)