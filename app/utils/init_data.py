from sqlalchemy.orm import Session
from app.models.chatroom import ChatroomDB
from app.core.firebase import get_db
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def create_default_chatrooms(db: Session) -> None:
    """애플리케이션 시작 시 기본 채팅방들을 생성합니다."""
    
    # 이미 시스템 채팅방이 있는지 확인
    existing_system_chatrooms = db.query(ChatroomDB).filter(
        ChatroomDB.created_by == 'system'
    ).count()
    
    if existing_system_chatrooms > 0:
        logger.info(f"기본 채팅방이 이미 {existing_system_chatrooms}개 존재합니다.")
        return
    
    # 기본 채팅방 데이터 정의
    default_chatrooms_data = [
        {
            'title': '🌍 전국 모임방',
            'description': '전국 어디서든 함께 할 수 있는 모임을 만들어보세요!',
            'connection': [
                {"latitude": 37.5665, "longitude": 126.9780}  # 서울 시청
            ]
        },
        {
            'title': '🏃‍♂️ 러닝 크루',
            'description': '함께 달리며 건강한 아침을 만들어요!',
            'connection': [
                {"latitude": 37.5665, "longitude": 126.9780},  # 서울 시청
                {"latitude": 37.5641, "longitude": 126.9769}   # 청계천
            ]
        },
        {
            'title': '☕ 카페 투어', 
            'description': '맛있는 커피와 함께하는 모닝 카페 투어',
            'connection': [
                {"latitude": 37.5173, "longitude": 127.0473}  # 강남역
            ]
        },
        {
            'title': '🧘‍♀️ 요가 모임',
            'description': '상쾌한 아침 요가로 하루를 시작해요',
            'connection': [
                {"latitude": 37.5326, "longitude": 126.9904}  # 한강공원
            ]
        },
        {
            'title': '📚 독서 클럽',
            'description': '책과 함께하는 지적인 아침 시간',
            'connection': [
                {"latitude": 37.5700, "longitude": 126.9781}  # 광화문 교보문고
            ]
        },
        {
            'title': '🚴‍♂️ 자전거 라이딩',
            'description': '상쾌한 바람과 함께하는 아침 라이딩',
            'connection': [
                {"latitude": 37.5286, "longitude": 126.9340}  # 여의도 한강공원
            ]
        },
        {
            'title': '🎨 그림 그리기',
            'description': '아름다운 풍경을 그리며 여유로운 아침',
            'connection': [
                {"latitude": 37.5792, "longitude": 126.9770}  # 경복궁
            ]
        },
        {
            'title': '🍳 요리 모임',
            'description': '건강한 아침 식사를 함께 만들어요',
            'connection': [
                {"latitude": 37.5515, "longitude": 126.9882}  # 이태원
            ]
        }
    ]
    
    created_count = 0
    
    try:
        for chatroom_data in default_chatrooms_data:
            # 채팅방 생성
            new_chatroom = ChatroomDB(
                id=str(uuid.uuid4()),
                title=chatroom_data['title'],
                description=chatroom_data['description'],
                created_by='system',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True,
                participants=json.dumps([]),  # 빈 참여자 목록으로 시작
                connection=json.dumps(chatroom_data['connection'])
            )
            
            db.add(new_chatroom)
            created_count += 1
        
        db.commit()
        logger.info(f"기본 채팅방 {created_count}개가 성공적으로 생성되었습니다.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"기본 채팅방 생성 중 오류 발생: {str(e)}")
        raise

def get_default_chatrooms_sample() -> List[Dict[str, Any]]:
    """기본 채팅방 샘플 데이터를 반환합니다. (테스트용)"""
    return [
        {
            'title': '테스트 채팅방',
            'description': '테스트용 채팅방입니다.',
            'connection': [
                {"latitude": 37.5665, "longitude": 126.9780}
            ]
        }
    ]

async def init_application_data():
    """애플리케이션 초기화 시 실행되는 함수"""
    try:
        # DB 세션 생성
        from app.core.firebase import get_db
        db = next(get_db())
        
        # 기본 채팅방 생성
        create_default_chatrooms(db)
        
        logger.info("애플리케이션 초기 데이터 설정이 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"애플리케이션 초기화 중 오류 발생: {str(e)}")
    finally:
        if 'db' in locals():
            db.close() 