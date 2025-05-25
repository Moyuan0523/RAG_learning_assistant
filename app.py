# 利用 flask 將 python 變成網頁應用的Web框架
from flask import Flask, render_template, request
from app.retriever import load_pdf, split_text, build_faiss_index, search_similar_chunks
from app.generator import generate_answer
from langchain.memory import ConversationBufferMemory 
import pickle, faiss, os

app = Flask(__name__)
memory = ConversationBufferMemory(return_messages = True) # 初始化 memory

# 讀取 chunk 和 index
with open("chunks/data_mining.pkl", "rb") as f:
    chunks = pickle.load(f)
index = faiss.read_index("embeddings/data_mining.index")

@app.route("/", methods=["POST", "GET"])
def home():
    answer = ""
    query = ""
    retrieved_chunks = []

    if request.method == "POST":
        # 取得使用者輸入的問題
        query = request.form["query"]

        # 語意檢索相關段落
        query_result = search_similar_chunks(query, index, chunks, top_k=4, return_indices=True)
        top_chunks = query_result["chunks"]
        top_indices = query_result["indices"]
        retrieved_chunks = [(i, chunks[i]) for i in top_indices]  # 給前端顯示

        # 更新記憶體（問 + 留空回答）
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message("(尚未回答)")

        # 呼叫 GPT 模型產生回答（內部會組 prompt）
        history = memory.chat_memory.messages
        answer = generate_answer(query, top_chunks, history = history)
        memory.chat_memory.messages[-1].content = answer  # 將 GPT 回答寫入記憶體

    return render_template("index.html", query=query, answer=answer, retrieved_chunks=retrieved_chunks)

if __name__ == "__main__":
    app.run(debug=True)