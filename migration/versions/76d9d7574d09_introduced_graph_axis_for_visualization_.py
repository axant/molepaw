"""Introduced graph_axis for visualization with graphs

Revision ID: 76d9d7574d09
Revises: 331ace739944
Create Date: 2018-06-12 11:24:52.838646

"""

# revision identifiers, used by Alembic.
revision = '76d9d7574d09'
down_revision = '331ace739944'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column('extractions', sa.Column('graph_axis', sa.Unicode(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    op.drop_column('extractions', 'graph_axis')
    # ### end Alembic commands ###
