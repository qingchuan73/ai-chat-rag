from sqlalchemy import (
   Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__="user"
    
    id=Column(
        Integer,
        primary_key=True,
        index=True
    )
    
    username=Column(
        String(50),
        nullable=False
    )
    
    account=Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    password_hash=Column(
        String(128),
        nullable=False,
    )
    
    created_at=Column(
        DateTime,
        default=func.now()
    )
    
    conversations=relationship(
        "Conversation",
        back_populates="user"
    )
    
    knowledge_files=relationship(
        "KnowledgeFile",
        back_populates="user"
    )

    model_config=relationship(
        "UserModelConfig",
        back_populates="user",
        uselist=False,
        cascade="all,delete"
    )
    
    
class Conversation(Base):
    __tablename__="conversation"
    
    id=Column(
        Integer,
        primary_key=True,
      
    )
    
    user_id=Column(
        Integer,
        ForeignKey(
            "user.id"
        ),
        nullable=False
    )
    
    summary=Column(
        Text,
        nullable=True
    )
    
    title=Column(
        String(255),
        default="New Chat"
    )
    
    created_at=Column(
        DateTime,
        default=func.now()
    )
    
    user=relationship(
        "User",
        back_populates="conversations"
    )
    
    messages=relationship(
        "Message",
        back_populates="conversation",
        cascade="all,delete"
    )
    
class Message(Base):
    
    __tablename__='message'
    
    id=Column(
        Integer,
        primary_key=True
    )
    
    conversation_id=Column(
        Integer,
        ForeignKey(
            "conversation.id"
        )
    )
    
    role=Column(
        String(20)
    )
    
    content=Column(
        Text
    )
    
    created_at=Column(
        DateTime,
        default=func.now()
    )
    
    conversation=relationship(
        "Conversation",
        back_populates="messages"
    )
    
    
class KnowledgeFile(Base):
    __tablename__="knowledge_file"
    
    id=Column(
        Integer,
        primary_key=True
    )
    
    user_id=Column(
        Integer,
        ForeignKey("user.id")
    )
    
    original_filename=Column(
        String(255)
    )
    
    storage_filename=Column(
        String(255)
    )
    
    file_type=Column(
        String(50)
    )
    user=relationship(
        "User",
        back_populates="knowledge_files"
    )
    created_at=Column(
        DateTime,
        default=func.now()
    )


class UserModelConfig(Base):
    __tablename__="user_model_config"

    id=Column(
        Integer,
        primary_key=True
    )

    user_id=Column(
        Integer,
        ForeignKey("user.id"),
        unique=True,
        nullable=False,
        index=True
    )

    provider=Column(
        String(50),
        default="openai",
        nullable=False
    )

    base_url=Column(
        String(255),
        nullable=True
    )

    chat_model=Column(
        String(100),
        nullable=False
    )

    api_key_encrypted=Column(
        Text,
        nullable=False
    )

    created_at=Column(
        DateTime,
        default=func.now()
    )

    updated_at=Column(
        DateTime,
        default=func.now(),
        onupdate=func.now()
    )

    user=relationship(
        "User",
        back_populates="model_config"
    )


class RagTrace(Base):
    __tablename__ = "rag_trace"

    id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    conversation_id = Column(
        Integer,
        ForeignKey("conversation.id"),
        nullable=False,
        index=True
    )

    question = Column(
        Text,
        nullable=False
    )

    rewritten_query = Column(
        Text,
        nullable=True
    )

    question_type = Column(
        String(50),
        nullable=True
    )

    used_knowledge = Column(
        String(10),
        nullable=False,
        default="false"
    )

    expanded_queries = Column(
        Text,
        nullable=True
    )

    retrieved_count = Column(
        Integer,
        default=0
    )

    selected_sources = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=func.now()
    )

