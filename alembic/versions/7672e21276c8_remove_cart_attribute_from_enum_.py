"""remove cart attribute from enum OrderStatuses

Revision ID: 7672e21276c8
Revises: 0f9dea33ccb5
Create Date: 2023-06-11 20:33:09.846856

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7672e21276c8'
down_revision = '0f9dea33ccb5'
branch_labels = None
depends_on = None


old_attributes = ('waiting', 'accepted', 'rejected', 'taken', 'no_taken', 'ready', 'cart')
new_attributes = ('waiting', 'accepted', 'rejected', 'taken', 'no_taken', 'ready')

old_type = sa.Enum(*old_attributes, name='orderstatuses')
new_type = sa.Enum(*new_attributes, name='orderstatuses')
tmp_type = sa.Enum(*new_attributes, name='_orderstatuses')

orders_table = sa.sql.table('orders',
                            sa.Column('status', new_type, nullable=False))


def upgrade():
    # Delete orders with 'cart' status
    op.execute(orders_table.delete().where(orders_table.c.status == u'cart'))

    # Create a temporary "_orderstatuses" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE orders ALTER COLUMN status TYPE _orderstatuses'
               ' USING status::text::_orderstatuses')
    old_type.drop(op.get_bind(), checkfirst=False)

    # Create and convert to the "new" status type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE orders ALTER COLUMN status TYPE orderstatuses'
               ' USING status::text::orderstatuses')
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade():
    # Create a temporary "_orderstatuses" type, convert and drop the "new" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE orders ALTER COLUMN status TYPE _orderstatuses'
               ' USING status::text::_orderstatuses')
    new_type.drop(op.get_bind(), checkfirst=False)

    # Create and convert to the "old" status type
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE orders ALTER COLUMN status TYPE orderstatuses'
               ' USING status::text::orderstatuses')
    tmp_type.drop(op.get_bind(), checkfirst=False)
