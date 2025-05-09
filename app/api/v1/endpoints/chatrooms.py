from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.orm import Session
from app.services.chatroom_service import ChatroomService
from app.database import get_db
from app.dependencies import get_current_user
from app.models.chatroom import LocationModel, ChatroomResponse, ChatroomFilter, ChatroomSearchResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter()

class ParticipantCreate(BaseModel):
    uid: str
    coordinate: LocationModel

class ChatroomCreate(BaseModel):
    title: str
    participants: List[ParticipantCreate]

class MessageCreate(BaseModel):
    content: str

# [채팅방] 조건에 맞는 채팅방 목록(검색) 조회
@router.get("/chatrooms/search", response_model=List[ChatroomSearchResponse])
async def search_chatrooms(
    keyword: Optional[str] = Query(None, description="검색할 채팅방 제목"),
    is_active: Optional[bool] = Query(True, description="활성화된 채팅방만 검색"),
    min_participants: Optional[int] = Query(None, description="최소 참여자 수"),
    max_participants: Optional[int] = Query(None, description="최대 참여자 수"),
    skip: int = Query(0, description="건너뛸 결과 수"),
    limit: int = Query(20, description="반환할 최대 결과 수"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    filter = ChatroomFilter(
        keyword=keyword,
        is_active=is_active,
        min_participants=min_participants,
        max_participants=max_participants
    )
    return await ChatroomService.search_chatrooms(db, filter, current_user_id, skip, limit)

# [채팅방] 채팅방 생성
@router.post("/chatrooms", response_model=ChatroomResponse)
async def create_chatroom(
    chatroom: ChatroomCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    # 현재 사용자가 참여자 목록에 포함되어 있는지 확인
    participant_ids = [p.uid for p in chatroom.participants]
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=400, detail="Current user must be included in participants")
    
    return await ChatroomService.create_chatroom(
        db=db,
        title=chatroom.title,
        participants=[p.dict() for p in chatroom.participants]
    )

# [채팅방] 특정 채팅방 상세 정보 조회
@router.get("/chatrooms/{chatroom_id}", response_model=ChatroomResponse)
async def get_chatroom(
    chatroom_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    return await ChatroomService.get_chatroom(db, chatroom_id)

# [채팅방] 채팅방에 메시지 추가
@router.post("/chatrooms/{chatroom_id}/messages")
async def add_message(
    chatroom_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    return await ChatroomService.add_message(
        db=db,
        chatroom_id=chatroom_id,
        sender_id=current_user_id,
        content=message.content
    ) 