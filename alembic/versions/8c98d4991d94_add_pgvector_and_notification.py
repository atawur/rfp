"""Add pgvector and notification_receive

Revision ID: 8c98d4991d94
Revises: 7b97c3880c83
Create Date: 2026-09-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '8c98d4991d94'
down_revision: Union[str, None] = '7b97c3880c83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    
    # Add notification_receive to user
    op.add_column('user', sa.Column('notification_receive', sa.Boolean(), server_default='false', nullable=True))
    
    # Add embedding to rfp
    op.add_column('rfp', sa.Column('embedding', Vector(dim=384), nullable=True))


def downgrade() -> None:
    # Remove embedding from rfp
    op.drop_column('rfp', 'embedding')
    
    # Remove notification_receive from user
    op.drop_column('user', 'notification_receive')
    
    # Drop vector extension (optional, but good practice if it's the only usage)
    # op.execute('DROP EXTENSION IF EXISTS vector;')
