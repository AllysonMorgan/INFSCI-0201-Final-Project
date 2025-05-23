"""Add time field to events

Revision ID: e9a582944a16
Revises: 6e9d9e88134b
Create Date: 2025-04-20 21:45:55.165657

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9a582944a16'
down_revision = '6e9d9e88134b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('time', sa.String(length=20), nullable=False))
        batch_op.alter_column('start_time',
               existing_type=sa.TIME(),
               type_=sa.String(length=20),
               existing_nullable=True)
        batch_op.alter_column('end_time',
               existing_type=sa.TIME(),
               type_=sa.String(length=20),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.alter_column('end_time',
               existing_type=sa.String(length=20),
               type_=sa.TIME(),
               existing_nullable=True)
        batch_op.alter_column('start_time',
               existing_type=sa.String(length=20),
               type_=sa.TIME(),
               existing_nullable=True)
        batch_op.drop_column('time')

    # ### end Alembic commands ###
