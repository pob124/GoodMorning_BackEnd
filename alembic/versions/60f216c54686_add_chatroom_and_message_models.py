"""Add chatroom and message models

Revision ID: 60f216c54686
Revises: f27b67c54611
Create Date: 2025-05-02 06:50:10.825146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60f216c54686'
down_revision: Union[str, None] = 'f27b67c54611'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create chatrooms table
    op.create_table('chatrooms',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(50), nullable=False),
        sa.Column('participants', sa.Text(), nullable=True),  # JSON string
        sa.Column('connection', sa.Text(), nullable=True),    # JSON string
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('chatroom_id', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chatroom_id'], ['chatrooms.id']),
        sa.ForeignKeyConstraint(['sender_id'], ['users.firebase_uid'])
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('messages')
    op.drop_table('chatrooms')
