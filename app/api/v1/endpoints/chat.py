from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.services.chat_service import ChatService
from app.database import get_db
from pydantic import BaseModel

router = APIRouter()

class ChatCreate(BaseModel):
    receiver_id: str
    message: str

# [채팅] 1:1 채팅 메시지 전송
@router.post("/send")
async def send_message(
    chat: ChatCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    # 현재 사용자 -> 상대방에게 메시지 전송
    return await ChatService.create_chat(
        db=db,
        sender_id=current_user_id,
        receiver_id=chat.receiver_id,
        message=chat.message
    )

# [채팅] 특정 사용자와의 채팅 내역 조회
@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    # 현재 사용자와 user_id 간의 채팅 내역 반환
    return await ChatService.get_chat_between_users(db, current_user_id, user_id) 