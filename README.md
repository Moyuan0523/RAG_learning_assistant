# RAG_learning_assistant
RAG Learning Assistant 是一個基於 Retrieval-Augmented Generation 技術的智慧聊天助理，透過 Flask 網頁應用整合 Weaviate 向量資料庫與 OpenAI API，提供文件知識查詢與自然語言回答的能力。

## 功能特色

## 安裝指南
### git 下載
`git clone https://github.com/Moyuan0523/RAG_learning_assistant`
### conda 環境架設
```bash
conda env create -f environment.yml
```

## 使用方式
### Step 1. 
在 app/ 中新建 .env 檔，並加入以下文字：
```
OPENAI_API_KEY = Your_API_key
SERVER_IP = Your_Server_Address
```
### Step 1.     (跳過這步驟，後端功能尚未完善，未來希望讓 user 從網頁加入教材，並選擇從指定教材學習資料)
將自己的教材放入 Source/ 後，執行 gen_chunk_Index_to_weavaite.py
### Step 2. 
執行 app.py，利用 flask 建置 Developer 私人網站，進入聊天室網頁畫面
### Step 3.
在網頁聊天室提出問題，得到回答