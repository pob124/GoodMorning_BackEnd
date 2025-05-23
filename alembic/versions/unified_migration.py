"""Unified schema migration

Revision ID: unified_schema
Revises: 
Create Date: 2025-05-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'unified_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables in a single migration."""
    
    # 1. Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('firebase_uid', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True, default=0),
        # 프로필 관련 필드 (API 문서에 맞춤)
        sa.Column('nickname', sa.String(), nullable=True),
        sa.Column('profile_picture', sa.String(), nullable=True),
        sa.Column('bio', sa.String(), nullable=True),
        sa.Column('profile_image_url', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('birth_date', sa.DateTime(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        # 로그인 관련 필드
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)
    
    # 2. Create chatrooms table (API 문서에 맞춤)
    op.create_table('chatrooms',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=False),
        sa.Column('participants', sa.Text(), nullable=True),
        sa.Column('connection', sa.Text(), nullable=True),  # 좌표 정보를 JSON으로 저장
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatrooms_id'), 'chatrooms', ['id'], unique=False)
    
    # 3. Create messages table (API 문서에 맞춤)
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chatroom_id', sa.String(), nullable=True),
        sa.Column('sender_id', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['chatroom_id'], ['chatrooms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_chatroom_id'), 'messages', ['chatroom_id'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse order."""
    # 1. Drop messages table
    op.drop_index(op.f('ix_messages_chatroom_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    
    # 2. Drop chatrooms table
    op.drop_index(op.f('ix_chatrooms_id'), table_name='chatrooms')
    op.drop_table('chatrooms')
    
    # 3. Drop users table
    op.drop_index(op.f('ix_users_firebase_uid'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users') 