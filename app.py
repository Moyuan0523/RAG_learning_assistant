# 利用 flask 將 python 變成網頁應用的Web框架
from flask import Flask, render_template, request
from app.retriever import search_similar_chunks
from app.generator import generate_answer
from langchain.memory import ConversationBufferMemory 
import weaviate
import pickle, os
import uuid

app = Flask(__name__)
memory = ConversationBufferMemory(return_messages = True) # 初始化 memory
source_mapping = {} # 原本是 list，改用 dict 以 uuid 當 Key 辨識每一次回答，避免記憶遺失

# 連接 weaviate 遠端向量資料庫
weaviate_client = weaviate.Client("http://140.116.82.104:8080")

def build_memory(memory_obj):
    result = []
    messages = memory_obj.chat_memory.messages[-20:] # 限制回傳最後幾筆資料數，避免載入過多資料

    for msg in messages:
        if(msg.type == "human"):
            result.append({
                "type" : "human", 
                "content" : msg.content
            })
        elif(msg.type == "ai"):
            msg_id = msg.metadata.get("id") if msg.metadata else None
            source_chunks = source_mapping.get(msg_id)
            result.append({ # 因在 line53. 加入了 id (也是用id找到這次的回答)，便不需再加上 id
                "type" : "ai", 
                "content" : msg.content, 
                "sources" : source_chunks
            })
    return result

@app.route("/", methods=["POST", "GET"])

def home():
    answer = ""
    query = ""
    retrieved_chunks = []

    if request.method == "POST":
        # 取得使用者輸入的問題
        query = request.form["query"]

        # 語意檢索相關段落
        retrieved_chunks = search_similar_chunks(query, top_k = 4)
        top_chunks = [chunk["text"] for chunk in retrieved_chunks]

        # 更新記憶體（問 + 留空回答）
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message("(尚未回答)")

        # 以 uuid 儲存並引用段落
        msg_id = str(uuid.uuid4())
        memory.chat_memory.messages[-1].metadata = {"id" : msg_id} # 在最後（[-1]）的位置加上id，此時最後一筆是 AI_message "尚未回答"
        source_mapping[msg_id] = retrieved_chunks

        # 呼叫 GPT 模型產生回答（內部會組 prompt）
        history = memory.chat_memory.messages
        answer = generate_answer(query, top_chunks, history = history)
        memory.chat_memory.messages[-1].content = answer  # 將 GPT 回答寫入記憶體

        query = ""  # 清空查詢欄

    return render_template("index.html", query = query, memory=build_memory(memory))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)