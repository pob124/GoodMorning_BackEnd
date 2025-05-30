"""Create default chatrooms

Revision ID: create_default_chatrooms
Revises: 
Create Date: 2024-01-15 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime
import json
import uuid

# revision identifiers
revision = 'create_default_chatrooms'
down_revision = '60f216c54686_add_chatroom_and_message_models'  # 실제 존재하는 마이그레이션 ID로 변경
branch_labels = None
depends_on = None

def upgrade():
    # 임시 테이블 구조 정의
    chatrooms_table = table('chatrooms',
        column('id', sa.String),
        column('title', sa.String),
        column('description', sa.Text),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime),
        column('created_by', sa.String),
        column('participants', sa.Text),
        column('connection', sa.Text),
        column('is_active', sa.Boolean)
    )
    
    # 기본 채팅방 데이터
    default_chatrooms = [
        {
            'id': str(uuid.uuid4()),
            'title': '🌍 전국 모임방',
            'description': '전국 어디서든 함께 할 수 있는 모임을 만들어보세요!',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'created_by': 'system',
            'participants': json.dumps([]),
            'connection': json.dumps([
                {"latitude": 37.5665, "longitude": 126.9780}  # 서울 시청
            ]),
            'is_active': True
        },
        {
            'id': str(uuid.uuid4()),
            'title': '🏃‍♂️ 러닝 크루',
            'description': '함께 달리며 건강한 아침을 만들어요!',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'created_by': 'system',
            'participants': json.dumps([]),
            'connection': json.dumps([
                {"latitude": 37.5665, "longitude": 126.9780},  # 서울 시청
                {"latitude": 37.5641, "longitude": 126.9769}   # 청계천
            ]),
            'is_active': True
        },
        {
            'id': str(uuid.uuid4()),
            'title': '☕ 카페 투어',
            'description': '맛있는 커피와 함께하는 모닝 카페 투어',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'created_by': 'system',
            'participants': json.dumps([]),
            'connection': json.dumps([
                {"latitude": 37.5173, "longitude": 127.0473}  # 강남역
            ]),
            'is_active': True
        },
        {
            'id': str(uuid.uuid4()),
            'title': '🧘‍♀️ 요가 모임',
            'description': '상쾌한 아침 요가로 하루를 시작해요',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'created_by': 'system',
            'participants': json.dumps([]),
            'connection': json.dumps([
                {"latitude": 37.5326, "longitude": 126.9904}  # 한강공원
            ]),
            'is_active': True
        },
        {
            'id': str(uuid.uuid4()),
            'title': '📚 독서 클럽',
            'description': '책과 함께하는 지적인 아침 시간',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'created_by': 'system',
            'participants': json.dumps([]),
            'connection': json.dumps([
                {"latitude": 37.5700, "longitude": 126.9781}  # 광화문 교보문고
            ]),
            'is_active': True
        }
    ]
    
    # 데이터 삽입
    op.bulk_insert(chatrooms_table, default_chatrooms)

def downgrade():
    # 시스템이 생성한 기본 채팅방들 삭제
    op.execute("DELETE FROM chatrooms WHERE created_by = 'system'") 