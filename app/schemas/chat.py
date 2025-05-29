from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
from app.schemas.chatroom import Message

class MessageRequest(BaseModel):
    content: str = Field(..., description="메시지 내용")

    class Config:
        schema_extra = {
            "example": {
                "content": "안녕하세요?"
            }
        }

class MessageHistoryParams(BaseModel):
    skip: int = Field(0, description="건너뛸 메시지 수")
    limit: int = Field(50, description="가져올 메시지 수")

class MessageSearchParams(BaseModel):
    keyword: str = Field(..., description="검색할 키워드")

class MessageListResponse(BaseModel):
    messages: List[Message]

class ActiveUsersResponse(BaseModel):
    active_users: List[str] = Field(..., description="접속 중인 사용자 ID 목록")

class MessageReadResponse(BaseModel):
    success: bool = Field(True, description="성공 여부")
    message_id: str = Field(..., description="읽음 처리된 메시지 ID")