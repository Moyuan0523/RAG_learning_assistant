import pickle
import faiss
from retriever import get_embedding, search_similar_chunks

# 讀取儲存的 chunks 和 index
with open("chunks/data_mining.pkl", "rb") as f: # rb，以二進制模式讀取，適合向量檔案（非文字檔）
    chunks = pickle.load(f)
index = faiss.read_index("embeddings/data_mining.index")

# 測試查詢功能
query = "什麼是Gini指數？"
top_chunks = search_similar_chunks(query, index, chunks, top_k = 3)

print("前三個相關的段落如下：\n")
for i, chunk in enumerate(top_chunks, 1): # enmerate 讓迴圈時同時取得 index 和 相對 value
    print(f"[{i}] {chunk[:150]}...\n")