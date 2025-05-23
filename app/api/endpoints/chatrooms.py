from fastapi import APIRouter, Depends, Body, Query, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.schemas.chatroom import CreateChatroomRequest, Chatroom, ChatroomFilter, Coordinate, UserProfile, Message

from app.core.firebase import get_db, get_current_user_id
from app.models.user_models import UserDB
from app.models.chatroom import MessageDB, ChatroomDB
from app.utils.utils import get_chatroom_or_404, apply_pagination, filter_chatrooms, create_message, verify_chatroom_participant, connection_manager
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/chatrooms",
    tags=["채팅방"],
    responses={404: {"description": "Not found"}},
)

# [채팅방] 조건에 맞는 채팅방 목록(검색) 조회
@router.get("/search", response_model=List[Chatroom])
async def search_chatrooms(
    keyword: Optional[str] = Query(None, description="검색할 채팅방 제목"),
    is_active: Optional[bool] = Query(True, description="활성화된 채팅방만 검색"),
    skip: int = Query(0, description="건너뛸 결과 수"),
    limit: int = Query(20, description="반환할 최대 결과 수"),
    db: Session = Depends(get_db)
):
    """키워드 기반으로 채팅방을 검색합니다."""
    # ChatroomFilter 사용
    filter_params = ChatroomFilter(
        keyword=keyword,
        is_active=is_active
    )
    
    query = db.query(ChatroomDB)
    query = filter_chatrooms(query, filter_params.dict())
    chatrooms_db = apply_pagination(query, skip, limit).all()
    
    # DB 객체 목록을 Pydantic 모델 목록으로 변환
    result = []
    for chatroom in chatrooms_db:
        # 참가자 정보 조회
        participant_ids = json.loads(chatroom.participants) if chatroom.participants else []
        user_profiles = []
        for uid in participant_ids:
            user = db.query(UserDB).filter(UserDB.firebase_uid == uid).first()
            if user:
                user_profiles.append(UserProfile(
                    uid=user.firebase_uid,
                    nickname=user.name,
                    bio=user.bio,
                    profileImageUrl=user.profile_picture,
                    likes=user.likes or 0
                ))
        
        # 최근 메시지 조회
        messages = db.query(MessageDB).filter(MessageDB.chatroom_id == chatroom.id).order_by(MessageDB.timestamp.desc()).limit(10).all()
        message_models = [Message(
            id=msg.id,
            senderId=msg.sender_id,
            content=msg.content,
            timestamp=msg.timestamp
        ) for msg in messages]
        
        result.append(Chatroom(
            id=str(chatroom.id),
            title=chatroom.title,
            participants=user_profiles,
            connection=json.loads(chatroom.connection) if chatroom.connection else [],
            createdAt=chatroom.created_at,
            Message=message_models  # API.yaml에 맞춰 "Message"로 변경
        ))
    
    return result

# [채팅방] 채팅방 생성
@router.post("/", response_model=Chatroom, status_code=201)
async def create_chatroom(
    request: CreateChatroomRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """새로운 채팅방을 생성합니다."""
    # 참여자 확인 및 저장
    participants = [current_user_id]  # 생성자는 항상 참여자에 포함
    
    for uid in request.participants:
        if uid != current_user_id:
            user = db.query(UserDB).filter(UserDB.firebase_uid == uid).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User {uid} not found")
            participants.append(uid)
    
    # 채팅방 ID 생성
    chatroom_id = str(uuid.uuid4())
    
    # 채팅방 생성
    chatroom = ChatroomDB(
        id=chatroom_id,
        title=request.title,
        created_by=current_user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True,
        participants=json.dumps(participants),  # 참여자 목록을 JSON 문자열로 저장
        connection=json.dumps([coord.dict() for coord in request.connection])  # 좌표 정보를 JSON으로 저장
    )
    
    db.add(chatroom)
    db.commit()
    db.refresh(chatroom)
    
    # 참가자 정보 조회
    user_profiles = []
    for uid in participants:
        user = db.query(UserDB).filter(UserDB.firebase_uid == uid).first()
        if user:
            user_profiles.append(UserProfile(
                uid=user.firebase_uid,
                nickname=user.name,
                bio=user.bio,
                profileImageUrl=user.profile_picture,
                likes=user.likes or 0
            ))
    
    # DB 객체를 Pydantic 모델에 맞게 변환
    response_chatroom = Chatroom(
        id=chatroom.id,
        title=chatroom.title,
        participants=user_profiles,
        connection=request.connection,
        createdAt=chatroom.created_at,
        Message=[]  # API.yaml에 맞춰 "Message"로 변경
    )
    
    return response_chatroom

# [채팅방] 특정 채팅방 상세 정보 조회
@router.get("/{chatroom_id}", response_model=Chatroom, status_code=200)
async def get_chatroom(
    chatroom_id: str,
    db: Session = Depends(get_db)
):
    """특정 채팅방의 정보를 조회합니다."""
    chatroom = get_chatroom_or_404(db, chatroom_id)
    
    # 참가자 정보 조회
    participant_ids = json.loads(chatroom.participants) if chatroom.participants else []
    user_profiles = []
    for uid in participant_ids:
        user = db.query(UserDB).filter(UserDB.firebase_uid == uid).first()
        if user:
            user_profiles.append(UserProfile(
                uid=user.firebase_uid,
                nickname=user.name,
                bio=user.bio,
                profileImageUrl=user.profile_picture,
                likes=user.likes or 0
            ))
    
    # 최근 메시지 조회
    messages = db.query(MessageDB).filter(MessageDB.chatroom_id == chatroom.id).order_by(MessageDB.timestamp.desc()).limit(10).all()
    message_models = [Message(
        id=msg.id,
        senderId=msg.sender_id,
        content=msg.content,
        timestamp=msg.timestamp
    ) for msg in messages]
    
    # DB 객체를 Pydantic 모델로 변환
    return Chatroom(
        id=chatroom.id,
        title=chatroom.title,
        participants=user_profiles,
        connection=json.loads(chatroom.connection) if chatroom.connection else [],
        createdAt=chatroom.created_at,
        Message=message_models  # API.yaml에 맞춰 "Message"로 변경
    )

# [채팅방] 활성화된 채팅방 목록 조회
@router.get("/", response_model=List[Chatroom])
async def get_chatrooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """활성화된 채팅방 목록을 조회합니다."""
    query = db.query(ChatroomDB).filter(ChatroomDB.is_active == True)
    chatrooms_db = apply_pagination(query, skip, limit).all()
    
    # DB 객체 목록을 Pydantic 모델 목록으로 변환
    result = []
    for chatroom in chatrooms_db:
        # 참가자 정보 조회
        participant_ids = json.loads(chatroom.participants) if chatroom.participants else []
        user_profiles = []
        for uid in participant_ids:
            user = db.query(UserDB).filter(UserDB.firebase_uid == uid).first()
            if user:
                user_profiles.append(UserProfile(
                    uid=user.firebase_uid,
                    nickname=user.name,
                    bio=user.bio,
                    profileImageUrl=user.profile_picture,
                    likes=user.likes or 0
                ))
        
        # 최근 메시지 조회
        messages = db.query(MessageDB).filter(MessageDB.chatroom_id == chatroom.id).order_by(MessageDB.timestamp.desc()).limit(10).all()
        message_models = [Message(
            id=msg.id,
            senderId=msg.sender_id,
            content=msg.content,
            timestamp=msg.timestamp
        ) for msg in messages]
        
        result.append(Chatroom(
            id=str(chatroom.id),
            title=chatroom.title,
            participants=user_profiles,
            connection=json.loads(chatroom.connection) if chatroom.connection else [],
            createdAt=chatroom.created_at,
            Message=message_models  # API.yaml에 맞춰 "Message"로 변경
        ))
    
    return result

# [채팅방] 채팅방 삭제
@router.delete("/{room_id}", status_code=204)
async def delete_chatroom(
    room_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """채팅방을 삭제합니다."""
    # 채팅방 존재 여부 확인
    chatroom = get_chatroom_or_404(db, room_id)
    
    # 채팅방 참여자인지 확인
    verify_chatroom_participant(chatroom, current_user_id)
    
    # 채팅방 삭제
    db.delete(chatroom)
    db.commit()
    
    return None

# WebSocket 엔드포인트 추가
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str = None):
    """
    WebSocket 채팅 엔드포인트
    
    이 엔드포인트는 실시간 채팅을 위한 WebSocket 연결을 제공합니다.
    클라이언트는 메시지를 보내고 받을 수 있으며, 채팅방에 참여한 모든 사용자에게 메시지가 전송됩니다.
    """
    db = next(get_db())
    
    try:
        # 1. 토큰 검증 및 사용자 확인
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
            
        try:
            user_id = await get_current_user_id(token)
        except Exception as e:
            await websocket.close(code=1008, reason="Invalid authentication")
            return
        
        # 2. 채팅방 존재 여부 확인
        try:
            chatroom = get_chatroom_or_404(db, room_id)
        except HTTPException:
            await websocket.close(code=1008, reason="Chatroom not found")
            return
        
        # 3. 참여자 확인
        try:
            verify_chatroom_participant(chatroom, user_id)
        except HTTPException:
            await websocket.close(code=1008, reason="Not authorized to join this chatroom")
            return
        
        # 4. WebSocket 연결 수락
        await connection_manager.connect(websocket, room_id, user_id)
        
        # 5. 메시지 처리 루프
        try:
            while True:
                # 메시지 수신
                data = await websocket.receive_text()
                
                # 메시지 DB 저장
                db_message = create_message(db, data, room_id, user_id)
                
                # 브로드캐스트
                await connection_manager.broadcast_message(db_message, room_id)
                
        except WebSocketDisconnect:
            # 연결 종료 처리
            user_id = connection_manager.disconnect(websocket, room_id)
            if user_id:
                await connection_manager.broadcast(f"User {user_id} left the chat", room_id, "system")
    except Exception as e:
        # 예상치 못한 오류 처리
        try:
            await websocket.close(code=1011, reason=f"Server error: {str(e)}")
        except:
            pass 