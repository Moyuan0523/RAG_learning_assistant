# 新的chunk生成器，去除原本FAISS的部分，改為上傳至 Weaviate 遠端向量資料庫
import os
import pickle
import uuid
from dotenv import load_dotenv
from app.retriever import load_pdf, split_text, get_embedding
import weaviate

def connect_weaviate():
    # 讀取環境變數
    load_dotenv()
    server_ip = os.getenv("SERVER_IP")

    # 連接 Weaviate v3 遠端資料庫
    weaviate_client = weaviate.Client("http://" + server_ip + ":8080")
    if weaviate_client.is_ready():
        print("Connected to Weaviate")
    else:
        print("Failed to connect to Weaviate")
    return weaviate_client

def pdf_to_weaviate(pdf_filename:str, upload_folder = "Sources"):

    pdf_path = os.path.join(upload_folder,pdf_filename)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} 不存在")
    source_name = pdf_filename.replace(".pdf", "")


    # 讀取資料並切割為 chunks
    text = load_pdf(pdf_path)
    chunks = split_text(text)

    # 建立 Weaviate schema 
    class_obj = {
        "class": "Paragraph",
        "description": "Chunks from uploaded PDFs",
        "vectorizer": "none",
        "properties": [
            {"name": "text", "dataType": ["text"]},
            {"name": "source", "dataType": ["text"]}
        ]
    }

    try:
        weaviate_client = connect_weaviate()
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