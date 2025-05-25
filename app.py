# 利用 flask 將 python 變成網頁應用的Web框架
from flask import Flask, render_template, request
from app.retriever import load_pdf, split_text, build_faiss_index, search_similar_chunks
from app.generator import generate_answer
import pickle, faiss, os

app = Flask(__name__)

# 讀取 chunk 和 index
with open("chunks/data_mining.pkl", "rb") as f:
    chunks = pickle.load(f)
index = faiss.read_index("embeddings/data_mining.index")

@app.route("/", methods = ["POST", "GET"]) # 定義首頁 url 的處理方式
def home():
    answer = ""
    top_chunks = []
    query = "" 

    if request.method == "POST" :
        query = request.form["query"]
        top_chunks = search_similar_chunks(query, index, chunks, top_k = 4)
        answer = generate_answer(query, top_chunks)
    
    return render_template("index.html", query = query, answer = answer, top_chunks = top_chunks) #回傳 HTML，並將資料丟進去渲染

if __name__ == "__main__":
    app.run(debug = True) #app,run = 開啟一個本地伺服器