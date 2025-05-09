from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from app.models.chatroom import Chatroom, ChatroomParticipant, Message, ChatroomFilter
from app.models.user import User
from fastapi import HTTPException
from typing import List, Dict, Any
from uuid import uuid4

class ChatroomService:
    @staticmethod
    def _format_participant(participant: ChatroomParticipant) -> Dict[str, Any]:
        return {
            "uid": participant.user.id,
            "nickname": participant.user.nickname,
            "bio": participant.user.bio,
            "profileImageUrl": participant.user.profile_image,
            "likes": participant.user.likes
        }

    @staticmethod
    def _format_location(participant: ChatroomParticipant) -> Dict[str, float]:
        return {
            "latitude": participant.latitude,
            "longitude": participant.longitude
        }

    @staticmethod
    def _format_message(message: Message) -> Dict[str, Any]:
        return {
            "id": message.id,
            "senderId": message.sender_id,
            "content": message.content,
            "timestamp": message.timestamp
        }

    @staticmethod
    def _format_search_response(chatroom: Chatroom, current_user_id: str = None) -> Dict[str, Any]:
        # 마지막 메시지 조회
        last_message = None
        if chatroom.messages:
            last_message = ChatroomService._format_message(chatroom.messages[0])

        # 안 읽은 메시지 수 계산 (현재 사용자 관련)
        unread_count = 0
        if current_user_id:
            # 이 부분은 실제 구현 시 읽은 메시지를 추적하는 테이블이 필요
            pass

        return {
            "id": chatroom.id,
            "title": chatroom.title,
            "participant_count": chatroom.participant_count,
            "participants": [ChatroomService._format_participant(p) for p in chatroom.participants],
            "connection": [ChatroomService._format_location(p) for p in chatroom.participants],
            "createdAt": chatroom.created_at,
            "last_message": last_message,
            "unread_count": unread_count
        }

    @staticmethod
    async def search_chatrooms(
        db: Session,
        filter: ChatroomFilter,
        current_user_id: str = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        # 기본 쿼리 생성 (필요한 관계만 조인)
        query = db.query(Chatroom).options(
            joinedload(Chatroom.participants).joinedload(ChatroomParticipant.user),
            joinedload(Chatroom.messages).limit(1)  # 마지막 메시지만 로드
        )

        # 활성화 상태 필터
        if filter.is_active is not None:
            query = query.filter(Chatroom.is_active == filter.is_active)

        # 키워드 검색 (제목)
        if filter.keyword:
            query = query.filter(Chatroom.title.ilike(f"%{filter.keyword}%"))

        # 참여자 수 필터
        if filter.min_participants is not None:
            query = query.filter(Chatroom.participant_count >= filter.min_participants)
        if filter.max_participants is not None:
            query = query.filter(Chatroom.participant_count <= filter.max_participants)

        # 정렬 (최근 메시지 순)
        query = query.order_by(Chatroom.last_message_at.desc())

        # 페이지네이션
        chatrooms = query.offset(skip).limit(limit).all()
        
        return [ChatroomService._format_search_response(chatroom, current_user_id) for chatroom in chatrooms]

    @staticmethod
    async def create_chatroom(
        db: Session,
        title: str,
        participants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # Create chatroom
        chatroom = Chatroom(
            id=str(uuid4()),
            title=title,
            participant_count=len(participants)
        )
        db.add(chatroom)
        
        # Add participants
        for participant in participants:
            user = db.query(User).filter(User.id == participant["uid"]).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User {participant['uid']} not found")
            
            chatroom_participant = ChatroomParticipant(
                id=str(uuid4()),
                chatroom_id=chatroom.id,
                user_id=user.id,
                latitude=participant["coordinate"]["latitude"],
                longitude=participant["coordinate"]["longitude"]
            )
            db.add(chatroom_participant)
        
        db.commit()
        db.refresh(chatroom)
        
        return ChatroomService._format_search_response(chatroom)

    @staticmethod
    async def get_chatroom(db: Session, chatroom_id: str) -> Dict[str, Any]:
        chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
        if not chatroom:
            raise HTTPException(status_code=404, detail="Chatroom not found")
        return ChatroomService._format_search_response(chatroom)

    @staticmethod
    async def add_message(
        db: Session,
        chatroom_id: str,
        sender_id: str,
        content: str
    ) -> Dict[str, Any]:
        # Verify chatroom exists
        chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
        if not chatroom:
            raise HTTPException(status_code=404, detail="Chatroom not found")
        
        # Verify sender is a participant
        participant = db.query(ChatroomParticipant).filter(
            ChatroomParticipant.chatroom_id == chatroom_id,
            ChatroomParticipant.user_id == sender_id
        ).first()
        if not participant:
            raise HTTPException(status_code=403, detail="User is not a participant in this chatroom")
        
        # Create message
        message = Message(
            id=str(uuid4()),
            chatroom_id=chatroom_id,
            sender_id=sender_id,
            content=content
        )
        db.add(message)
        
        # Update chatroom's last_message_at
        chatroom.last_message_at = func.now()
        
        db.commit()
        db.refresh(message)
        
        return ChatroomService._format_message(message) 