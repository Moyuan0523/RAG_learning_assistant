from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages = True)

def add_user_message(message: str):
    memory.chat_memory.add_user_message(message)
    # 將使用者的回答加入memory

def add_ai_message(message: str):
    memory.chat_memory.add_ai_message(message)
    # 將機器的回答加入memory

def get_dialogue_history() -> str:
    history = ""
    for msg in memory.chat_memory.messages:
        if msg.type == "human":
            history += f"使用者：{msg.content}\n"
        elif msg.type == "ai":
            history += f"助理：{msg.content}\n"
    return history.strip()
    # strip() 前後多餘的空白或換行去掉

def clear_memory():
    memory.clear()