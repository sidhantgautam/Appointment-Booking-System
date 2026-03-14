# simple in-memory conversation store

memory_store = {}

def get_memory(session_id: str):
    return memory_store.get(session_id, {})

def update_memory(session_id: str, key: str, value):
    if session_id not in memory_store:
        memory_store[session_id] = {}

    memory_store[session_id][key] = value

def clear_memory(session_id: str):
    if session_id in memory_store:
        del memory_store[session_id]



def add_to_conversation_history(session_id: str, role: str, message: str):
    """Add a message to conversation history"""
    if session_id not in memory_store:
        memory_store[session_id] = {}
    
    if "conversation_history" not in memory_store[session_id]:
        memory_store[session_id]["conversation_history"] = []
    
    from datetime import datetime
    memory_store[session_id]["conversation_history"].append({
        "role": role,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })


def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    memory = get_memory(session_id)
    return memory.get("conversation_history", [])


def get_recent_context(session_id: str, num_messages: int = 5):
    """Get recent conversation context as a formatted string"""
    history = get_conversation_history(session_id)
    recent = history[-num_messages:] if len(history) > num_messages else history
    
    context = ""
    for entry in recent:
        context += f"{entry['role']}: {entry['message']}\n"
    
    return context.strip()
