"""rename ToppingToProduct to Topping2OrderedProduct

Revision ID: d3cc16c77435
Revises: 9031bcb1597f
Create Date: 2023-04-28 01:08:38.946417

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3cc16c77435'
down_revision = '9031bcb1597f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table('toppingtoproducts', 'topping2orderedproducts')


def downgrade() -> None:
    op.rename_table('topping2orderedproducts', 'toppingtoproducts')
