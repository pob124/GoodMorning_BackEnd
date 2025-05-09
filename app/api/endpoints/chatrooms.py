from fastapi import APIRouter, Depends, Body, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.firebase import get_db
from app.models import Chatroom, User, Coordinate
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter(
    prefix="/chatrooms",
    tags=["채팅방"],
    responses={404: {"description": "Not found"}},
)

class ParticipantCreate(BaseModel):
    uid: str
    coordinate: Coordinate

class ChatroomCreate(BaseModel):
    title: str
    participants: List[ParticipantCreate]

class MessageCreate(BaseModel):
    content: str

class CreateChatroomRequest(BaseModel):
    title: str
    participants: List[str]  # 참여자 ID 목록

# [채팅방] 조건에 맞는 채팅방 목록(검색) 조회
@router.get("/search", response_model=List[Chatroom])
async def search_chatrooms(
    keyword: Optional[str] = Query(None, description="검색할 채팅방 제목"),
    is_active: Optional[bool] = Query(True, description="활성화된 채팅방만 검색"),
    min_participants: Optional[int] = Query(None, description="최소 참여자 수"),
    max_participants: Optional[int] = Query(None, description="최대 참여자 수"),
    skip: int = Query(0, description="건너뛸 결과 수"),
    limit: int = Query(20, description="반환할 최대 결과 수"),
    db: Session = Depends(get_db)
):
    filter = ChatroomFilter(
        keyword=keyword,
        is_active=is_active,
        min_participants=min_participants,
        max_participants=max_participants
    )
    return await ChatroomService.search_chatrooms(db, filter, skip, limit)

# [채팅방] 채팅방 생성
@router.post("/", response_model=Chatroom, status_code=201)
async def create_chatroom(
    request: CreateChatroomRequest,
    db: Session = Depends(get_db)
):
    """새로운 채팅방을 생성합니다."""
    # TODO: Firebase 인증 토큰에서 사용자 ID를 가져오는 로직 구현 필요
    current_user_id = "temp_user_id"
    
    # 참여자 확인
    participants = []
    for uid in request.participants:
        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {uid} not found")
        participants.append(user)
    
    # 채팅방 생성
    chatroom = Chatroom(
        title=request.title,
        participants=participants
    )
    db.add(chatroom)
    db.commit()
    db.refresh(chatroom)
    return chatroom

# [채팅방] 특정 채팅방 상세 정보 조회
@router.get("/{chatroom_id}", response_model=Chatroom)
async def get_chatroom(
    chatroom_id: str,
    db: Session = Depends(get_db)
):
    """특정 채팅방의 정보를 조회합니다."""
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    return chatroom

# [채팅방] 채팅방에 메시지 추가
@router.post("/{chatroom_id}/messages", status_code=status.HTTP_201_CREATED, summary="메시지 전송")
async def add_message(
    chatroom_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """채팅방에 메시지를 추가합니다."""
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    
    # TODO: Firebase 인증 토큰에서 사용자 ID를 가져오는 로직 구현 필요
    current_user_id = "temp_user_id"
    
    if current_user_id not in [p.firebase_uid for p in chatroom.participants]:
        raise HTTPException(status_code=403, detail="Not authorized to send message")
    
    # 메시지 생성
    new_message = Message(
        content=message.content,
        chatroom_id=chatroom_id,
        sender_id=current_user_id
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@router.get("/", response_model=List[Chatroom])
async def get_chatrooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """활성화된 채팅방 목록을 조회합니다."""
    chatrooms = db.query(Chatroom).offset(skip).limit(limit).all()
    return chatrooms

@router.delete("/{room_id}", status_code=204)
async def delete_chatroom(
    room_id: str,
    db: Session = Depends(get_db)
):
    """채팅방을 삭제합니다."""
    # TODO: Firebase 인증 토큰에서 사용자 ID를 가져오는 로직 구현 필요
    current_user_id = "temp_user_id"
    
    chatroom = db.query(Chatroom).filter(Chatroom.id == room_id).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    
    # 참여자 확인
    is_participant = any(p.firebase_uid == current_user_id for p in chatroom.participants)
    if not is_participant:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chatroom")
    
    db.delete(chatroom)
    db.commit()
    return None 