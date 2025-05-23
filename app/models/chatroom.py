from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
from app.models.user_models import UserProfile  # UserProfile 모델 import

# 채팅방-사용자 다대다 관계를 위한 중간 테이블
chatroom_participants = Table(
    'chatroom_participants',
    Base.metadata,
    Column('chatroom_id', Integer, ForeignKey('chatrooms.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

# Pydantic 모델 (API 스키마에 맞춤)
class Coordinate(BaseModel):
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")

class MessageBase(BaseModel):
    content: str = Field(..., description="메시지 내용")

class MessageCreate(MessageBase):
    """메시지 생성 요청 모델"""
    chatroom_id: str = Field(..., description="채팅방 ID")

class Message(BaseModel):
    id: str = Field(..., description="메시지 ID")
    senderId: str = Field(..., description="발신자 ID")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(..., description="타임스탬프")

    class Config:
        from_attributes = True

class ChatroomBase(BaseModel):
    title: str = Field(..., description="채팅방 제목")

class ChatroomCreate(BaseModel):
    title: str = Field(..., description="채팅방 제목")
    participants: List[str] = Field(..., min_items=1, max_items=2, description="참가자 목록 (최소 1명, 최대 2명)")
    connection: List[Coordinate] = Field(..., min_items=1, max_items=2, description="위치 정보 (최소 1개, 최대 2개)")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "새로운 채팅방",
                "participants": ["user1", "user2"],
                "connection": [
                    {"latitude": 37.5665, "longitude": 126.9780},
                    {"latitude": 37.5665, "longitude": 126.9780}
                ]
            }
        }

class Chatroom(BaseModel):
    id: str = Field(..., description="채팅방 ID")
    title: str = Field(..., description="채팅방 제목")
    participants: List[UserProfile] = Field(..., min_items=1, max_items=2, description="참가자 목록")
    connection: List[Coordinate] = Field(..., min_items=1, max_items=2, description="위치 정보")
    createdAt: datetime = Field(..., description="생성 시간")
    message: List[Message] = Field(default_factory=list, min_items=0, max_items=10, alias="Message")

    class Config:
        from_attributes = True

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
            message=[msg.to_api_model() for msg in recent_messages[:10]]
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

# 검색 결과용 모델
class ChatroomSearchResponse(BaseModel):
    id: str
    title: str
    participants: List[UserProfile]
    connection: List[Coordinate]
    createdAt: datetime
    message: List[Message] = Field(default_factory=list, max_items=1)  # messages를 Message로 변경하고 마지막 메시지만 포함
    unread_count: int = 0  # 읽지 않은 메시지 수

    class Config:
        from_attributes = True

class ChatroomFilter(BaseModel):
    keyword: Optional[str] = None
    is_active: Optional[bool] = True 