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
    # 생성자만 참여자로 추가 (다른 사용자는 나중에 참여 가능)
    participants = [current_user_id]
    
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
        participants=json.dumps(participants),  # 생성자만 포함
        connection=json.dumps([coord.dict() for coord in request.connection])  # 좌표 정보를 JSON으로 저장
    )
    
    db.add(chatroom)
    db.commit()
    db.refresh(chatroom)
    
    # 생성자 정보 조회
    user_profiles = []
    user = db.query(UserDB).filter(UserDB.firebase_uid == current_user_id).first()
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
        Message=[]  # 생성 시점에는 메시지가 없음
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

# [채팅방] 채팅방 참여
@router.post("/{room_id}/join", response_model=Chatroom, status_code=200)
async def join_chatroom(
    room_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """채팅방에 참여합니다."""
    # 채팅방 존재 여부 확인
    chatroom = get_chatroom_or_404(db, room_id)
    
    # 현재 참여자 목록 가져오기
    current_participants = json.loads(chatroom.participants) if chatroom.participants else []
    
    # 이미 참여 중인지 확인
    if current_user_id in current_participants:
        # 이미 참여 중이어도 에러가 아니라 현재 채팅방 정보를 반환
        pass
    else:
        # 새로운 참여자 추가
        current_participants.append(current_user_id)
        
        # DB 업데이트
        chatroom.participants = json.dumps(current_participants)
        chatroom.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(chatroom)
    
    # 참여자 정보 조회
    user_profiles = []
    for uid in current_participants:
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
    
    # 채팅방 정보 반환
    return Chatroom(
        id=chatroom.id,
        title=chatroom.title,
        participants=user_profiles,
        connection=json.loads(chatroom.connection) if chatroom.connection else [],
        createdAt=chatroom.created_at,
        Message=message_models
    )

# [채팅방] 채팅방 나가기
@router.post("/{room_id}/leave", status_code=200)
async def leave_chatroom(
    room_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """채팅방에서 나갑니다."""
    # 채팅방 존재 여부 확인
    chatroom = get_chatroom_or_404(db, room_id)
    
    # 현재 참여자 목록 가져오기
    current_participants = json.loads(chatroom.participants) if chatroom.participants else []
    
    # 참여 중인지 확인
    if current_user_id not in current_participants:
        raise HTTPException(status_code=400, detail="You are not a participant in this chatroom")
    
    # 참여자 목록에서 제거
    current_participants.remove(current_user_id)
    
    # DB 업데이트
    chatroom.participants = json.dumps(current_participants)
    chatroom.updated_at = datetime.utcnow()
    
    # 참여자가 모두 나가면 채팅방 비활성화
    if not current_participants:
        chatroom.is_active = False
    
    db.commit()
    
    return {"message": "Successfully left the chatroom"}

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