import pickle
import faiss
from retriever import get_embedding, search_similar_chunks
from generator import generate_answer

# 讀取儲存的 chunks 和 index
with open("chunks/data_mining.pkl", "rb") as f: # rb，以二進制模式讀取，適合向量檔案（非文字檔）
    chunks = pickle.load(f)
index = faiss.read_index("embeddings/data_mining.index")

# 測試查詢功能
query = input("輸入您的問題 ： \n")
top_chunks = search_similar_chunks(query, index, chunks, top_k = 4)

# 產生 GPT 回答
answer = generate_answer(query, top_chunks)

print("\n 回答： \n")
print(answer)