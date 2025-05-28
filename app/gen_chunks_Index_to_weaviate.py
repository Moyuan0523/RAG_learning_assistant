# 新的chunk生成器，去除原本FAISS的部分，改為上傳至 Weaviate 遠端向量資料庫
import os
import pickle
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from app.retriever_original import load_pdf, split_text, get_embedding
import weaviate

# 讀取環境變數
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 連接 Weaviate v3 遠端資料庫
weaviate_client = weaviate.Client("http://140.116.82.104:8080")

# chunks 與教材的儲存位置，多存一個本地保險
pdf_path = "Sources/Introduction to Data Mining-Pearson Education Limited (2019)-Pang-Ning Tan.pdf"
filename = os.path.basename(pdf_path)
source_name = filename.replace(".pdf", "")
chunks_path = "chunks/data_mining.pkl"

# 讀取資料並切割為 chunks
text = load_pdf(pdf_path)
chunks = split_text(text)

# 儲存本地 chunk 備份
with open(chunks_path, "wb") as f:
    pickle.dump(chunks, f)

# 建立 Weaviate schema 
class_obj = {
    "class": "Paragraph",
    "description": "Chunks from Data Mining PDF",
    "vectorizer": "none",
    "properties": [
        {"name": "text", "dataType": ["text"]},
        {"name": "source", "dataType": ["text"]}
    ]
}
try:
    if "Paragraph" not in [c['class'] for c in weaviate_client.schema.get()["classes"]]:
        weaviate_client.schema.create_class(class_obj)
        print("已新建立 Paragraph schema")

    # 上傳 chunks and embedding    
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        weaviate_client.data_object.create(
            {
                "text": chunk,
                "source": source_name
            },
            class_name = "Paragraph",
            uuid = str(uuid.uuid4()), # 為 chunk 加入唯一識別碼
            vector = embedding
        )
        if i % 10 == 0:
            print(f"已上傳 {i} 段")

    print(f"上傳完成，共 {len(chunks)} 段。已建立 Weaviate 向量索引！")

except Exception as e:
    print("發生錯誤:\n", e)

finally:
    print("關閉連線")
