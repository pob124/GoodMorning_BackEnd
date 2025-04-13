from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserData(BaseModel):
    id_token: str
    name: str = None
    profile_picture: str = None
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
    password: Optional[str] = None
    
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