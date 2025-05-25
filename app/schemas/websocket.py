from pydantic import BaseModel, Field
from typing import Optional, Union, Literal
from datetime import datetime

# WebSocket 메시지 기본 타입
class WebSocketMessage(BaseModel):
    """WebSocket 메시지 기본 구조"""
    type: str = Field(..., description="메시지 타입")
    timestamp: Optional[datetime] = Field(default=None, description="메시지 타임스탬프")

# 인증 메시지
class AuthMessage(WebSocketMessage):
    """인증을 위한 메시지"""
    type: Literal["auth"] = "auth"
    token: str = Field(..., description="JWT 인증 토큰")

# 채팅 메시지 (클라이언트 → 서버)
class ChatMessage(WebSocketMessage):
    """채팅 메시지 전송"""
    type: Literal["message"] = "message"
    content: str = Field(..., min_length=1, max_length=1000, description="메시지 내용")

# 채팅 메시지 응답 (서버 → 클라이언트)
class ChatMessageResponse(WebSocketMessage):
    """채팅 메시지 응답"""
    type: Literal["message"] = "message"
    id: str = Field(..., description="메시지 ID")
    sender_id: str = Field(..., description="발신자 ID")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(..., description="메시지 생성 시간")

# 시스템 메시지 (서버 → 클라이언트)
class SystemMessage(WebSocketMessage):
    """시스템 알림 메시지"""
    type: Literal["system"] = "system"
    content: str = Field(..., description="시스템 메시지 내용")
    sender: Literal["system"] = "system"

# 사용자 상태 메시지
class UserStatusMessage(WebSocketMessage):
    """사용자 접속/퇴장 알림"""
    type: Literal["user_status"] = "user_status"
    user_id: str = Field(..., description="사용자 ID")
    status: Literal["joined", "left"] = Field(..., description="사용자 상태")
    content: str = Field(..., description="상태 메시지")

# 오류 메시지 (서버 → 클라이언트)
class ErrorMessage(WebSocketMessage):
    """오류 메시지"""
    type: Literal["error"] = "error"
    code: int = Field(..., description="오류 코드")
    message: str = Field(..., description="오류 메시지")
    details: Optional[str] = Field(None, description="오류 상세 정보")

# 성공 응답 메시지
class SuccessMessage(WebSocketMessage):
    """성공 응답 메시지"""
    type: Literal["success"] = "success"
    message: str = Field(..., description="성공 메시지")
    data: Optional[dict] = Field(None, description="추가 데이터")

# 연결 확인 메시지 (Ping/Pong)
class PingMessage(WebSocketMessage):
    """연결 확인 요청"""
    type: Literal["ping"] = "ping"

class PongMessage(WebSocketMessage):
    """연결 확인 응답"""
    type: Literal["pong"] = "pong"

# 활성 사용자 목록 요청/응답
class ActiveUsersRequest(WebSocketMessage):
    """활성 사용자 목록 요청"""
    type: Literal["get_active_users"] = "get_active_users"

class ActiveUsersResponse(WebSocketMessage):
    """활성 사용자 목록 응답"""
    type: Literal["active_users"] = "active_users"
    users: list[str] = Field(..., description="활성 사용자 ID 목록")

# 채팅방 정보 요청/응답
class RoomInfoRequest(WebSocketMessage):
    """채팅방 정보 요청"""
    type: Literal["get_room_info"] = "get_room_info"

class RoomInfoResponse(WebSocketMessage):
    """채팅방 정보 응답"""
    type: Literal["room_info"] = "room_info"
    room_id: str = Field(..., description="채팅방 ID")
    title: str = Field(..., description="채팅방 제목")
    participant_count: int = Field(..., description="참여자 수")
    active_user_count: int = Field(..., description="현재 접속 중인 사용자 수")

# 타이핑 상태 메시지
class TypingMessage(WebSocketMessage):
    """타이핑 상태 알림"""
    type: Literal["typing"] = "typing"
    user_id: str = Field(..., description="타이핑 중인 사용자 ID")
    is_typing: bool = Field(..., description="타이핑 여부")

# 메시지 읽음 상태
class ReadStatusMessage(WebSocketMessage):
    """메시지 읽음 상태"""
    type: Literal["read_status"] = "read_status"
    message_id: str = Field(..., description="읽은 메시지 ID")
    user_id: str = Field(..., description="읽은 사용자 ID")

# WebSocket 메시지 유니온 타입 (들어오는 메시지)
WebSocketIncomingMessage = Union[
    AuthMessage,
    ChatMessage,
    PingMessage,
    ActiveUsersRequest,
    RoomInfoRequest,
    TypingMessage,
    ReadStatusMessage
]

# WebSocket 메시지 유니온 타입 (나가는 메시지)
WebSocketOutgoingMessage = Union[
    ChatMessageResponse,
    SystemMessage,
    UserStatusMessage,
    ErrorMessage,
    SuccessMessage,
    PongMessage,
    ActiveUsersResponse,
    RoomInfoResponse,
    TypingMessage,
    ReadStatusMessage
] 