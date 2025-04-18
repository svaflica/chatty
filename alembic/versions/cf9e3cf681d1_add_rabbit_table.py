"""add rabbit table

Revision ID: cf9e3cf681d1
Revises: 82602e6e7bf6
Create Date: 2025-04-03 10:46:59.668870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf9e3cf681d1'
down_revision: Union[str, None] = '82602e6e7bf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rabbit_message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message_id', sa.String(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rabbit_message_id'), 'rabbit_message', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_rabbit_message_id'), table_name='rabbit_message')
    op.drop_table('rabbit_message')
    # ### end Alembic commands ###
