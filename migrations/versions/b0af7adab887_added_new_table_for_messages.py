"""added new table for messages

Revision ID: b0af7adab887
Revises: c8333ff4f486
Create Date: 2024-06-28 12:24:13.502314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0af7adab887'
down_revision = 'c8333ff4f486'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.drop_constraint('uq_message_email_address', type_='unique')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_message_email_address', ['email_address'])

    # ### end Alembic commands ###
