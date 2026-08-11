from pydantic import BaseModel
from typing import List, Optional
class Message(BaseModel):
    role: str
    content: str
 
class Attachment(BaseModel):
    fileId: int
    displayName: str
    originalName: str
    fileType: str
    size: int
    
class ChatRequest(BaseModel):
    conversation_id:int
    content:str
    attachments: Optional[List[Attachment]] = []


    
class ConversationCreate(BaseModel):
    user_id: int