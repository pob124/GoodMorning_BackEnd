# 모든 모델을 하나의 파일로 통합
from sqlalchemy import Column, String, Boolean, DateTime, func, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

# SQLAlchemy 베이스
Base = declarative_base()

# SQLAlchemy DB 모델
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 프로필 관련 추가 필드
    profile_picture = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    phone_number = Column(String, nullable=True)
    location = Column(String, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    
    # 로그인 관련 추가 필드
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)

# 채팅방 모델
class ChatroomDB(Base):
    __tablename__ = "chatrooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

# 채팅방 참여자 모델
class ParticipantDB(Base):
    __tablename__ = "participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatroom_id = Column(UUID(as_uuid=True), ForeignKey("chatrooms.id"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    joined_at = Column(DateTime, default=func.now())

# 메시지 모델
class MessageDB(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatroom_id = Column(UUID(as_uuid=True), ForeignKey("chatrooms.id"), index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())

# Pydantic API 모델
class UserData(BaseModel):
    id_token: str
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None

class SignupData(BaseModel):
    username: str
    password: str
    name: str
    token: str

class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    is_active: bool = True
    
    # 프로필 필드
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    
    # 로그인 정보
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserProfile(BaseModel):
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# OpenAPI에 정의된 모델들
class Coordinate(BaseModel):
    latitude: float
    longitude: float

class Participant(BaseModel):
    userId: str
    coordinate: Coordinate

class CreateChatroomRequest(BaseModel):
    title: Optional[str] = None
    participants: List[Participant]

class UpdateChatroomRequest(BaseModel):
    title: Optional[str] = None

class UpdateMyPageRequest(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    profileImageUrl: Optional[str] = None

class Chatroom(BaseModel):
    id: str
    title: Optional[str] = None
    participants: List[Participant]
    createdAt: datetime
    
    class Config:
        from_attributes = True

class Message(BaseModel):
    id: str
    senderId: str
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True 