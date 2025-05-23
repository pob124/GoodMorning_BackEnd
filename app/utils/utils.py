from fastapi import HTTPException, WebSocket
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_
from typing import Dict, List, Any, Optional, Set
import json
import uuid
from datetime import datetime
from app.models.chatroom import ChatroomDB, MessageDB

# 채팅방 조회 유틸리티
def get_chatroom_or_404(db: Session, chatroom_id: str) -> ChatroomDB:
    """ID로 채팅방을 조회하고, 없으면 404 오류를 발생시킵니다."""
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == chatroom_id).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    return chatroom

# 페이지네이션 유틸리티
def apply_pagination(query: Query, skip: int = 0, limit: int = 100) -> Query:
    """쿼리에 페이지네이션을 적용합니다."""
    return query.offset(skip).limit(limit)

# 채팅방 필터링 유틸리티
def filter_chatrooms(query: Query, filters: Dict[str, Any]) -> Query:
    """필터 조건에 따라 채팅방 쿼리를 필터링합니다."""
    if filters.get("keyword"):
        query = query.filter(ChatroomDB.title.ilike(f"%{filters['keyword']}%"))
    
    if filters.get("is_active") is not None:
        query = query.filter(ChatroomDB.is_active == filters["is_active"])
    
    return query

# 채팅방 참여자 확인 유틸리티
def verify_chatroom_participant(chatroom: ChatroomDB, user_id: str) -> bool:
    """사용자가 채팅방 참여자인지 확인합니다."""
    participants = json.loads(chatroom.participants) if chatroom.participants else []
    if user_id not in participants:
        raise HTTPException(status_code=403, detail="You are not a participant in this chatroom")
    return True

# 메시지 생성 유틸리티
def create_message(db: Session, content: str, chatroom_id: str, sender_id: str) -> MessageDB:
    """새 메시지를 생성하고 저장합니다."""
    message_id = str(uuid.uuid4())
    message = MessageDB(
        id=message_id,
        content=content,
        chatroom_id=chatroom_id,
        sender_id=sender_id,
        timestamp=datetime.utcnow(),
        is_read=False
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message

# WebSocket 연결 관리자 클래스
class ConnectionManager:
    def __init__(self):
        # 채팅방별 연결 관리: {room_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        """WebSocket 연결을 수락하고 등록합니다."""
        await websocket.accept()
        
        # 채팅방이 없으면 생성
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        
        # 사용자 연결 등록
        self.active_connections[room_id][user_id] = websocket
        
        # 접속 알림 메시지 브로드캐스트
        await self.broadcast(f"User {user_id} joined the chat", room_id, "system")
    
    def disconnect(self, websocket: WebSocket, room_id: str) -> Optional[str]:
        """WebSocket 연결을 해제합니다."""
        if room_id not in self.active_connections:
            return None
        
        # 연결된 사용자 찾기
        user_id = None
        for uid, ws in self.active_connections[room_id].items():
            if ws == websocket:
                user_id = uid
                break
        
        if user_id:
            # 연결 해제
            del self.active_connections[room_id][user_id]
            
            # 채팅방에 더 이상 연결된 사용자가 없으면 채팅방도 제거
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        return user_id
    
    async def broadcast(self, message: str, room_id: str, sender: str = "system"):
        """채팅방의 모든 연결된 클라이언트에게 메시지를 브로드캐스트합니다."""
        if room_id not in self.active_connections:
            return
        
        # 채팅방의 모든 클라이언트에게 메시지 전송
        for user_id, websocket in self.active_connections[room_id].items():
            try:
                await websocket.send_text(
                    json.dumps({
                        "sender": sender,
                        "content": message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
            except:
                # 오류 발생 시 연결 해제
                self.disconnect(websocket, room_id)
    
    async def broadcast_message(self, message: MessageDB, room_id: str):
        """채팅방의 모든 연결된 클라이언트에게 DB 메시지를 브로드캐스트합니다."""
        if room_id not in self.active_connections:
            return
        
        # 채팅방의 모든 클라이언트에게 메시지 전송
        message_data = {
            "id": message.id,
            "sender_id": message.sender_id,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        }
        
        for user_id, websocket in self.active_connections[room_id].items():
            try:
                await websocket.send_text(json.dumps(message_data))
            except:
                # 오류 발생 시 연결 해제
                self.disconnect(websocket, room_id)
    
    def get_active_users(self, room_id: str) -> List[str]:
        """특정 채팅방에 현재 접속 중인 사용자 목록을 반환합니다."""
        if room_id not in self.active_connections:
            return []
        
        return list(self.active_connections[room_id].keys())

# 글로벌 ConnectionManager 인스턴스 생성
connection_manager = ConnectionManager()