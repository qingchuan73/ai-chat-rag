from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from crud.message import (
    get_all_conversation_messages
)
from crud.conversation import (
    create_conversation,
    get_user_conversations,
    get_user_conversation
)
from services.auth_service import get_current_user_id

router = APIRouter(
    prefix="/conversation",
    tags=["conversation"]
)

@router.post("")
def new_conversation(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) 
):
    print(f"Creating new conversation for user {user_id}")
    conversation = create_conversation(db, user_id)
    return{
        "id":conversation.id,
        "title":conversation.title
    }
    
# @router.get('/{conversation_id}/conversation')
# def get_conversation(
#     conversation_id: int,
#     db: Session = Depends(get_db),
#     current_user_id: int = Depends(get_current_user_id) # 1. 引入当前用户 ID
# ):
#     conversation = search_conversation(db, conversation_id)
    
#     if not conversation:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Conversation not found"
#         )
        
  
#     if conversation.user_id != current_user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have permission to access this conversation"
#         )
        
#     return dict(
#         id=conversation.id,
#         title=conversation.title,
#     )
 
@router.get("")
def conversations(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) #
):
   
    result=get_user_conversations(db,user_id)
    
    return {
        "conversations":[
            {
                "id": c.id,
                "title": c.title
            }
            for c in result
        ]
    }

@router.get('/{conversation_id}/messages')
def messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) # 1. 引入当前用户 ID
):
    conversation = get_user_conversation(
        db,
        conversation_id,
        user_id
    )
    
    if not conversation:
        raise HTTPException(
            404,
            detail="Conversation not found"
        )
        
  
   
        
    result = get_all_conversation_messages(db, conversation_id,user_id)
    
    return {
        "messages":[
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at
            }
            for m in result
        ]
    }
