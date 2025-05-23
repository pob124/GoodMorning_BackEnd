from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, ForwardRef
from datetime import datetime


class Coordinate(BaseModel):
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")

    class Config:
        schema_extra = {
            "example": {
                "latitude": 37.5665,
                "longitude": 126.9780
            }
        }

class Message(BaseModel):
    id: str = Field(..., description="메시지 ID")
    senderId: str = Field(..., description="발신자 ID")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(..., description="전송 시간")

    class Config:
        schema_extra = {
            "example": {
                "id": "msg123",
                "senderId": "user123",
                "content": "내일 몇 시에 만날까요?",
                "timestamp": "2023-05-23T14:30:00Z"
            }
        }

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

class CreateChatroomRequest(BaseModel):
    title: str = Field(..., description="채팅방 제목")
    participants: List[str] = Field(..., description="참여자 UID 목록")
    connection: List[Coordinate] = Field(..., description="위치 정보")

    class Config:
        schema_extra = {
            "example": {
                "title": "한라산 등산 파트너 구해요",
                "participants": ["user123", "user456"],
                "connection": [
                    {"latitude": 37.5665, "longitude": 126.9780},
                    {"latitude": 37.4791, "longitude": 126.8456}
                ]
            }
        }

class Chatroom(BaseModel):
    id: str = Field(..., description="채팅방 ID")
    title: str = Field(..., description="채팅방 제목")
    participants: List[UserProfile] = Field(..., description="참여자 목록")
    connection: List[Coordinate] = Field(..., description="위치 정보")
    createdAt: datetime = Field(..., description="생성 시간")
    messages: List[Message] = Field(default_factory=list, alias="Message", description="최근 메시지 목록")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class ChatroomFilter(BaseModel):
    keyword: Optional[str] = Field(None, description="검색 키워드")
    is_active: Optional[bool] = Field(True, description="활성 채팅방만 검색")