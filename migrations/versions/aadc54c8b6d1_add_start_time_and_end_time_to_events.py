"""Add start_time and end_time to events

Revision ID: aadc54c8b6d1
Revises: 
Create Date: 2025-04-20 21:03:47.910347

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aadc54c8b6d1'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_time', sa.String(length=20), nullable=True))  # Change to nullable
        batch_op.add_column(sa.Column('end_time', sa.String(length=20), nullable=True))   # 


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.drop_column('end_time')
        batch_op.drop_column('start_time')

    # ### end Alembic commands ###
