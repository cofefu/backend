"""add nullable attribute to all columns

Revision ID: 34b5690d15cc
Revises: 7672e21276c8
Create Date: 2023-06-13 15:41:56.884114

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '34b5690d15cc'
down_revision = '7672e21276c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('coffeehousebranchs', 'placement',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('coffeehousebranchs', 'chat_id',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('coffeehousebranchs', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('customers', 'name',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('fsm', 'telegram_id',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('logincodes', 'customer_phone_number',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('logincodes', 'expire',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('menuupdatetimes', 'time',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('menuupdatetimes', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('orders', 'time',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
    op.alter_column('orders', 'creation_time',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('orders', 'status',
               existing_type=postgresql.ENUM('waiting', 'accepted', 'rejected', 'taken', 'no_taken', 'ready', name='orderstatuses'),
               nullable=False)
    op.alter_column('productincart', 'customer_phone_number',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('productincart', 'product_various_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('productinorders', 'order_id',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('productinorders', 'product_various_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('products', 'name',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('products', 'type_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('products', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('productvarious', 'price',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('productvarious', 'product_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('productvarious', 'size_name',
               existing_type=sa.VARCHAR(length=4),
               nullable=False)
    op.alter_column('topping2productincarts', 'product_in_cart_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('topping2productincarts', 'topping_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('topping2productinorders', 'topping_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('toppings', 'name',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.alter_column('toppings', 'price',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('toppings', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('worktime', 'coffee_house_branch_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('worktime', 'day_of_week',
               existing_type=postgresql.ENUM('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', name='daysofweek'),
               nullable=False)
    op.alter_column('worktime', 'open_time',
               existing_type=postgresql.TIME(),
               nullable=False)
    op.alter_column('worktime', 'close_time',
               existing_type=postgresql.TIME(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('worktime', 'close_time',
               existing_type=postgresql.TIME(),
               nullable=True)
    op.alter_column('worktime', 'open_time',
               existing_type=postgresql.TIME(),
               nullable=True)
    op.alter_column('worktime', 'day_of_week',
               existing_type=postgresql.ENUM('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', name='daysofweek'),
               nullable=True)
    op.alter_column('worktime', 'coffee_house_branch_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('toppings', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('toppings', 'price',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('toppings', 'name',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('topping2productinorders', 'topping_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('topping2productincarts', 'topping_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('topping2productincarts', 'product_in_cart_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('productvarious', 'size_name',
               existing_type=sa.VARCHAR(length=4),
               nullable=True)
    op.alter_column('productvarious', 'product_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('productvarious', 'price',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('products', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('products', 'type_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('products', 'name',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('productinorders', 'product_various_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('productinorders', 'order_id',
               existing_type=sa.BIGINT(),
               nullable=True)
    op.alter_column('productincart', 'product_various_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('productincart', 'customer_phone_number',
               existing_type=sa.BIGINT(),
               nullable=True)
    op.alter_column('orders', 'status',
               existing_type=postgresql.ENUM('waiting', 'accepted', 'rejected', 'taken', 'no_taken', 'ready', name='orderstatuses'),
               nullable=True)
    op.alter_column('orders', 'creation_time',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('orders', 'time',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)
    op.alter_column('menuupdatetimes', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('menuupdatetimes', 'time',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('logincodes', 'expire',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('logincodes', 'customer_phone_number',
               existing_type=sa.BIGINT(),
               nullable=True)
    op.alter_column('fsm', 'telegram_id',
               existing_type=sa.BIGINT(),
               nullable=True)
    op.alter_column('customers', 'name',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('coffeehousebranchs', 'coffee_house_name',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('coffeehousebranchs', 'chat_id',
               existing_type=sa.BIGINT(),
               nullable=True)
    op.alter_column('coffeehousebranchs', 'placement',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    # ### end Alembic commands ###