# Goal : Record chat history with Weaviate for semantic search
# {
#     "role": "user" / "assistant",
#     "content": "內容文字",
#     "uuid": "對應回答的唯一識別碼",
#     "sources": [...],        # AI 才有（retrieved_chunks）
#     "timestamp": "2025-05-28T22:18",
# }
import uuid
import datetime
from app.retriever import connect_weaviate, get_embedding

class CustomMemory:
    def __init__(self, use_weaviate=True, max_recent_turns=5):
        """
        Args:
            use_weaviate: 是否使用 Weaviate 儲存與檢索對話歷史
            max_recent_turns: 保留最近幾輪對話（始終包含在 context 中）
        """
        self.chat_history = []  # 短期記憶（session 內）
        self.use_weaviate = use_weaviate
        self.max_recent_turns = max_recent_turns
        self.weaviate_client = None
        
        if self.use_weaviate:
            self._init_weaviate_schema()
        #print("CustomMemory created with Weaviate:", use_weaviate)
    
    def _init_weaviate_schema(self):
        """初始化 Weaviate schema for 對話歷史"""
        try:
            self.weaviate_client = connect_weaviate()
            
            # 定義 ChatHistory 類別
            class_obj = {
                "class": "ChatHistory",
                "description": "User and assistant conversation history",
                "vectorizer": "none",
                "properties": [
                    {"name": "role", "dataType": ["text"]},
                    {"name": "content", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["text"]},
                    {"name": "sources", "dataType": ["text"]},  # JSON string
                    {"name": "session_id", "dataType": ["text"]}  # 可用於區分不同對話 session
                ]
            }
            
            # 檢查並創建 schema
            existing_classes = [c['class'] for c in self.weaviate_client.schema.get()["classes"]]
            if "ChatHistory" not in existing_classes:
                self.weaviate_client.schema.create_class(class_obj)
                print("✓ Created ChatHistory schema in Weaviate")
        except Exception as e:
            print(f"⚠️  Weaviate schema init failed: {e}")
            self.use_weaviate = False

    def add_user_message(self, content):
        msg = {
            "role": "user",
            "content": content,
            "timestamp": datetime.datetime.now().isoformat(),
            "uuid": str(uuid.uuid4())
        }
        self.chat_history.append(msg)
        
        # 存入 Weaviate（長期記憶）
        if self.use_weaviate:
            self._save_to_weaviate(msg)

    def add_ai_message(self, content, sources=None):
        msg_id = str(uuid.uuid4())
        msg = {
            "role": "assistant",
            "content": content,
            "uuid": msg_id,
            "sources": sources,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.chat_history.append(msg)
        
        # 存入 Weaviate（長期記憶）
        if self.use_weaviate:
            self._save_to_weaviate(msg)
            
        return msg_id  # uuid
    
    def _save_to_weaviate(self, message):
        """將單一訊息存入 Weaviate"""
        try:
            import json
            embedding = get_embedding(message["content"])
            
            data_obj = {
                "role": message["role"],
                "content": message["content"],
                "timestamp": message["timestamp"],
                "sources": json.dumps(message.get("sources", []), ensure_ascii=False),
                "session_id": "default"  # 可以改成動態 session
            }
            
            self.weaviate_client.data_object.create(
                data_obj,
                class_name="ChatHistory",
                uuid=message["uuid"],
                vector=embedding
            )
        except Exception as e:
            print(f"⚠️  Failed to save to Weaviate: {e}")
    
    def search_relevant_history(self, query, top_k=3):
        """
        從 Weaviate 中搜尋與當前問題最相關的歷史對話
        
        Args:
            query: 當前用戶的問題
            top_k: 返回最相關的 k 條歷史記錄
            
        Returns:
            list: 相關的歷史對話列表
        """
        if not self.use_weaviate:
            return []
        
        try:
            query_embedding = get_embedding(query)
            
            result = self.weaviate_client.query.get(
                "ChatHistory",
                ["role", "content", "timestamp", "sources"]
            ).with_near_vector({
                "vector": query_embedding
            }).with_limit(top_k).do()
            
            data = result.get("data", {}).get("Get", {}).get("ChatHistory", [])
            
            # 轉換為標準格式
            import json
            history = []
            for item in data:
                msg = {
                    "role": item["role"],
                    "content": item["content"],
                    "timestamp": item["timestamp"]
                }
                if item.get("sources"):
                    try:
                        msg["sources"] = json.loads(item["sources"])
                    except:
                        msg["sources"] = []
                history.append(msg)
            
            return history
        except Exception as e:
            print(f"⚠️  Failed to search history: {e}")
            return []
    
    def get_history(self, limit=None, current_query=None):
        """
        智能獲取對話歷史
        
        策略：
        1. 始終包含最近 N 輪對話（短期記憶）
        2. 如果提供 current_query，從 Weaviate 檢索相關的歷史對話（長期記憶）
        3. 合併並去重
        
        Args:
            limit: 最多返回幾條記錄（None = 全部）
            current_query: 當前用戶問題，用於語義搜尋相關歷史
            
        Returns:
            list: 對話歷史列表
        """
        if not self.use_weaviate or current_query is None:
            # 傳統模式：直接返回最近的對話
            return self.chat_history[-limit:] if limit else self.chat_history
        
        # 智能模式：最近對話 + 語義相關對話
        recent_history = self.chat_history[-self.max_recent_turns * 2:] if self.chat_history else []
        
        # 從 Weaviate 檢索相關歷史
        relevant_history = self.search_relevant_history(current_query, top_k=5)
        
        # 合併並去重（基於 content）
        seen_content = set()
        combined_history = []
        
        # 先加入相關歷史
        for msg in relevant_history:
            if msg["content"] not in seen_content:
                seen_content.add(msg["content"])
                combined_history.append(msg)
        
        # 再加入最近歷史（確保最新對話被包含）
        for msg in recent_history:
            if msg["content"] not in seen_content:
                seen_content.add(msg["content"])
                combined_history.append(msg)
        
        # 按時間排序
        combined_history.sort(key=lambda x: x.get("timestamp", ""))
        
        return combined_history[-limit:] if limit else combined_history
    
    def get_source_byid(self, msg_id):
        for msg in self.chat_history:
            if msg.get("uuid") == msg_id:
                return msg.get("source", [])
        return []
    
    def send_to_prompt(self):
        prompt = ""
        for msg in self.chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            prompt += f"{role}: {msg['content']}\n"
        return prompt

