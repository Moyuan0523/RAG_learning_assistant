# 新的chunk生成器，去除原本FAISS的部分，改為上傳至 Weaviate 遠端向量資料庫
import os
import pickle
import uuid
from dotenv import load_dotenv
from app.retriever import load_pdf, split_text, get_embedding, connect_weaviate
import weaviate

def pdf_to_weaviate(pdf_filename:str, upload_folder = "Sources"):

    pdf_path = os.path.join(upload_folder,pdf_filename)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} 不存在")
    source_name = pdf_filename.replace(".pdf", "")


    # read and split to chunks
    text = load_pdf(pdf_path)
    chunks = split_text(text)

    # Create Weaviate schema 
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
            print("Created Paragraph schema")

        # Upload chunks and embedding    
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            weaviate_client.data_object.create(
                {
                    "text": chunk,
                    "source": source_name
                },
                class_name = "Paragraph",
                uuid = str(uuid.uuid4()), # for memory to identify
                vector = embedding
            )
            if i % 500 == 0:
                print(f"Uploaded {i} 段")

        print(f"done! {len(chunks)} chunks stored into weaviate DB on remote server")

    except Exception as e:
        print("Error :\n", e)

    finally:
        print("disconnect with weaviate")