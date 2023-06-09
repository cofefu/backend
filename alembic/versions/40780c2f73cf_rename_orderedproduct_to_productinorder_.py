"""rename OrderedProduct to ProductInOrder, Topping2OrderedProduct to Topping2ProductInOrder

Revision ID: 40780c2f73cf
Revises: ba77154f75f2
Create Date: 2023-06-09 22:48:41.623410

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '40780c2f73cf'
down_revision = 'ba77154f75f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table('orderedproducts', 'productinorders')
    op.rename_table('topping2orderedproducts', 'topping2productinorders')


def downgrade() -> None:
    op.rename_table('productinorders', 'orderedproducts')
    op.rename_table('topping2productinorders', 'topping2orderedproducts')
