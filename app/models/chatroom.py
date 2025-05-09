from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# SQLAlchemy Models
class Chatroom(Base):
    __tablename__ = "chatrooms"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, index=True)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    participant_count = Column(Integer, default=0)
    
    # Relationships
    participants = relationship("ChatroomParticipant", back_populates="chatroom")
    messages = relationship("Message", back_populates="chatroom")

class ChatroomParticipant(Base):
    __tablename__ = "chatroom_participants"

    id = Column(String, primary_key=True, index=True)
    chatroom_id = Column(String, ForeignKey("chatrooms.id"))
    user_id = Column(String, ForeignKey("users.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chatroom = relationship("Chatroom", back_populates="participants")
    user = relationship("User")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    chatroom_id = Column(String, ForeignKey("chatrooms.id"))
    sender_id = Column(String, ForeignKey("users.id"))
    content = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chatroom = relationship("Chatroom", back_populates="messages")
    sender = relationship("User")

# Pydantic Models for API
class LocationModel(BaseModel):
    latitude: float
    longitude: float

class ParticipantModel(BaseModel):
    uid: str
    nickname: str
    bio: str
    profileImageUrl: str
    likes: int

class MessageModel(BaseModel):
    id: str
    senderId: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatroomResponse(BaseModel):
    id: str
    title: str
    participants: List[ParticipantModel]
    connection: List[LocationModel]
    createdAt: datetime
    Message: List[MessageModel]

    class Config:
        from_attributes = True

# 검색 결과용 간소화된 응답 모델
class ChatroomSearchResponse(BaseModel):
    id: str
    title: str
    participant_count: int
    participants: List[ParticipantModel]
    connection: List[LocationModel]
    createdAt: datetime
    last_message: Optional[MessageModel] = None  # 마지막 메시지만 포함
    unread_count: Optional[int] = 0  # 읽지 않은 메시지 수

    class Config:
        from_attributes = True

class ChatroomFilter(BaseModel):
    keyword: Optional[str] = None
    is_active: Optional[bool] = True
    min_participants: Optional[int] = None
    max_participants: Optional[int] = None 