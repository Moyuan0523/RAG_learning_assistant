# 利用 flask 將 python 變成網頁應用的Web框架
from flask import Flask, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
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
print("Flask 啟動中，DEBUG =", app.debug)

UPLOAD_FOLDER = "Sources"
ALLOWED_EXTENSIONS = {"pdf"} 
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER #??

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

    retrieved_chunks = search_similar_chunks(query, top_k=10) # 引用段落
    top_chunks = [chunk["text"] for chunk in retrieved_chunks]
    answer = generate_answer(query, top_chunks, history=memory.get_history())
    memory.add_ai_message(answer, sources=retrieved_chunks)

    return jsonify({
        "answer": answer,
        "sources": retrieved_chunks
    })

def allowed_pdf(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"

@app.route("/upload", methods=['POST'])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error" : "You didn't choose the file"}), 400 # ??
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error" : "the name of provided file is empty"}), 400
    
    print("收到檔案：", file.filename)
    
    if file and allowed_pdf(file.filename):
        print("before secure "+file.filename)
        filename = secure_filename(file.filename)
        print("after secure "+filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        print("回傳 JSON：", {"status": "success", "filename": filename, "source": filename})
        return jsonify({
            "status" : "success",
            "filename" : filename,
            "source" : filename # 後續 chunk 的 souce id
        }),200
    else:
        return jsonify({"error" : "ONLY PDF"}), 400
    

if __name__ == "__main__":
    app.run(use_reloader=False)