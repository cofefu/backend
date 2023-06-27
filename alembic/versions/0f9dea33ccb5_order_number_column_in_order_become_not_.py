"""order_number column in Order become not null

Revision ID: 0f9dea33ccb5
Revises: 8f7aa2b53518
Create Date: 2023-06-11 03:18:13.553983

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0f9dea33ccb5'
down_revision = '8f7aa2b53518'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('orders', 'order_number', nullable=False)


def downgrade() -> None:
    op.alter_column('orders', 'order_number', nullable=True)
