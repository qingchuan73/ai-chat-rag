from sqlalchemy.orm import Session
from database.models import Conversation
from database.models import Message

def create_message(
    db:Session,
    conversation_id:int,
    role:str,
    content:str
):
    message=Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message
    
def update_message(
        db:Session,
        message_id:int,
        content:str
    ):
        message=db.query(
            Message
        ).filter(
            Message.id==message_id
        ).first()
        
        message.content=content
        db.commit()
        
        return message


def get_conversation_messages(
    db,
    conversation_id,
    user_id,
    limit=20
):

    messages=db.query(
        Message
    ).join(
        Conversation
    ).filter(
        Message.conversation_id==conversation_id,
        Conversation.user_id==user_id
    ).order_by(
        Message.created_at.desc()
    ).limit(
        limit
    ).all()


    return messages[::-1]

def get_message_count(db:Session,conversation_id:int,user_id):
    count=db.query(
    Message
    ).join(
        Conversation
    ).filter(
        Message.conversation_id==conversation_id,
        Conversation.user_id==user_id
    ).count()
    
    return count

def get_all_conversation_messages(
    db,
    conversation_id,
    user_id
):

    return db.query(
        Message
    ).join(
        Conversation
    ).filter(
        Message.conversation_id==conversation_id,
        Conversation.user_id==user_id
    ).order_by(
        Message.created_at
    ).all()