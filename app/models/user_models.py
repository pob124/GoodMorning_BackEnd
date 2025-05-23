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

# SQLAlchemy DB 모델 (API 문서에 맞춤)
class UserDB(Base):
    """데이터베이스 User 모델"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    nickname = Column(String)  # name을 nickname으로 통일
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    likes = Column(Integer, default=0)
    
    # 프로필 관련 필드 (API 문서에 맞춤)
    bio = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)  # profile_picture를 profile_image_url로 통일
    phone_number = Column(String, nullable=True)
    location = Column(String, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    
    # 로그인 관련 필드
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)

# Pydantic API 모델 (API 문서에 맞춤)
class UserBase(BaseModel):
    """기본 사용자 스키마"""
    email: str
    nickname: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str

class UserUpdate(BaseModel):
    """사용자 정보 업데이트 스키마"""
    nickname: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    """API 응답용 사용자 스키마"""
    id: uuid.UUID
    is_active: bool
    likes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    """사용자 프로필 스키마 (API 문서에 맞춤)"""
    uid: str
    nickname: Optional[str] = None
    bio: Optional[str] = None
    profileImageUrl: Optional[str] = None
    likes: int = 0

    class Config:
        from_attributes = True
        
    @classmethod
    def from_db(cls, user_db):
        """DB 모델에서 API 모델로 변환"""
        return cls(
            uid=str(user_db.id) if user_db.id else str(user_db.firebase_uid),
            nickname=user_db.nickname,
            bio=user_db.bio,
            profileImageUrl=user_db.profile_image_url,
            likes=user_db.likes or 0
        )

class Token(BaseModel):
    """토큰 스키마"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    email: Optional[str] = None

class SignupData(BaseModel):
    email: str
    password: str
    nickname: Optional[str] = None
