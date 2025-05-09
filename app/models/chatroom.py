from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# 채팅방-사용자 다대다 관계를 위한 중간 테이블
chatroom_participants = Table(
    'chatroom_participants',
    Base.metadata,
    Column('chatroom_id', Integer, ForeignKey('chatrooms.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

# Pydantic 모델
class Coordinate(BaseModel):
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")

class ChatroomBase(BaseModel):
    title: str = Field(..., description="채팅방 제목")
    description: Optional[str] = Field(None, description="채팅방 설명")
    location: Coordinate = Field(..., description="위치 정보")
    max_participants: int = Field(..., description="최대 참가자 수")
    is_active: bool = Field(True, description="활성화 상태")

class ChatroomCreate(ChatroomBase):
    pass

class Chatroom(ChatroomBase):
    id: int = Field(..., description="채팅방 ID")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    created_by: str = Field(..., description="생성자 ID")
    participants: List[str] = Field(default_factory=list, description="참가자 목록")

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str = Field(..., description="메시지 내용")
    chatroom_id: int = Field(..., description="채팅방 ID")

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int = Field(..., description="메시지 ID")
    sender_id: str = Field(..., description="발신자 ID")
    created_at: datetime = Field(..., description="생성 시간")
    is_read: bool = Field(False, description="읽음 상태")

    class Config:
        from_attributes = True

# SQLAlchemy 모델
class ChatroomDB(Base):
    __tablename__ = "chatrooms"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    max_participants = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=False)
    participants = Column(Text, default="[]")  # JSON 문자열로 저장

class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    chatroom_id = Column(Integer, ForeignKey("chatrooms.id"))
    sender_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    chatroom = relationship("ChatroomDB", back_populates="messages")

# Pydantic Models for API
class CoordinateModel(BaseModel):
    latitude: float
    longitude: float

    class Config:
        from_attributes = True

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