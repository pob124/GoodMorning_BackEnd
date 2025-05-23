# app/utils/utils.py - 유틸리티 함수 모음
from firebase_admin import auth
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, WebSocket, WebSocketDisconnect
import json
import uuid
from typing import Optional, Any, List, Dict, Tuple
from app.models.chatroom import ChatroomDB, MessageDB
from datetime import datetime

# Firebase 인증 관련
async def verify_firebase_token(token: str, db: Session) -> str:
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        # 선택: db에서 사용자 존재 확인 or 생성
        return uid
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

# 채팅방 관련 유틸리티
def get_chatroom_or_404(db: Session, chatroom_id: str) -> ChatroomDB:
    """채팅방을 조회하고, 존재하지 않으면 404 에러를 발생시킵니다."""
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == chatroom_id).first()
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    return chatroom

def verify_chatroom_participant(chatroom: ChatroomDB, user_id: str) -> None:
    """사용자가 채팅방 참여자인지 확인하고, 아니면 403 에러를 발생시킵니다."""
    try:
        participants = json.loads(chatroom.participants)
        if user_id not in participants:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only participants can access this resource"
            )
    except (json.JSONDecodeError, TypeError):
        # participants 필드가 유효한 JSON이 아닌 경우 처리
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid participant data"
        )

# 쿼리 관련 유틸리티
def apply_pagination(query: Any, skip: int = 0, limit: int = 100) -> Any:
    """쿼리에 페이지네이션을 적용합니다."""
    return query.offset(skip).limit(limit)

def filter_chatrooms(query: Any, filter_params: Dict) -> Any:
    """채팅방 필터링 조건을 적용합니다."""
    if filter_params.get("keyword"):
        query = query.filter(ChatroomDB.title.contains(filter_params["keyword"]))
    
    if filter_params.get("is_active") is not None:
        query = query.filter(ChatroomDB.is_active == filter_params["is_active"])
    
    # 추가 필터링 조건은 필요에 따라 구현
    return query

# 메시지 관련 유틸리티
def create_message(db: Session, content: str, chatroom_id: str, sender_id: str) -> MessageDB:
    """새 메시지를 생성하고 저장합니다."""
    message = MessageDB(
        id=str(uuid.uuid4()),  # UUID 문자열 형식으로 변경
        content=content,
        chatroom_id=chatroom_id,
        sender_id=sender_id,
        timestamp=datetime.utcnow(),  # created_at 대신 timestamp 사용
        is_read=False
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

# WebSocket 연결 관리 
class ConnectionManager:
    def __init__(self):
        # room_id: {websocket: user_id}
        self.active_connections: Dict[str, Dict[WebSocket, str]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        """WebSocket 연결을 수락하고 채팅방에 추가합니다."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][websocket] = user_id
        
        # 접속 메시지 브로드캐스트
        await self.broadcast(f"User {user_id} joined the chat", room_id, "system")
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """WebSocket 연결을 해제합니다."""
        if room_id in self.active_connections:
            user_id = self.active_connections[room_id].pop(websocket, None)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            return user_id
        return None
    
    async def broadcast(self, message: str, room_id: str, sender_id: str):
        """채팅방의 모든 연결에 메시지를 브로드캐스트합니다."""
        if room_id in self.active_connections:
            message_data = {
                "senderId": sender_id,  # API 문서에 맞게 필드명 변경
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            for connection in self.active_connections[room_id]:
                await connection.send_text(json.dumps(message_data))
    
    async def broadcast_message(self, message: MessageDB, room_id: str):
        """채팅 메시지 객체를 브로드캐스트합니다."""
        if room_id in self.active_connections:
            message_data = {
                "id": message.id,
                "senderId": message.sender_id,  # API 문서에 맞게 필드명 변경
                "content": message.content,
                "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.now().isoformat()
            }
            for connection in self.active_connections[room_id]:
                await connection.send_text(json.dumps(message_data))
    
    def get_active_users(self, room_id: str) -> List[str]:
        """현재 채팅방에 접속 중인 사용자 목록을 반환합니다."""
        if room_id not in self.active_connections:
            return []
        return list(set(self.active_connections[room_id].values()))

# 전역 연결 관리자 인스턴스
connection_manager = ConnectionManager()
