"""changed timezones used

Revision ID: 3b00345cba21
Revises: 88ee6c984c16
Create Date: 2024-07-14 11:03:33.574503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b00345cba21'
down_revision = '88ee6c984c16'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('case_report', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('crime', schema=None) as batch_op:
        batch_op.alter_column('date_crime_received',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.alter_column('date_received',
               existing_type=sa.DATETIME(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.alter_column('date_received',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('crime', schema=None) as batch_op:
        batch_op.alter_column('date_crime_received',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('case_report', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    # ### end Alembic commands ###