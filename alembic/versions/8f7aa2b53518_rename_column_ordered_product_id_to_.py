"""rename column ordered_product_id to product_in_order_id in Topping2ProductInOrder

Revision ID: 8f7aa2b53518
Revises: 40780c2f73cf
Create Date: 2023-06-10 03:22:52.246272

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8f7aa2b53518'
down_revision = '40780c2f73cf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('topping2productinorders', 'ordered_product_id', nullable=False,
                    new_column_name='product_in_order_id')
    op.drop_index('ix_orderedproducts_id', table_name='productinorders')
    op.create_index(op.f('ix_productinorders_id'), 'productinorders', ['id'], unique=True)
    op.alter_column('topping2productinorders', 'product_in_order_id',
                    existing_type=sa.INTEGER())
    op.drop_index('ix_topping2orderedproducts_id', table_name='topping2productinorders')
    op.create_index(op.f('ix_topping2productinorders_id'), 'topping2productinorders', ['id'], unique=True)


def downgrade() -> None:
    op.alter_column('topping2productinorders', 'product_in_order_id', nullable=False,
                    new_column_name='ordered_product_id')
    op.drop_index(op.f('ix_topping2productinorders_id'), table_name='topping2productinorders')
    op.create_index('ix_topping2orderedproducts_id', 'topping2productinorders', ['id'], unique=False)
    op.alter_column('topping2productinorders', 'product_in_order_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.drop_index(op.f('ix_productinorders_id'), table_name='productinorders')
    op.create_index('ix_orderedproducts_id', 'productinorders', ['id'], unique=False)
