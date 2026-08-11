import json
from .redis_client import redis_client

def save_context(
    user_id,
    conversation_id,
    messages
):
    key=f"chat:{user_id}:{conversation_id}"
    
    redis_client.set(
        key,
        json.dumps(messages,ensure_ascii=False),
        ex=3600
    )
    
def get_context(
    user_id,
    conversation_id
):
    key=f"chat:{user_id}:{conversation_id}"
    
    data=redis_client.get(key)
    
    if data:
        return json.loads(data)

    return []