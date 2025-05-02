from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models import UserDB as User, ChatroomDB, ParticipantDB, MessageDB
from app.models import UpdateMyPageRequest, CreateChatroomRequest, UpdateChatroomRequest, Chatroom, Message, Participant, Coordinate
from app.config import get_settings
from app.auth.utils import get_current_user, verify_token
from app.services import get_db
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import uuid

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    # 추가 프로필 필드
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(token_data: dict = Depends(verify_token)):
    """현재 인증된 사용자 정보를 반환합니다. DB에 저장하지 않고 토큰 정보만 사용."""
    try:
        # 토큰에서 직접 사용자 정보 반환 (DB 조회 없음)
        return {
            "id": token_data["firebase_uid"],  # Firebase UID를 ID로 사용
            "email": token_data["email"],
            "name": token_data["name"],
            "username": None,  # Firebase에서 제공하지 않는 정보는 기본값 사용
            "is_active": True,
            "profile_picture": None,
            "bio": None,
            "phone_number": None,
            "location": None,
            "gender": None,
            "birth_date": None,
            "last_login_at": None
        }
    except Exception as e:
        logger.error(f"Error in read_users_me: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보를 가져오는 중 오류 발생: {str(e)}"
        )

@router.post("/users/me", response_model=UserResponse)
async def update_users_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 인증된 사용자 정보를 업데이트합니다."""
    # 업데이트할 필드만 처리
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "username": current_user.username,
        "is_active": current_user.is_active
    }

@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 인증된 사용자 계정을 비활성화합니다."""
    current_user.is_active = False
    db.commit()
    return {"detail": "계정이 비활성화되었습니다"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "app_name": settings.APP_NAME}

# 마이페이지 엔드포인트
@router.patch("/mypage")
async def update_mypage(
    request: UpdateMyPageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 마이페이지 정보를 수정합니다."""
    if request.name:
        current_user.name = request.name
    if request.bio:
        current_user.bio = request.bio
    if request.profileImageUrl:
        current_user.profile_picture = request.profileImageUrl
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "profile_picture": current_user.profile_picture,
        "bio": current_user.bio,
        "phone_number": current_user.phone_number,
        "location": current_user.location,
        "gender": current_user.gender,
        "birth_date": current_user.birth_date
    }

# 채팅방 엔드포인트
@router.post("/chatrooms", status_code=201, response_model=Chatroom)
async def create_chatroom(
    request: CreateChatroomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새로운 채팅방을 생성합니다."""
    # 채팅방 생성
    new_chatroom = ChatroomDB(
        title=request.title
    )
    db.add(new_chatroom)
    db.flush()
    
    # 참여자 추가
    participants = []
    
    # 현재 사용자를 첫 번째 참여자로 추가
    participant1 = request.participants[0]
    current_user_participant = ParticipantDB(
        chatroom_id=new_chatroom.id,
        user_id=current_user.id,
        latitude=participant1.coordinate.latitude,
        longitude=participant1.coordinate.longitude
    )
    db.add(current_user_participant)
    
    # 두 번째 참여자 추가
    participant2 = request.participants[1]
    # 사용자 ID 조회
    second_user = db.query(User).filter(User.firebase_uid == participant2.userId).first()
    if not second_user:
        raise HTTPException(status_code=400, detail="두 번째 참여자를 찾을 수 없습니다.")
    
    second_participant = ParticipantDB(
        chatroom_id=new_chatroom.id,
        user_id=second_user.id,
        latitude=participant2.coordinate.latitude,
        longitude=participant2.coordinate.longitude
    )
    db.add(second_participant)
    
    db.commit()
    db.refresh(new_chatroom)
    
    # 응답 구성
    participant_models = []
    for participant in [current_user_participant, second_participant]:
        user = db.query(User).filter(User.id == participant.user_id).first()
        participant_models.append(
            Participant(
                userId=str(user.firebase_uid),
                coordinate=Coordinate(
                    latitude=participant.latitude,
                    longitude=participant.longitude
                )
            )
        )
    
    return Chatroom(
        id=str(new_chatroom.id),
        title=new_chatroom.title,
        participants=participant_models,
        createdAt=new_chatroom.created_at
    )

@router.get("/chatrooms", response_model=List[Chatroom])
async def get_chatrooms(db: Session = Depends(get_db)):
    """활성화된 채팅방 목록을 조회합니다."""
    chatrooms = db.query(ChatroomDB).filter(ChatroomDB.is_active == True).all()
    
    result = []
    for chatroom in chatrooms:
        participants_db = db.query(ParticipantDB).filter(ParticipantDB.chatroom_id == chatroom.id).all()
        participants = []
        
        for participant_db in participants_db:
            user = db.query(User).filter(User.id == participant_db.user_id).first()
            participants.append(
                Participant(
                    userId=str(user.firebase_uid),
                    coordinate=Coordinate(
                        latitude=participant_db.latitude,
                        longitude=participant_db.longitude
                    )
                )
            )
        
        result.append(
            Chatroom(
                id=str(chatroom.id),
                title=chatroom.title,
                participants=participants,
                createdAt=chatroom.created_at
            )
        )
    
    return result

@router.get("/chatrooms/{room_id}", status_code=204)
async def get_chatroom(room_id: str, db: Session = Depends(get_db)):
    """채팅방을 조회합니다."""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 채팅방 ID입니다.")
    
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_uuid).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    return {}

@router.patch("/chatrooms/{room_id}", status_code=200)
async def update_chatroom(
    room_id: str, 
    request: UpdateChatroomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅방 정보를 수정합니다."""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 채팅방 ID입니다.")
    
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_uuid).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    # 참여자 확인
    participant = db.query(ParticipantDB).filter(
        ParticipantDB.chatroom_id == room_uuid,
        ParticipantDB.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="이 채팅방의 참여자만 수정할 수 있습니다.")
    
    # 채팅방 정보 업데이트
    if request.title:
        chatroom.title = request.title
    
    db.commit()
    
    return {}

@router.delete("/chatrooms/{room_id}", status_code=204)
async def delete_chatroom(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅방을 삭제합니다."""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 채팅방 ID입니다.")
    
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_uuid).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    # 참여자 확인
    participant = db.query(ParticipantDB).filter(
        ParticipantDB.chatroom_id == room_uuid,
        ParticipantDB.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="이 채팅방의 참여자만 삭제할 수 있습니다.")
    
    # 채팅방 비활성화 (소프트 삭제)
    chatroom.is_active = False
    db.commit()
    
    return {}

@router.get("/chatrooms/{room_id}/messages", response_model=List[Message])
async def get_messages(
    room_id: str,
    search: Optional[str] = None,
    limit: Optional[int] = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅방 메시지를 검색합니다."""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 채팅방 ID입니다.")
    
    # 채팅방 존재 확인
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_uuid).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    # 참여자 확인
    participant = db.query(ParticipantDB).filter(
        ParticipantDB.chatroom_id == room_uuid,
        ParticipantDB.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="이 채팅방의 참여자만 메시지를 조회할 수 있습니다.")
    
    # 메시지 쿼리
    query = db.query(MessageDB).filter(MessageDB.chatroom_id == room_uuid)
    
    # 검색어가 있으면 필터링
    if search:
        query = query.filter(MessageDB.content.ilike(f"%{search}%"))
    
    # 최신순으로 정렬하고 제한
    messages = query.order_by(MessageDB.timestamp.desc()).limit(limit).all()
    
    # 응답 변환
    result = []
    for msg in messages:
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        result.append(
            Message(
                id=str(msg.id),
                senderId=str(sender.firebase_uid),
                content=msg.content,
                timestamp=msg.timestamp
            )
        )
    
    return result

@router.post("/chatrooms/{room_id}/messages")
async def create_message(
    room_id: str,
    content: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅방에 메시지를 저장합니다."""
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 채팅방 ID입니다.")
    
    # 채팅방 존재 확인
    chatroom = db.query(ChatroomDB).filter(ChatroomDB.id == room_uuid).first()
    if not chatroom:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    # 참여자 확인
    participant = db.query(ParticipantDB).filter(
        ParticipantDB.chatroom_id == room_uuid,
        ParticipantDB.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="이 채팅방의 참여자만 메시지를 보낼 수 있습니다.")
    
    # 메시지 생성
    new_message = MessageDB(
        chatroom_id=room_uuid,
        sender_id=current_user.id,
        content=content
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return {
        "id": str(new_message.id),
        "senderId": str(current_user.firebase_uid),
        "content": new_message.content,
        "timestamp": new_message.timestamp
    } 