"""10_7_dashboard_widget_columns_variable

Revision ID: 24eb2df31bbe
Revises: 5b33195692ea
Create Date: 2020-08-17 14:41:31.008376

"""

# revision identifiers, used by Alembic.
revision = '24eb2df31bbe'
down_revision = '5b33195692ea'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('dashboard_extraction_associations', sa.Column('columns', sa.Integer(), nullable=False, server_default='4'))


def downgrade():
    op.drop_column('dashboard_extraction_associations', 'columns')
