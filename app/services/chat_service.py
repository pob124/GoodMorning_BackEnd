from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.chat import Chat
from typing import List

class ChatService:
    @staticmethod
    async def create_chat(db: Session, sender_id: str, receiver_id: str, message: str) -> Chat:
        chat = Chat(
            id=str(uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    @staticmethod
    async def get_chat_history(db: Session, user_id: str) -> List[Chat]:
        return db.query(Chat).filter(
            (Chat.sender_id == user_id) | (Chat.receiver_id == user_id)
        ).order_by(Chat.created_at.desc()).all()

    @staticmethod
    async def get_chat_between_users(db: Session, user1_id: str, user2_id: str) -> List[Chat]:
        return db.query(Chat).filter(
            ((Chat.sender_id == user1_id) & (Chat.receiver_id == user2_id)) |
            ((Chat.sender_id == user2_id) & (Chat.receiver_id == user1_id))
        ).order_by(Chat.created_at.desc()).all() 