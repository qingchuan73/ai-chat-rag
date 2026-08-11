from sqlalchemy.orm import Session
from database.models import Conversation
from database.models import Message




def update_title(
    db:Session,
    conversation_id:int,
    title:str
):
    conversation=db.query(
        Conversation
    ).filter(
        Conversation.id==conversation_id
    ).first()
    
    conversation.title=title
    db.commit()
    
    return conversation

def get_summary(
    db,
    conversation_id
):

    conversation=db.query(
        Conversation
    ).filter(
        Conversation.id==conversation_id
    ).first()


    return conversation.summary

def update_summary(
    db,
    conversation_id,
    summary
):
    conversation=db.query(
        Conversation
    ).filter(
        Conversation.id==conversation_id
    ).first()
    
    conversation.summary=summary
    db.commit()

def create_conversation(
    db,
    user_id
):
    conversation=Conversation(
        user_id=user_id,
        title="New Chat"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation

def get_user_conversations(
    db,
    user_id
):
    return db.query(
        Conversation
    ).filter(
        Conversation.user_id==user_id
    ).all()
    
def get_user_conversation(
    db,
    conversation_id,
    user_id
):
    return db.query(
        Conversation
    ).filter(
        Conversation.id==conversation_id,
        Conversation.user_id==user_id
    ).first()