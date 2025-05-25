from fastapi import APIRouter, Depends, Body, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from app.schemas.chat import MessageRequest
from app.schemas.chatroom import Message

from datetime import datetime
import json

from app.core.firebase import get_current_user_id, get_db
from app.models.chatroom import MessageDB, ChatroomDB
from app.utils.utils import (
    get_chatroom_or_404, 
    verify_chatroom_participant, 
    apply_pagination, 
    create_message, 
    connection_manager
)

router = APIRouter(
    prefix="/chat",
    tags=["채팅"],
    responses={404: {"description": "Not found"}},
)

@router.get("/search", response_model=List[Message], summary="채팅방 히스토리 검색")
async def search_messages(
    keyword: str = Query(None, description="검색할 키워드"),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    키워드 기반으로 채팅 메시지를 검색합니다.
    
    - **keyword**: 검색할 메시지 키워드
    - **current_user_id**: 현재 로그인한 사용자 ID
    
    Returns:
        List[Message]: 검색된 메시지 목록
    """
    # 키워드가 없으면 빈 목록 반환
    if not keyword:
        return []
    
    # 현재 사용자가 참여한 채팅방 목록 조회
    chatrooms = db.query(ChatroomDB).all()
    user_chatrooms = []
    
    for chatroom in chatrooms:
        try:
            participants = json.loads(chatroom.participants)
            if current_user_id in participants:
                user_chatrooms.append(chatroom.id)
        except:
            continue
    
    if not user_chatrooms:
        return []
    
    # 검색 쿼리 실행
    query = db.query(MessageDB)\
        .filter(MessageDB.chatroom_id.in_(user_chatrooms))\
        .filter(MessageDB.content.contains(keyword))\
        .order_by(MessageDB.timestamp.desc())
    
    messages_db = query.limit(50).all()
    
    # DB 객체 목록을 Pydantic 모델 목록으로 변환
    messages = [
        Message(
            id=msg.id,
            senderId=msg.sender_id,
            content=msg.content,
            timestamp=msg.timestamp
        ) for msg in messages_db
    ]
    
    return messages

@router.get("/{room_id}", response_model=List[Message], summary="채팅 내역 조회")
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
        List[Message]: 채팅 메시지 목록
    """
    # 채팅방 존재 여부 확인
    chatroom = get_chatroom_or_404(db, room_id)
    
    # 참가자 확인
    verify_chatroom_participant(chatroom, current_user_id)
    
    # 메시지 조회
    query = db.query(MessageDB)\
        .filter(MessageDB.chatroom_id == room_id)\
        .order_by(MessageDB.timestamp.desc())
    
    messages_db = apply_pagination(query, skip, limit).all()
    
    # DB 객체 목록을 Pydantic 모델 목록으로 변환
    messages = [
        Message(
            id=msg.id,
            senderId=msg.sender_id,
            content=msg.content,
            timestamp=msg.timestamp
        ) for msg in messages_db
    ]
    
    return messages

@router.post("/{room_id}", response_model=Message, status_code=status.HTTP_201_CREATED)
async def send_message(
    room_id: str,
    message_request: MessageRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    채팅방에 새로운 메시지를 전송합니다.
    
    - **room_id**: 채팅방 ID
    - **message**: 전송할 메시지
    - **current_user_id**: 현재 로그인한 사용자 ID
    
    Returns:
        Message: 생성된 메시지 정보
    """
    # 채팅방 존재 여부 확인
    chatroom = get_chatroom_or_404(db, room_id)
    
    # 참가자 확인
    verify_chatroom_participant(chatroom, current_user_id)
    
    # 메시지 생성
    db_message = create_message(db, message_request.content, room_id, current_user_id)
    
    # WebSocket 연결된 사용자들에게 메시지 브로드캐스트
    await connection_manager.broadcast_message(db_message, room_id)
    
    # DB 모델을 API 모델로 변환
    return Message(
        id=db_message.id,
        senderId=db_message.sender_id,
        content=db_message.content,
        timestamp=db_message.timestamp
    )

@router.get("/{room_id}/active-users", summary="현재 접속 중인 사용자 목록")
async def get_active_users(
    room_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    채팅방에 현재 접속 중인 사용자 목록을 조회합니다.
    
    - **room_id**: 채팅방 ID
    - **current_user_id**: 현재 로그인한 사용자 ID
    
    Returns:
        List[str]: 접속 중인 사용자 ID 목록
    """
    # 채팅방 존재 여부 확인
    chatroom = get_chatroom_or_404(db, room_id)
    
    # 참가자 확인
    verify_chatroom_participant(chatroom, current_user_id)
    
    # 접속 중인 사용자 목록 조회
    active_users = connection_manager.get_active_users(room_id)
    
    return {"active_users": active_users}

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
    chatroom = get_chatroom_or_404(db, room_id)
    
    # 참가자 확인
    verify_chatroom_participant(chatroom, current_user_id)
    
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