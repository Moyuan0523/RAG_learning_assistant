# Goal : 紀錄歷史問答紀錄，每一次回答紀錄如下
# {
#     "role": "user" / "assistant",
#     "content": "內容文字",
#     "uuid": "對應回答的唯一識別碼（ai才有）",
#     "sources": [...],        # AI 才有（retrieved_chunks）
#     "timestamp": "2025-05-28T22:18",
# }
import uuid
import datetime

class CustomMemory:
    def __init__(self):
        self.chat_history = [] # 紀錄所有對話
        #print("CustomMemory 已建立")
    
    # 加入 User 的回答
    def add_user_message(self, content):
        self.chat_history.append({
            "role" : "user",
            "content" : content,
            "timestamp" : datetime.datetime.now().isoformat()
        })

    # 加入 AI 的回答
    def add_ai_message(self, content, sources = None):
        msg_id = str(uuid.uuid4())
        self.chat_history.append({
            "role" : "assistant",
            "content" : content,
            "uuid" : msg_id,
            "sources" : sources,
            "timestamp" : datetime.datetime.now().isoformat()
        })
        return msg_id # 回傳這次回答的索引
    
    def get_history(self, limit = None):
        return self.chat_history[-limit:] if limit else self.chat_history
    
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
