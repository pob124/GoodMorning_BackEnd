from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserProfile(BaseModel):
    uid: str = Field(..., description="사용자 UID")
    nickname: Optional[str] = Field(None, description="사용자 닉네임")
    bio: Optional[str] = Field(None, description="자기소개")
    profileImageUrl: Optional[str] = Field(None, description="프로필 이미지 URL")
    likes: int = Field(0, description="좋아요 수")

    class Config:
        schema_extra = {
            "example": {
                "uid": "firebase123",
                "nickname": "하이커",
                "bio": "등산을 좋아합니다.",
                "profileImageUrl": "https://example.com/profile.jpg",
                "likes": 5
            }
        }