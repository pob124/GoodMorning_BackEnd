# SQLAlchemy 모델 (DB 스키마)
from sqlalchemy import Column, String, Boolean, DateTime, Integer, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime

# Pydantic 모델 (API 스키마)
from pydantic import BaseModel, EmailStr
from typing import Optional, Union

# 공통 베이스
Base = declarative_base()

# SQLAlchemy DB 모델
class UserDB(Base):
    """데이터베이스 User 모델"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    likes = Column(Integer, default=0)
    
    # 프로필 관련 추가 필드
    profile_picture = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    location = Column(String, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    
    # 로그인 관련 추가 필드
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)

# Pydantic API 모델
class UserBase(BaseModel):
    """기본 사용자 스키마"""
    email: str
    name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str

class UserUpdate(BaseModel):
    """사용자 정보 업데이트 스키마"""
    name: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    """API 응답용 사용자 스키마"""
    id: int
    is_active: bool
    likes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserProfile(BaseModel):
    """사용자 프로필 스키마"""
    uid: str
    nickname: Optional[str] = None
    bio: Optional[str] = None
    profileImageUrl: Optional[str] = None
    likes: int = 0

    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class Token(BaseModel):
    """토큰 스키마"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    email: Optional[str] = None
    firebase_uid: str
class SignupData(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
