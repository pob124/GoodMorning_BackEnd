from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table, Float, Text, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.user_models import Base  # 공통 Base 사용
from datetime import datetime
import json

# Schemas에서 Pydantic 모델들 import
from app.schemas.user import UserProfile
from app.schemas.chatroom import Coordinate, Message, Chatroom

# 채팅방-사용자 다대다 관계를 위한 중간 테이블
chatroom_participants = Table(
    'chatroom_participants',
    Base.metadata,
    Column('chatroom_id', String, ForeignKey('chatrooms.id')),
    Column('user_id', UUID, ForeignKey('users.id'))
)

# SQLAlchemy 모델 (DB 스키마에 맞춤)
class ChatroomDB(Base):
    __tablename__ = "chatrooms"

    id = Column(String, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=False)
    participants = Column(Text, default="[]")  # JSON 형식의 문자열로 저장
    connection = Column(Text, default="[]")    # JSON 형식의 문자열로 저장
    is_active = Column(Boolean, default=True)
    
    # MessageDB와의 관계
    messages = relationship("MessageDB", back_populates="chatroom", cascade="all, delete-orphan")

    def get_participants(self):
        """참가자 목록을 JSON 형식에서 파싱하여 반환"""
        try:
            return json.loads(self.participants)
        except:
            return []

    def get_connection(self):
        """좌표 정보를 JSON 형식에서 파싱하여 반환"""
        try:
            return json.loads(self.connection)
        except:
            return []

    def to_api_model(self, user_profiles, recent_messages=None):
        """API 응답 모델로 변환"""
        if recent_messages is None:
            recent_messages = []
        
        return Chatroom(
            id=self.id,
            title=self.title,
            participants=user_profiles,
            connection=self.get_connection(),
            createdAt=self.created_at,
            messages=[msg.to_api_model() for msg in recent_messages[:10]]
        )

class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    chatroom_id = Column(String, ForeignKey("chatrooms.id"))
    sender_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    chatroom = relationship("ChatroomDB", back_populates="messages")

    def to_api_model(self):
        """API 응답 모델로 변환"""
        return Message(
            id=self.id,
            senderId=self.sender_id,
            content=self.content,
            timestamp=self.timestamp
        ) 