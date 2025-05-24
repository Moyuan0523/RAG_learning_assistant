import os
import pickle
import faiss
from retriever import load_pdf, split_text, build_faiss_index

pdf_path = "Sources/Introduction to Data Mining-Pearson Education Limited (2019)-Pang-Ning Tan.pdf"
chunks_path = "chunks/data_mining.pkl"
index_path = "embeddings/data_mining.index"

# 讀取 source 和 chunk
text = load_pdf(pdf_path)
chunks = split_text(text)

# 儲存 chunk
with open(chunks_path, "wb") as f:
    pickle.dump(chunks, f)

# 向量化 ＋ FAISS Index
index, embeddings = build_faiss_index(chunks)

#儲存 FAISS 向量資料庫
faiss.write_index(index, index_path)

print(f"完成向量化，共有 {len(chunks)} 段資料")
print(f"chunks 儲存於 {chunks_path}")
print(f"index 儲存於 {index_path}")