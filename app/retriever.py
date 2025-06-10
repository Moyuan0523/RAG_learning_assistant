import os
import fitz  # PyMuPDF
import faiss
import numpy as np
import weaviate 
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from typing import List

# model for embedding, local, free
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def connect_weaviate():
    # read enviornment variable
    load_dotenv()
    server_ip = os.getenv("SERVER_IP")

    # Connect Weaviate v3 DB on remote server 
    weaviate_client = weaviate.Client("http://" + server_ip + ":8080")
    if weaviate_client.is_ready():
        print("Connected to Weaviate")
    else:
        print("Failed to connect to Weaviate")
    return weaviate_client

# read PDF，get str for whole text
def load_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    pdf_content = ""
    for page in doc:
        pdf_content += page.get_text()
    doc.close()
    return pdf_content

# Spilt pdf_text to overlaping chunks
def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]: # 初始化數值，也可後續overwrite
    spliter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap
    )
    chunks = spliter.split_text(text)
    return chunks

def get_embedding(text: str) -> List[float]:
    #  HuggingFace 
    return embedding_model.encode(text).tolist()

# # 將 chunks 轉為向量後存入 FAISS 向量資料庫
# def build_faiss_index(chunks: List[str]):
#     embeddings = [get_embedding(chunk) for chunk in chunks] # 依序放入，效果如下
#     #get_embedding("什麼是決策樹") → [0.123, -0.456, ..., 0.789]  # 共 1536 維
#     #embeddings = [
#     #   [0.123, -0.456, ..., 0.789],  # chunk 1 的向量
#     #   [0.001, 0.876, ..., -0.234],  # chunk 2 的向量
#     #   [0.234, 0.567, ..., 0.001]    # chunk 3 的向量
#     # ]
#     dim = len(embeddings[0]) # 設定維度，text-embedding-ada-002 維度為 1536
#     index = faiss.IndexFlatL2(dim)  # 建立扁平式索引器，以 L2 歐幾里得距離作為相似度依據
#     index.add(np.array(embeddings).astype("float32")) # 存入資料庫
#     return index, embeddings

# get the most similar chunks
def search_similar_chunks(query: str, top_k: int = 3, source_filter: str = None) -> List[str]:
    weaviate_client = connect_weaviate()
    query_vector = get_embedding(query) # query to vector
    
    # Get the near vector from class Paragraph 
    query_obj = weaviate_client.query.get("Paragraph", ["text", "source"]) \
        .with_near_vector({"vector" : query_vector}) \
        .with_limit(top_k)
    
    if source_filter:
        if isinstance(source_filter, list):
            # Multiple source, "OR" operator (store in List)
            or_conditions = [
                {
                    "path": ["source"],
                    "operator": "Equal",
                    "valueText": src
                } for src in source_filter
            ]
            query_obj = query_obj.with_where({
                "operator": "Or",
                "operands": or_conditions
        })
        elif isinstance(source_filter, str):
            # Single source
            query_obj = query_obj.with_where({
                "path": ["source"],
                "operator": "Equal",
                "valueText": source_filter
            })
    
    results = query_obj.do()
    
    return[
        {
            "text" : item["text"],
            "source" : item.get("source", "N/A")
        }
        for item in results["data"]["Get"]["Paragraph"]
    ]