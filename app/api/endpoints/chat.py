from fastapi import APIRouter, Depends, Body, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import json

from app.core.firebase import get_current_user_id, get_db
from app.models.chatroom import MessageModel, MessageDB, ChatroomDB

router = APIRouter(
    prefix="/chat",
    tags=["채팅"],
    responses={404: {"description": "Not found"}},
)

# WebSocket 연결 관리를 위한 클래스
class ConnectionManager:
    def __init__(self):
        # room_id: {websocket: user_id}
        self.active_connections: Dict[str, Dict[WebSocket, str]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][websocket] = user_id
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(websocket, None)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def broadcast(self, message: str, room_id: str, sender_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(json.dumps({
                    "sender_id": sender_id,
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }))

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str):
    try:
        # 토큰 검증
        user_id = await get_current_user_id(token)
        
        # WebSocket 연결
        await manager.connect(websocket, room_id, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(data, room_id, user_id)
        except WebSocketDisconnect:
            manager.disconnect(websocket, room_id)
            await manager.broadcast(f"User {user_id} left the chat", room_id, "system")
    except Exception as e:
        await websocket.close(code=1008)  # Policy Violation

@router.get("/{room_id}", response_model=List[MessageModel], summary="채팅 내역 조회")
async def get_chat_history(
    room_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    특정 채팅방의 메시지 내역을 조회합니다.
    
    - **room_id**: 채팅방 ID
    - **skip**: 건너뛸 메시지 수
    - **limit**: 가져올 메시지 수
    - **current_user_id**: 현재 로그인한 사용자 ID
    
    Returns:
        List[MessageModel]: 채팅 메시지 목록
    """
    # 채팅방 존재 여부 확인
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_id).first()
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    # 참가자 확인
    participants = json.loads(chatroom.participants)
    if current_user_id not in participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only participants can view chat history"
        )
    
    # 메시지 조회
    messages = db.query(MessageDB)\
        .filter(MessageDB.chatroom_id == room_id)\
        .order_by(MessageDB.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return messages

@router.post("/{room_id}", response_model=MessageModel, status_code=status.HTTP_201_CREATED, summary="메시지 전송")
async def send_message(
    room_id: str,
    message: str = Body(..., embed=True),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    채팅방에 새로운 메시지를 전송합니다.
    
    - **room_id**: 채팅방 ID
    - **message**: 전송할 메시지
    - **current_user_id**: 현재 로그인한 사용자 ID
    
    Returns:
        MessageModel: 생성된 메시지 정보
    """
    # 채팅방 존재 여부 확인
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_id).first()
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    # 참가자 확인
    participants = json.loads(chatroom.participants)
    if current_user_id not in participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only participants can send messages"
        )
    
    # 메시지 생성
    db_message = MessageDB(
        content=message,
        chatroom_id=room_id,
        sender_id=current_user_id,
        created_at=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@router.patch("/{room_id}/messages/{message_id}/read", summary="메시지 읽음 처리")
async def mark_message_as_read(
    room_id: str,
    message_id: int,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    메시지를 읽음 상태로 표시합니다.
    
    - **room_id**: 채팅방 ID
    - **message_id**: 메시지 ID
    - **current_user_id**: 현재 로그인한 사용자 ID
    
    Returns:
        dict: 성공 상태
    """
    # 채팅방 존재 여부 확인
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_id).first()
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    # 참가자 확인
    participants = json.loads(chatroom.participants)
    if current_user_id not in participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only participants can mark messages as read"
        )
    
    # 메시지 존재 여부 확인
    message = db.query(MessageDB)\
        .filter(MessageDB.id == message_id, MessageDB.chatroom_id == room_id)\
        .first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # 메시지 읽음 상태 업데이트
    message.is_read = True
    db.commit()
    
    return {"status": "success"} 